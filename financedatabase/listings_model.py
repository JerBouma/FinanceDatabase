"""Listings Model

Finds the primary listing of instruments that trade on several exchanges, from the data
alone: no list of exchanges, countries or naming conventions is kept.

- Main venues: an exchange is a main venue when it leads the country most of its
  companies come from, that is when no exchange has a much larger share of that
  country's companies. Euronext Amsterdam, Xetra and the NYSE are main venues; the
  German regional exchanges and OTC Markets, where most companies are foreign, are not.
- Home listings: a company's listing is at home when its country makes up a fair share
  of the exchange's companies, and stronger the larger that share: ASML.AS on Euronext
  Amsterdam, not ASML on NASDAQ or ASMLF over the counter.
- The primary listing of an instrument is its strongest home listing on a main venue,
  or without one its listing on the largest main venue, or without one its strongest
  home listing elsewhere. A listing abroad off the main venues is never primary.

Listings of one instrument are linked by ISIN and by name within a home. Names are
compared without accents, punctuation and the trailing words that end many names of
the asset class, such as legal forms ('Inc.', 'N.V.', 'AG'). A lone listing joins the
most listed name of its home with the same distinctive first word ('ASML CDR (CAD
Hedged)' joins 'ASML Holding'), and a listing without a home joins the name it starts
with ('Toyota Motor ADR' joins 'Toyota Motor').
"""

__docformat__ = "google"

import polars as pl

# A venue leads a home when its share of that home is at least this fraction of the
# largest share any venue has of it (the NYSE and NASDAQ both lead the United States).
LEADING_FRACTION = 0.8
# Shares are measured as if every exchange had this many more listings, so a venue
# with a handful of listings cannot lead a country with a share of 100%.
PRIOR_LISTINGS = 20
# A home makes up at least this share of an exchange's listings for the exchange to
# be a home market of it (Frankfurt is one for German companies at 6%).
HOME_SHARE = 0.05
# Listings scoring within this fraction of the best one are primary as well (the
# National Stock Exchange and BSE for an Indian company).
PRIMARY_TOLERANCE = 0.9
# A word that ends at least this share of the names of an asset class is ignored at
# the end of names ('Inc', 'Limited', 'AG', 'Index', 'USD').
TRAILING_WORD_SHARE = 0.003
MAXIMUM_TRAILING_WORDS = 4
# A first word shared by at most this many names of a home links a lone listing to
# the most listed of them.
DISTINCTIVE_WORD_NAMES = 5
NON_WORD = r"[^a-z0-9]+"


def get_words(name: pl.Expr) -> pl.Expr:
    """
    Get a name in lowercase words separated by single spaces.

    Args:
        name (pl.Expr): The name column.

    Returns:
        pl.Expr: The words.
    """
    return (
        name.str.normalize("NFKD")
        .str.to_lowercase()
        .str.replace_all(NON_WORD, " ")
        .str.strip_chars()
    )


def get_trailing_words(names: pl.Series) -> list[str]:
    """
    Get the words that end many names, such as legal forms in equities.

    Args:
        names (pl.Series): The names of an asset class.

    Returns:
        list[str]: The words that end at least TRAILING_WORD_SHARE of the names.
    """
    names = names.drop_nulls()
    if names.is_empty():
        return []
    last = (
        pl.select(get_words(pl.lit(names)).str.extract(r"(\S+)$").alias("word"))
        .to_series()
        .drop_nulls()
    )
    minimum = TRAILING_WORD_SHARE * len(names)
    counts = last.value_counts()
    return counts.filter(pl.col("count") >= minimum).get_column("word").to_list()


def get_name_key(name: pl.Expr, trailing_words: list[str]) -> pl.Expr:
    """
    Get a name without punctuation and without the trailing words of its asset class,
    to link listings named 'ASML Holding N.V.' and 'ASML HOLDING NV'.

    Args:
        name (pl.Expr): The name column.
        trailing_words (list[str]): The words to remove from the end of names.

    Returns:
        pl.Expr: The normalised name, null when nothing is left.
    """
    key = get_words(name)
    if trailing_words:
        pattern = r"\s(?:" + "|".join(sorted(trailing_words, key=len)[::-1]) + r")$"
        for _ in range(MAXIMUM_TRAILING_WORDS):
            key = key.str.replace(pattern, "")
    return pl.when(key.str.len_chars() > 0).then(key)


