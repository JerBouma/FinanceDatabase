"""Ranking Model"""

__docformat__ = "google"

import re
from dataclasses import dataclass, field

import polars as pl

from financedatabase.listings_model import get_name_key, get_trailing_words, get_words

MARKET_CAP_ORDER = [
    "Mega Cap",
    "Large Cap",
    "Mid Cap",
    "Small Cap",
    "Micro Cap",
    "Nano Cap",
]
# Maximum share of symbols with a separator for it to mark a variant (AEXGR.AS).
VARIANT_SEPARATOR_SHARE = 0.5
SEPARATORS = [".", "-", "="]
CURRENCY_COLUMNS = ["currency", "base_currency", "quote_currency"]
# Minimum query length to also match names without spaces ('USDJPY' for 'USD/JPY').
COMPACT_MINIMUM = 5
# Categories of the database that hold leveraged, inverse and other trading products.
DERIVATIVE_CATEGORIES = ["Derivatives", "Trading"]
PREFERENCE_COLUMNS = [
    "_secondary",
    "_derivative",
    "_not_primary",
    "_cap",
    "_listings",
    "_listing",
    "_missing",
    "_name_length",
    "_unusual_currency",
    "_currency",
    "_symbol_length",
]


@dataclass
class RankingProfile:
    """
    What the ranking measures on an asset class once.

    Attributes:
        trailing_words (list[str]): Words that end many names, see listings_model.
        currency_order (dict[str, int]): Currencies by frequency, the most common 0.
        variant_separators (list[str]): Symbol separators that mark a variant.
        venue_sizes (dict[str, int]): Exchanges by their number of listings.
        name_keys (pl.DataFrame | None): The search frame with "_key", "_words", "_compact".
    """

    trailing_words: list[str] = field(default_factory=list)
    currency_order: dict[str, int] = field(default_factory=dict)
    variant_separators: list[str] = field(default_factory=list)
    venue_sizes: dict[str, int] = field(default_factory=dict)
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


def create_profile(
    lazy: pl.LazyFrame,
    ranks: pl.DataFrame | None,
    identifier_columns: list[str] | None = None,
) -> RankingProfile:
    """
    Measure an asset class for the ranking.

    Args:
        lazy (pl.LazyFrame): The dataset, the symbol column first.
        ranks (pl.DataFrame | None): The listing ranks, see listings_model.
        identifier_columns (list[str] | None): Columns a query matches exactly.

    Returns:
        RankingProfile: The measurements.
    """
    columns = lazy.collect_schema().names()
    currencies = [c for c in CURRENCY_COLUMNS if c in columns]
    identifiers = [c for c in identifier_columns or [] if c in columns]
    wanted = [c for c in (columns[0], "name", "exchange") if c in columns]
    frame = lazy.select(*wanted, *currencies, *identifiers).collect()
    symbols = frame.get_column(columns[0]).drop_nulls()

    profile = RankingProfile()
    if "name" in columns:
        profile.trailing_words = get_trailing_words(frame.get_column("name"))
        profile.name_keys = frame.select(
            columns[0],
            "name",
            *identifiers,
            get_name_key(pl.col("name"), profile.trailing_words)
            .fill_null(pl.col(columns[0]))
            .alias("_key"),
            (pl.lit(" ") + get_words(pl.col("name")) + pl.lit(" ")).alias("_words"),
            get_words(pl.col("name")).str.replace_all(" ", "").alias("_compact"),
        ).unique(columns[0])
    if "exchange" in columns:
        counts = frame.get_column("exchange").drop_nulls().value_counts()
        profile.venue_sizes = dict(
            zip(counts["exchange"], counts["count"], strict=True)
        )
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
    Build the match filter and relevance tier (0 = exact, 7 = any match) for a query.

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
    # 'brk.b' and 'BRK/B' find BRK-B: separators in symbols are ignored.
    compact_symbol = symbol.str.replace_all(r"[^a-z0-9]+", "")
    compact_query = re.sub(r"[^a-z0-9]+", "", needle)
    full = (
        (symbol == needle)
        | (bare_symbol == bare)
        | ((compact_symbol == compact_query) & pl.lit(len(compact_query) > 1))
    ).fill_null(False)
    match = match | full
    exact = (full | (base == bare)).fill_null(False)
    if "name" not in columns:
        tier = pl.when(identifier | full).then(0).when(exact).then(1)
        tier = tier.when(bare_symbol.str.starts_with(bare)).then(4)
        return match, tier.otherwise(7).cast(pl.Int8)

    name = pl.col("name").str.to_lowercase()
    key = pl.col("_key")
    needle_key = (
        pl.select(get_name_key(pl.lit(query), profile.trailing_words)).item() or needle
    )
    words = pl.col("_words")
    # The query is read like the names: without accents and punctuation ('Hermès').
    normalized = pl.select(get_words(pl.lit(query))).item() or ""
    spaced = " " + normalized + " "

    compact = normalized.replace(" ", "")
    match = match | name.str.contains(needle, literal=True).fill_null(False)
    if len(compact) >= COMPACT_MINIMUM:
        # Spaces may be left out ('loreal'), but the match starts and ends on a word.
        spaced_out = r"\b" + " ?".join(compact) + r"\b"
        match = match | words.str.contains(spaced_out).fill_null(False)
    if spaced.strip():
        match = match | words.str.contains(spaced.strip(), literal=True).fill_null(
            False
        )
    named = (key == needle_key) | (
        words.str.starts_with(spaced) & bare_symbol.str.starts_with(bare)
    )
    if len(compact) >= COMPACT_MINIMUM:
        named = named | (pl.col("_compact") == compact)
        named = named | (key.str.replace_all(" ", "", literal=True) == compact)
    tier = pl.when(identifier | full).then(0)
    tier = tier.when(exact | named.fill_null(False)).then(1)
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
    Build the columns that order equally relevant matches, most important first.

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
        # A listing without a country lacks issuer data and is often not the instrument.
        secondary = not_primary | ~pl.col("home_known").fill_null(True)
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
        secondary.alias("_secondary"),
        derivative.alias("_derivative"),
        not_primary.alias("_not_primary"),
        cap.alias("_cap"),
        listings.alias("_listings"),
        pl.sum_horizontal(
            [pl.col(c).is_null().cast(pl.Int8) for c in columns[1:]]
        ).alias("_missing"),
        name.str.len_chars().fill_null(10_000).alias("_name_length"),
        listing.alias("_listing"),
        (~usual_currency).alias("_unusual_currency"),
        order(currency, profile.currency_order).alias("_currency"),
        symbol.str.len_chars().fill_null(0).alias("_symbol_length"),
    ]


