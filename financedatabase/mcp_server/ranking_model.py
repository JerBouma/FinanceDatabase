"""Ranking Model

Orders query results so the instrument a person most likely means comes first. Every
rule is general and every preference is measured on the data itself: how a query
matches (the name, the symbol, whole words or part of a word), whether a listing is
the primary listing of its instrument (see listings_model), market cap, and how common
an exchange or currency is within the asset class.
"""

__docformat__ = "google"

import re
from dataclasses import dataclass, field

import polars as pl

from financedatabase.listings_model import get_name_key, get_trailing_words

MARKET_CAP_ORDER = [
    "Mega Cap",
    "Large Cap",
    "Mid Cap",
    "Small Cap",
    "Micro Cap",
    "Nano Cap",
]
# A symbol separator used by fewer than this share of an asset class's symbols marks
# a variant of an instrument (AEXGR.AS or ^XVZ-IV among indices, but not the dash
# that every cryptocurrency pair has).
VARIANT_SEPARATOR_SHARE = 0.5
SEPARATORS = [".", "-", "="]
CURRENCY_COLUMNS = ["currency", "base_currency", "quote_currency"]
# Categories of the database that hold leveraged, inverse and other trading products.
DERIVATIVE_CATEGORIES = ["Derivatives", "Trading"]
PREFERENCE_COLUMNS = [
    "_secondary",
    "_derivative",
    "_not_primary",
    "_cap",
    "_listings",
    "_name_length",
    "_listing",
    "_unusual_currency",
    "_currency",
]


@dataclass
class RankingProfile:
    """
    What the ranking measures on an asset class once.

    Attributes:
        trailing_words (list[str]): Words that end many names, see listings_model.
        currency_order (dict[str, int]): Currencies by how often they occur in the
            currency columns, the most common 0.
        variant_separators (list[str]): Symbol separators that mark a variant.
        name_keys (pl.DataFrame | None): The symbol column, "_key" (the name without
            its common trailing words) and "_words" (the name as spaced lowercase
            words), to join to queried rows.
    """

    trailing_words: list[str] = field(default_factory=list)
    currency_order: dict[str, int] = field(default_factory=dict)
    variant_separators: list[str] = field(default_factory=list)
    name_keys: pl.DataFrame | None = None


def get_frequency_order(values: pl.Series) -> dict[str, int]:
    """
    Order values by how often they occur.

    Args:
        values (pl.Series): The values.

    Returns:
        dict[str, int]: Value -> position, the most frequent 0.
    """
    counts = values.drop_nulls().value_counts(sort=True)
    return {value: i for i, value in enumerate(counts.get_column(values.name))}


def create_profile(lazy: pl.LazyFrame, ranks: pl.DataFrame | None) -> RankingProfile:
    """
    Measure an asset class for the ranking.

    Args:
        lazy (pl.LazyFrame): The dataset, the symbol column first.
        ranks (pl.DataFrame | None): The listing ranks, see listings_model.

    Returns:
        RankingProfile: The measurements.
    """
    columns = lazy.collect_schema().names()
    currencies = [c for c in CURRENCY_COLUMNS if c in columns]
    wanted = [c for c in (columns[0], "name") if c in columns]
    frame = lazy.select(*wanted, *currencies).collect()
    symbols = frame.get_column(columns[0]).drop_nulls()

    profile = RankingProfile()
    if "name" in columns:
        profile.trailing_words = get_trailing_words(frame.get_column("name"))
        profile.name_keys = frame.select(
            columns[0],
            get_name_key(pl.col("name"), profile.trailing_words)
            .fill_null(pl.col(columns[0]))
            .alias("_key"),
            (
                pl.lit(" ")
                + pl.col("name").str.to_lowercase().str.replace_all(r"[^a-z0-9]+", " ")
                + pl.lit(" ")
            ).alias("_words"),
        ).unique(columns[0])
    if currencies:
        profile.currency_order = get_frequency_order(
            pl.concat([frame.get_column(c) for c in currencies]).alias("currency")
        )
    if ranks is None and len(symbols):
        profile.variant_separators = [
            separator
            for separator in SEPARATORS
            if symbols.str.contains(separator, literal=True).mean()
            < VARIANT_SEPARATOR_SHARE
        ]
    return profile