def get_home(columns: list[str]) -> pl.Expr:
    """
    Get the home of each instrument: its country, else the country code of its ISIN.
    Only an asset class with neither takes its currency.

    Args:
        columns (list[str]): The columns of the dataset.

    Returns:
        pl.Expr: The home, null when none of these is known.
    """
    candidates = []
    if "country" in columns:
        candidates.append(pl.col("country"))
    if "isin" in columns:
        isin = pl.col("isin")
        candidates.append(
            pl.when(isin.str.len_chars() == 12).then(isin.str.slice(0, 2))
        )
    if not candidates and "currency" in columns:
        candidates.append(pl.col("currency"))
    if not candidates:
        return pl.lit(None, dtype=pl.String)
    return pl.coalesce(candidates)


def get_main_venues(lazy: pl.LazyFrame) -> list[str]:
    """
    Get the main venues: the exchanges that lead the home most of their listings come
    from.

    Args:
        lazy (pl.LazyFrame): Listings with an "exchange" column and a country, ISIN or
            currency to take the home from.

    Returns:
        list[str]: The exchanges.
    """
    lazy = lazy.select(
        "exchange", get_home(lazy.collect_schema().names()).alias("country")
    )
    shares = (
        lazy.filter(pl.col("exchange").is_not_null() & pl.col("country").is_not_null())
        .group_by("exchange", "country")
        .len()
        .with_columns(
            (
                pl.col("len") / (pl.col("len").sum().over("exchange") + PRIOR_LISTINGS)
            ).alias("share")
        )
        .collect()
    )
    leading = shares.filter(
        pl.col("share") >= LEADING_FRACTION * pl.col("share").max().over("country")
    )
    largest = shares.filter(pl.col("share") == pl.col("share").max().over("exchange"))
    return sorted(
        leading.join(largest, on=["exchange", "country"], how="semi")
        .get_column("exchange")
        .unique()
        .to_list()
    )


def get_prefixes(keys: pl.DataFrame) -> pl.DataFrame:
    """
    Get every word-for-word start of each name: 'asml', 'asml holding' for 'asml
    holding'.

    Args:
        keys (pl.DataFrame): The column "_name".

    Returns:
        pl.DataFrame: The columns "_name", "_prefix" and "_size", its number of words.
    """
    return (
        keys.select("_name")
        .unique()
        .with_columns(pl.col("_name").str.split(" ").alias("_words"))
        .with_columns(pl.int_ranges(1, pl.col("_words").list.len() + 1).alias("_size"))
        .explode("_size")
        .with_columns(
            pl.col("_words").list.head(pl.col("_size")).list.join(" ").alias("_prefix")
        )
        .drop("_words")
    )