def mark_duplicates(lazy: pl.LazyFrame, sort_columns: list[str]) -> pl.LazyFrame:
    """
    Mark every row after the first of its name key as secondary ('Bitcoin EUR').

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
    Get the result bucket of a match: strong main lines, their secondary lines, the rest.

    Args:
        tier (pl.Expr): The match tier, see build_query_expressions.

    Returns:
        pl.Expr: The bucket, 0 first.
    """
    strong = pl.min_horizontal(tier, pl.lit(2, dtype=pl.Int8))
    # A derivative product is a secondary line unless its symbol or name is the query.
    secondary = pl.col("_secondary") | (pl.col("_derivative") & (tier >= 2))
    return (
        pl.when(tier <= 3)
        .then(strong + 3 * secondary.cast(pl.Int8))
        .otherwise(tier + 2)
        .cast(pl.Int8)
    )


def keep_top_company_together(
    lazy: pl.LazyFrame, venue_sizes: dict[str, int]
) -> pl.LazyFrame:
    """
    Move the best match's listing on its largest other exchange right after it.

    Args:
        lazy (pl.LazyFrame): The matches in order, with "_key", "_bucket", "exchange"
            and "main_venue".
        venue_sizes (dict[str, int]): Exchanges by their number of listings.

    Returns:
        pl.LazyFrame: The matches with "_top" and "_not_top" columns.
    """
    size = (
        pl.col("exchange")
        .replace_strict(venue_sizes, default=0, return_dtype=pl.Int64)
        .fill_null(0)
    )
    company = (pl.col("_key") == pl.col("_key").first()).fill_null(False) & pl.col(
        "main_venue"
    ).fill_null(False)
    largest = pl.when(company).then(size).max()
    first_row = pl.int_range(pl.len()) == 0
    top = first_row | (
        company
        & (size == largest)
        & (pl.col("exchange") != pl.col("exchange").first())
        & (
            pl.int_range(pl.len())
            == pl.when(company & (size == largest)).then(pl.int_range(pl.len())).min()
        )
    )
    return lazy.with_columns(top.alias("_top")).with_columns(
        pl.when("_top")
        .then(pl.col("_bucket").first())
        .otherwise(pl.col("_bucket"))
        .alias("_bucket"),
        (~pl.col("_top")).alias("_not_top"),
    )


def interleave_classes(frames: list[pl.DataFrame]) -> pl.DataFrame:
    """
    Merge the ranked matches of several asset classes, taking turns within a bucket.

    Args:
        frames (list[pl.DataFrame]): Per asset class its matches in order, with the
            ranking columns.

    Returns:
        pl.DataFrame: The merged matches without the ranking columns.
    """
    merged = pl.concat(
        [
            frame.with_columns(
                pl.int_range(pl.len()).over("_bucket").alias("_turn"),
                pl.int_range(pl.len()).alias("_row"),
                pl.lit(position).alias("_class"),
            )
            for position, frame in enumerate(frames)
        ]
    )
    order = (
        merged.filter(pl.col("_turn") == 0)
        .sort(
            [
                "_bucket",
                "_derivative",
                "_cap",
                "_tier",
                "_listings",
                "_name_length",
                "_class",
            ]
        )
        .select(
            "_bucket", "_class", pl.int_range(pl.len()).over("_bucket").alias("_order")
        )
    )
    merged = merged.join(order, on=["_bucket", "_class"], how="left")
    # The leading class's best company lines stay together before the others take turns.
    leader = merged.sort(["_bucket", "_order"]).get_column("_class").first()
    block = (pl.col("_class") == leader) & pl.col("_top")
    merged = merged.with_columns(
        pl.when(block)
        .then(-1)
        .otherwise((~block).cast(pl.Int32).cum_sum().over("_class", "_bucket") - 1)
        .alias("_turn")
    )
    return merged.sort(["_bucket", "_turn", "_order", "_row"]).drop(
        "_bucket",
        "_tier",
        "_derivative",
        "_cap",
        "_listings",
        "_name_length",
        "_top",
        "_turn",
        "_row",
        "_class",
        "_order",
    )