def build_query_expressions(
    columns: list[str],
    query: str,
    profile: RankingProfile,
    identifier_columns: list[str],
) -> tuple[pl.Expr, pl.Expr]:
    """
    Build the match filter and relevance tier for a free-text query. The tier needs
    the "_key" and "_words" columns of the profile's name keys where the asset class
    has names.

    Matching is a case-insensitive literal substring on symbol and name (no regex,
    so 'S&P 500' or 'BRK.B' need no escaping), also with punctuation ignored
    ('Anheuser-Busch' finds 'Anheuser Busch'), plus an exact match on identifier
    columns such as ISIN. A leading ^ of an index symbol is optional ('AEX' finds
    ^AEX).

    The tiers, best first:
    0. An identifier, the name without its common trailing words ('Bitcoin USD' for
       'bitcoin', 'AEX-INDEX' for 'AEX'), or a name starting with the query as whole
       words with a symbol that starts with it too ('ING Groep N.V.', INGA.AS).
    1. The symbol, also without what follows its first separator or a leading caret
       ('ASML.AS', '^AEX', 'BTC-USD').
    2. A name starting with the query as whole words.
    3. A name containing the query as whole words ('SPDR S&P 500 ETF Trust').
    4. A symbol starting with the query.
    5. A name starting with the query.
    6. A word in the name starting with the query.
    7. Any other match.

    Args:
        columns (list[str]): The columns of the dataset, the symbol column first.
        query (str): The free-text query.
        profile (RankingProfile): The measurements of the asset class.
        identifier_columns (list[str]): Columns matched exactly, such as ISIN.

    Returns:
        tuple[pl.Expr, pl.Expr]: The boolean filter and an integer tier (0 = best).
    """
    needle = query.strip().lower()
    bare = needle.lstrip("^") or needle
    symbol = pl.col(columns[0]).str.to_lowercase()
    bare_symbol = symbol.str.strip_chars_start("^")
    base = bare_symbol.str.replace(r"[.\-=].*$", "")

    identifier = pl.lit(False)
    for column in identifier_columns:
        if column in columns:
            identifier = identifier | (pl.col(column).str.to_lowercase() == needle)
    identifier = identifier.fill_null(False)

    match = (
        symbol.str.contains(needle, literal=True)
        | bare_symbol.str.contains(bare, literal=True)
    ).fill_null(False) | identifier
    exact = ((symbol == needle) | (bare_symbol == bare) | (base == bare)).fill_null(
        False
    )
    if "name" not in columns:
        tier = pl.when(identifier).then(0).when(exact).then(1)
        tier = tier.when(bare_symbol.str.starts_with(bare)).then(4)
        return match, tier.otherwise(7).cast(pl.Int8)

    name = pl.col("name").str.to_lowercase()
    key = pl.col("_key")
    needle_key = (
        pl.select(get_name_key(pl.lit(query), profile.trailing_words)).item() or needle
    )
    words = pl.col("_words")
    spaced = " " + " ".join(re.sub(r"[^a-z0-9]+", " ", needle).split()) + " "

    match = match | name.str.contains(needle, literal=True).fill_null(False)
    if spaced.strip():
        match = match | words.str.contains(spaced.strip(), literal=True).fill_null(
            False
        )
    named = (key == needle_key) | (
        words.str.starts_with(spaced) & bare_symbol.str.starts_with(bare)
    )
    tier = pl.when(identifier | named.fill_null(False)).then(0)
    tier = tier.when(exact).then(1)
    tier = tier.when(words.str.starts_with(spaced)).then(2)
    tier = tier.when(words.str.contains(spaced, literal=True)).then(3)
    tier = tier.when(bare_symbol.str.starts_with(bare)).then(4)
    tier = tier.when(name.str.starts_with(needle)).then(5)
    tier = tier.when(words.str.contains(spaced.rstrip(), literal=True)).then(6)
    return match, tier.otherwise(7).cast(pl.Int8)