def link_names(frame: pl.DataFrame) -> pl.Series:
    """
    Get the name that links the listings of one instrument.

    An instrument without a listing on a main venue at home, such as a depositary
    receipt, joins the
    name of its home that its own name starts with ('Samsung Electronics Sponsored
    GDR' joins 'Samsung Electronics'), or else the most listed name of its home with
    the same first word, when few names start with that word ('ASML CDR (CAD
    Hedged)' joins 'ASML Holding'). A listing without a home joins the shortest name
    of any home that its name starts with ('Toyota Motor ADR' joins 'Toyota Motor').
    Instruments with a listing on a main venue at home are never joined, so Siemens
    Energy stays apart from Siemens.

    Args:
        frame (pl.DataFrame): The columns "_name", "_home", "_at_home" and
            "main_venue".

    Returns:
        pl.Series: The linking name of every row.
    """
    keys = frame.group_by("_name", "_home").agg(
        pl.len(), (~(pl.col("_at_home") & pl.col("main_venue"))).all().alias("_orphan")
    )
    targets = keys.filter(pl.col("_home").is_not_null() & ~pl.col("_orphan"))

    by_prefix = (
        get_prefixes(keys)
        .join(keys.select("_name", "_home"), on="_name")
        .join(
            targets.select(pl.col("_name").alias("_prefix"), "_home"),
            on=["_prefix", "_home"],
            how="semi",
            nulls_equal=True,
        )
        .filter(pl.col("_prefix") != pl.col("_name"))
        .group_by("_name", "_home")
        .agg(pl.col("_prefix").sort_by("_size").first().alias("_by_prefix"))
    )
    first = pl.col("_name").str.extract(r"^(\S+)")
    by_word = (
        keys.filter(pl.col("_home").is_not_null())
        .with_columns(first.alias("_first"))
        .filter(pl.len().over("_first", "_home") <= DISTINCTIVE_WORD_NAMES)
        .join(
            targets.with_columns(first.alias("_first"))
            .sort("len", descending=True)
            .unique(["_first", "_home"], keep="first")
            .select("_first", "_home", pl.col("_name").alias("_by_word")),
            on=["_first", "_home"],
        )
        .select("_name", "_home", "_by_word")
    )
    homeless = (
        get_prefixes(keys.filter(pl.col("_home").is_null()))
        .join(targets.select(pl.col("_name").alias("_prefix")).unique(), on="_prefix")
        .group_by("_name")
        .agg(pl.col("_prefix").sort_by("_size").first().alias("_by_name"))
        .with_columns(pl.lit(None, dtype=pl.String).alias("_home"))
    )

    links = (
        keys.join(by_prefix, on=["_name", "_home"], how="left", nulls_equal=True)
        .join(by_word, on=["_name", "_home"], how="left", nulls_equal=True)
        .join(homeless, on=["_name", "_home"], how="left", nulls_equal=True)
        .with_columns(
            pl.when(pl.col("_home").is_null())
            .then(pl.col("_by_name"))
            .when(pl.col("_orphan"))
            .then(pl.coalesce("_by_prefix", "_by_word"))
            .fill_null(pl.col("_name"))
            .alias("_link")
        )
        .select("_name", "_home", "_link")
    )
    return frame.join(
        links, on=["_name", "_home"], how="left", nulls_equal=True
    ).get_column("_link")