def build_preference_columns(
    columns: list[str], profile: RankingProfile, has_ranks: bool
) -> list[pl.Expr]:
    """
    Build the columns that order equally relevant matches:

    - main lines before secondary ones: a listing that is not primary, a variant
      symbol of an asset class without listings, or a product in a derivatives
      category;
    - primary listings first;
    - larger market caps (a product without one ranks with mid caps);
    - instruments with more listings worldwide, a measure of prominence (Siemens AG
      before Siemens Limited);
    - shorter names, so Apple Inc. is listed before Apple Hospitality;
    - stronger listings of the same instrument: the home market first, then larger
      main venues, and listings in the usual currency of their market (RIO.L in
      pounds before 0KWZ.L in dollars);
    - more common currencies, so Bitcoin USD is listed before Bitcoin EUR.

    Args:
        columns (list[str]): The columns of the dataset, the symbol column first.
        profile (RankingProfile): The measurements of the asset class.
        has_ranks (bool): Whether the listing ranks are joined to the dataset.

    Returns:
        list[pl.Expr]: The preference columns, named as in PREFERENCE_COLUMNS.
    """
    symbol = pl.col(columns[0])
    if has_ranks:
        not_primary = ~pl.col("primary_listing").fill_null(False)
        secondary = not_primary
        listing = -pl.col("listing_score").fill_null(0.0)
        listings = -pl.col("listings").fill_null(1)
        usual_currency = pl.col("usual_currency").fill_null(False)
    else:
        variant = pl.lit(False)
        for separator in profile.variant_separators:
            variant = variant | symbol.str.contains(separator, literal=True)
        not_primary = secondary = variant.fill_null(False)
        listing = pl.lit(0.0)
        listings = pl.lit(-1)
        usual_currency = pl.lit(True)

    derivative = pl.lit(False)
    for column in ("category_group", "category"):
        if column in columns:
            derivative = derivative | pl.col(column).is_in(DERIVATIVE_CATEGORIES)
    derivative = derivative.fill_null(False)

    if "market_cap" in columns:
        cap = (
            pl.col("market_cap")
            .replace_strict(
                {tier: i for i, tier in enumerate(MARKET_CAP_ORDER)},
                default=len(MARKET_CAP_ORDER),
                return_dtype=pl.Int8,
            )
            .fill_null(len(MARKET_CAP_ORDER))
        )
    else:
        cap = pl.lit(MARKET_CAP_ORDER.index("Mid Cap"), dtype=pl.Int8)

    def order(column: str, positions: dict[str, int]) -> pl.Expr:
        if column not in columns or not positions:
            return pl.lit(0, dtype=pl.Int32)
        return (
            pl.col(column)
            .replace_strict(positions, default=len(positions), return_dtype=pl.Int32)
            .fill_null(len(positions))
        )

    currency = "quote_currency" if "quote_currency" in columns else "currency"
    name = pl.col("name") if "name" in columns else pl.lit(None, dtype=pl.String)
    return [
        (secondary | derivative).alias("_secondary"),
        derivative.alias("_derivative"),
        not_primary.alias("_not_primary"),
        cap.alias("_cap"),
        listings.alias("_listings"),
        name.str.len_chars().fill_null(10_000).alias("_name_length"),
        listing.alias("_listing"),
        (~usual_currency).alias("_unusual_currency"),
        order(currency, profile.currency_order).alias("_currency"),
    ]


def mark_duplicates(lazy: pl.LazyFrame, sort_columns: list[str]) -> pl.LazyFrame:
    """
    Mark every row after the first of its name key ("_key") as secondary, for asset
    classes without listings: 'Bitcoin EUR' after 'Bitcoin USD'.

    Args:
        lazy (pl.LazyFrame): The rows with the preference columns.
        sort_columns (list[str]): The order that decides which row is first.

    Returns:
        pl.LazyFrame: The rows, sorted, with "_secondary" updated.
    """
    return lazy.sort(sort_columns).with_columns(
        (pl.col("_secondary") | (pl.int_range(pl.len()).over("_key") > 0)).alias(
            "_secondary"
        )
    )


def get_bucket(tier: pl.Expr) -> pl.Expr:
    """
    Get the result bucket of a match: the main lines matching the name, the symbol,
    or the query as whole words, then their secondary lines, then the weaker matches.

    Args:
        tier (pl.Expr): The match tier, see build_query_expressions.

    Returns:
        pl.Expr: The bucket, 0 first.
    """
    strong = pl.min_horizontal(tier, pl.lit(2, dtype=pl.Int8))
    return (
        pl.when(tier <= 3)
        .then(strong + 3 * pl.col("_secondary").cast(pl.Int8))
        .otherwise(tier + 2)
        .cast(pl.Int8)
    )


def interleave_classes(frames: list[pl.DataFrame]) -> pl.DataFrame:
    """
    Merge the ranked matches of several asset classes. Within a bucket the classes
    take turns, so a search for 'bitcoin' shows the coin, ETFs and companies. The
    class whose first match is the closest goes first: by tier, plain products before
    derivatives, a large company before a product and a small one after it, and the
    shortest name.

    Args:
        frames (list[pl.DataFrame]): Per asset class its matches in order, with the
            columns "_bucket", "_tier", "_derivative", "_cap" and "_name_length".

    Returns:
        pl.DataFrame: The merged matches without the ranking columns.
    """
    merged = pl.concat(
        [
            frame.with_columns(
                pl.int_range(pl.len()).over("_bucket").alias("_turn"),
                pl.lit(position).alias("_class"),
            )
            for position, frame in enumerate(frames)
        ]
    )
    order = (
        merged.filter(pl.col("_turn") == 0)
        .sort(["_bucket", "_tier", "_derivative", "_cap", "_name_length", "_class"])
        .select(
            "_bucket", "_class", pl.int_range(pl.len()).over("_bucket").alias("_order")
        )
    )
    return (
        merged.join(order, on=["_bucket", "_class"], how="left")
        .sort(["_bucket", "_turn", "_order"])
        .drop(
            "_bucket",
            "_tier",
            "_derivative",
            "_cap",
            "_name_length",
            "_turn",
            "_class",
            "_order",
        )
    )