def get_listing_ranks(lazy: pl.LazyFrame, main_venues: list[str]) -> pl.DataFrame:
    """
    Score every listing and mark the primary ones.

    Listings score by level: a home listing on a main venue scores two plus its
    country's share of the exchange's listings, a listing on a main venue abroad one
    plus the venue's share of all listings on main venues, a home listing on another
    venue its country's share (a German company only traded in Frankfurt, a US company
    only traded over the counter) and any other listing nothing. The primary listings
    of an instrument are its best scoring ones; a listing abroad off the main venues is
    never primary. Delisted entries never hide a listed one.

    Args:
        lazy (pl.LazyFrame): The dataset, the symbol column first, with an exchange
            column.
        main_venues (list[str]): The main venues, see get_main_venues.

    Returns:
        pl.DataFrame: The symbol column, "listing_score" (higher is stronger),
            "primary_listing", "main_venue", "listings" (the number of listings of
            the instrument), "usual_currency" (whether it trades in the most common
            currency of its home's listings on that exchange) and "home_known"
            (whether the instrument's country is known, always for an asset class
            without countries).
    """
    columns = lazy.collect_schema().names()
    symbol = columns[0]
    name = pl.col("name") if "name" in columns else pl.lit(None, dtype=pl.String)
    isin = pl.col("isin") if "isin" in columns else pl.lit(None, dtype=pl.String)
    country = (
        pl.col("country") if "country" in columns else pl.lit(None, dtype=pl.String)
    )
    delisted = (
        pl.col("delisted").fill_null(False) if "delisted" in columns else pl.lit(False)
    )
    currency = (
        pl.col("currency") if "currency" in columns else pl.lit(None, dtype=pl.String)
    )

    frame = lazy.select(
        pl.col(symbol),
        pl.col("exchange").alias("_exchange"),
        currency.alias("_currency"),
        country.alias("_home"),
        name.alias("_full_name"),
        pl.when(isin.str.len_chars() == 12).then(isin).alias("_isin"),
        delisted.alias("_delisted"),
    ).collect()

    trailing_words = get_trailing_words(frame.get_column("_full_name"))
    frame = frame.with_columns(
        get_name_key(pl.col("_full_name"), trailing_words)
        .fill_null(pl.col(symbol))
        .alias("_name")
    )
    listed = frame.filter(~pl.col("_delisted"))
    shares = (
        listed.filter(pl.col("_home").is_not_null())
        .group_by("_exchange", "_home")
        .len()
        .with_columns(
            (pl.col("len") / pl.col("len").sum().over("_exchange")).alias("_share")
        )
        .drop("len")
    )
    sizes = (
        listed.filter(pl.col("_exchange").is_in(main_venues))
        .group_by("_exchange")
        .len()
        .with_columns((pl.col("len") / pl.col("len").sum()).alias("_size"))
        .drop("len")
    )

    frame = (
        frame.join(shares, on=["_exchange", "_home"], how="left", nulls_equal=True)
        .join(sizes, on="_exchange", how="left")
        .with_columns(
            pl.col("_exchange").is_in(main_venues).fill_null(False).alias("main_venue"),
            (pl.col("_share").fill_null(0.0) >= HOME_SHARE).alias("_at_home"),
        )
        .with_columns(
            pl.when(pl.col("main_venue") & pl.col("_at_home"))
            .then(2 + pl.col("_share"))
            .when(pl.col("main_venue"))
            .then(1 + pl.col("_size"))
            .when(pl.col("_at_home"))
            .then(pl.col("_share"))
            .otherwise(0.0)
            .alias("listing_score"),
            (pl.col("_at_home") | pl.col("main_venue")).alias("_candidate"),
        )
    )
    frame = frame.with_columns(link_names(frame).alias("_name"))

    # The usual currency of a market: the most common one of its listings there.
    usual = (
        frame.filter(~pl.col("_delisted") & pl.col("_currency").is_not_null())
        .group_by("_exchange", "_home", "_currency")
        .len()
        .sort("len", descending=True)
        .unique(["_exchange", "_home"], keep="first", maintain_order=True)
        .select("_exchange", "_home", pl.col("_currency").alias("_usual"))
    )
    frame = frame.join(
        usual, on=["_exchange", "_home"], how="left", nulls_equal=True
    ).with_columns(
        (pl.col("_currency") == pl.col("_usual"))
        .fill_null(True)
        .alias("usual_currency")
    )

    def spread(expression: pl.Expr) -> pl.Expr:
        # Over the listings of one instrument: its linked name within a home, or in
        # any home for a listing without one.
        return (
            pl.when(pl.col("_home").is_null())
            .then(expression.max().over("_name"))
            .otherwise(expression.max().over("_name", "_home"))
        )

    best = pl.when(~pl.col("_delisted") & pl.col("_candidate")).then(
        pl.col("listing_score")
    )
    frame = frame.with_columns(spread(best).alias("_best"))
    frame = frame.with_columns(
        pl.when(pl.col("_isin").is_not_null())
        .then(pl.col("_best").max().over("_isin"))
        .otherwise(pl.col("_best"))
        .alias("_best")
    ).with_columns(spread(pl.col("_best")).alias("_best"))

    # Within the best level (home on a main venue, a main venue abroad, home on
    # another venue), listings close to the best one are primary as well.
    level = pl.col("_best").floor()
    threshold = level + PRIMARY_TOLERANCE * (pl.col("_best") - level)
    primary = pl.col("_candidate") & (
        pl.col("_best").is_null() | (pl.col("listing_score") >= threshold)
    )
    # How many listings the instrument has worldwide, a measure of its prominence.
    listed_count = (~pl.col("_delisted")).cast(pl.Int32)
    frame = frame.with_columns(
        pl.when(pl.col("_home").is_null())
        .then(listed_count.sum().over("_name"))
        .otherwise(listed_count.sum().over("_name", "_home"))
        .alias("_listings")
    )
    frame = frame.with_columns(
        pl.when(pl.col("_isin").is_not_null())
        .then(pl.col("_listings").max().over("_isin"))
        .otherwise(pl.col("_listings"))
        .alias("listings")
    )
    return frame.select(
        symbol,
        "listing_score",
        primary.alias("primary_listing"),
        "main_venue",
        "listings",
        "usual_currency",
        (pl.col("_home").is_not_null() | pl.lit("country" not in columns)).alias(
            "home_known"
        ),
    )
