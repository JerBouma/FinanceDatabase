"""Listings Model"""

__docformat__ = "google"

import polars as pl

# Minimum share of a home, relative to the top venue's, to lead it (NYSE and NASDAQ).
LEADING_FRACTION = 0.8
# Listings added to every exchange so a tiny venue cannot lead a country at 100%.
PRIOR_LISTINGS = 20
# Minimum share of an exchange's listings for it to be a home market of a country.
HOME_SHARE = 0.05
# Minimum share of a country's home listings for a currency to be a home currency.
HOME_CURRENCY_SHARE = 0.1
# Minimum share of lines abroad among names with a word to mark receipts ('CDR').
RECEIPT_WORD_SHARE = 0.95
# Listings within this fraction of the best score are primary too (NSE and BSE).
PRIMARY_TOLERANCE = 0.9
# Minimum share of names a word ends to be ignored at the end ('Inc', 'AG', 'USD').
TRAILING_WORD_SHARE = 0.003
MAXIMUM_TRAILING_WORDS = 2
# Maximum names of a home sharing a first word for it to link a lone listing.
DISTINCTIVE_WORD_NAMES = 5
NON_WORD = r"[^a-z0-9]+"
# Letters that Unicode does not split into a letter and an accent.
LETTERS_WITHOUT_ACCENT = {"ø": "o", "æ": "ae", "œ": "oe", "ß": "ss", "ł": "l", "đ": "d"}
# The class or series suffix of a symbol: BAC-PB, FHN^E, POW-PC.TO, TSI-R.BK.
CLASS_SUFFIX = r"[-^][A-Z0-9]+(\.[A-Z]+)?$"


def get_words(name: pl.Expr) -> pl.Expr:
    """
    Get a name in lowercase words separated by single spaces, without accents.

    Args:
        name (pl.Expr): The name column.

    Returns:
        pl.Expr: The words.
    """
    # Runs of single letters are joined, so 'N.V.' and 'S.p.A.' read as 'nv' and 'spa'.
    return (
        name.str.normalize("NFKD")
        .str.replace_all(r"\p{Mn}", "")
        .str.to_lowercase()
        .str.replace_many(LETTERS_WITHOUT_ACCENT)
        .str.replace_all(NON_WORD, " ")
        .str.strip_chars()
        .str.replace_all(r"\b([a-z]) ([a-z]) ([a-z])\b", "$1$2$3")
        .str.replace_all(r"\b([a-z]) ([a-z])\b", "$1$2")
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
    Get a name without punctuation and the trailing words of its asset class.

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
    Get the home of each instrument: its country, else its ISIN country, else currency.

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
    Get the exchanges that lead the home most of their listings come from.

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
    Get every word-for-word start of each name ('asml', 'asml holding').

    Args:
        keys (pl.DataFrame): The column "_name".

    Returns:
        pl.DataFrame: The columns "_name", "_prefix" and "_size", its number of words.
    """
    if keys.is_empty():
        return pl.DataFrame(
            schema={"_name": pl.String, "_size": pl.Int64, "_prefix": pl.String}
        )
    return (
        keys.select("_name")
        .unique()
        .with_columns(
            pl.col("_name").str.split(" ").cast(pl.List(pl.String)).alias("_words")
        )
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

    Args:
        frame (pl.DataFrame): The columns "_name", "_home", "_at_home", "main_venue".

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
            .sort("len", "_name", descending=[True, False])
            .unique(["_first", "_home"], keep="first", maintain_order=True)
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

    Args:
        lazy (pl.LazyFrame): The dataset, symbol column first, with an exchange column.
        main_venues (list[str]): The main venues, see get_main_venues.

    Returns:
        pl.DataFrame: The symbol, "listing_score", "primary_listing", "main_venue",
            "listings", "usual_currency" and "home_known" columns.
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
    # A listing without a country takes the most common one of its ISIN, else name.
    frame = frame.with_columns(
        pl.coalesce(
            "_home",
            pl.when(pl.col("_isin").is_not_null()).then(
                pl.col("_home").drop_nulls().mode().min().over("_isin")
            ),
            pl.col("_home").drop_nulls().mode().min().over("_name"),
        ).alias("_home")
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
    # The country that leads a venue: the home most of its listings come from.
    venue_countries = (
        listed.filter(pl.col("_home").is_not_null())
        .group_by("_exchange", "_home")
        .len()
        .sort("len", "_home", descending=[True, False])
        .unique("_exchange", keep="first", maintain_order=True)
        .select("_exchange", pl.col("_home").alias("_venue_country"))
    )
    # A venue's size: the listings of its own country, so foreign lines don't count.
    sizes = (
        listed.join(venue_countries, on="_exchange")
        .filter(
            pl.col("_exchange").is_in(main_venues)
            & (pl.col("_home") == pl.col("_venue_country"))
        )
        .group_by("_exchange")
        .len()
        .with_columns((pl.col("len") / pl.col("len").sum()).alias("_size"))
        .drop("len")
    )

    # Home currencies: those of a tenth or more of a country's home main-venue listings.
    home_currencies = (
        listed.join(shares, on=["_exchange", "_home"], how="inner")
        .filter(
            pl.col("_exchange").is_in(main_venues)
            & (pl.col("_share") >= HOME_SHARE)
            & pl.col("_currency").is_not_null()
        )
        .group_by("_home", "_currency")
        .len()
        .filter(
            pl.col("len") >= HOME_CURRENCY_SHARE * pl.col("len").sum().over("_home")
        )
        .select("_home", "_currency", pl.lit(True).alias("_home_currency"))
    )

    frame = (
        frame.join(shares, on=["_exchange", "_home"], how="left", nulls_equal=True)
        .join(sizes, on="_exchange", how="left")
        .join(home_currencies, on=["_home", "_currency"], how="left")
        .join(
            home_currencies.select("_home", _currencies_known=pl.lit(True)).unique(),
            on="_home",
            how="left",
        )
        .join(venue_countries, on="_exchange", how="left")
        .with_columns(
            pl.col("_exchange").is_in(main_venues).fill_null(False).alias("main_venue"),
        )
        .with_columns(
            (pl.col("_share").fill_null(0.0) >= HOME_SHARE).alias("_at_home"),
        )
        .with_columns(
            # At home only in a home currency or on a main venue its home leads.
            (
                pl.col("_at_home")
                & (
                    pl.col("_home_currency").fill_null(False)
                    | ~pl.col("_currencies_known").fill_null(False)
                    | pl.col("_currency").is_null()
                    | (
                        pl.col("main_venue")
                        & (pl.col("_venue_country") == pl.col("_home")).fill_null(True)
                    )
                )
            ).alias("_home_line"),
        )
        .with_columns(
            pl.when(pl.col("main_venue") & pl.col("_home_line"))
            .then(2 + pl.col("_share"))
            .when(pl.col("main_venue"))
            .then(1 + pl.col("_size"))
            .when(pl.col("_home_line"))
            .then(pl.col("_share"))
            .otherwise(0.0)
            .alias("listing_score"),
            (pl.col("_home_line") | pl.col("main_venue")).alias("_candidate"),
        )
    )
    # A line abroad named after a share listed at home is a local receipt ('GE CDR').
    home_names = (
        frame.filter(pl.col("main_venue") & pl.col("_home_line") & ~pl.col("_delisted"))
        .select("_home", pl.col("_name").alias("_prefix"))
        .unique()
    )
    # Only a line with a known home can be abroad; ETFs and indices have no country.
    abroad = (
        pl.col("_home").is_not_null()
        & pl.col("main_venue")
        & ~pl.col("_home_line")
        & ~pl.col("_home_currency").fill_null(False)
        & pl.col("_currency").is_not_null()
    )
    words = pl.col("_name").str.split(" ")
    starts = (
        frame.filter(abroad)
        .select(
            symbol,
            "_home",
            pl.int_ranges(1, words.list.len()).alias("_length"),
            words.alias("_words"),
        )
        .explode("_length")
        .drop_nulls("_length")
    )
    receipts = (
        starts.select(
            symbol,
            "_home",
            pl.col("_words")
            .list.head(pl.col("_length"))
            .list.join(" ")
            .alias("_prefix"),
        )
        .join(home_names, on=["_home", "_prefix"], how="semi")
        .get_column(symbol)
        if starts.height
        else pl.Series(symbol, [], dtype=pl.String)
    )
    # So is a line abroad with a word that almost only names such lines ('CDR', 'DRN').
    names = frame.filter(~pl.col("_delisted")).select(
        symbol,
        abroad.alias("_abroad"),
        get_words(pl.col("_full_name")).str.split(" ").list.unique().alias("_word"),
    )
    receipt_words = (
        names.explode("_word")
        .group_by("_word")
        .agg(pl.col("_abroad").sum().alias("_lines"), pl.len().alias("_total"))
        .filter(
            (pl.col("_lines") >= PRIOR_LISTINGS)
            & (pl.col("_lines") >= RECEIPT_WORD_SHARE * pl.col("_total"))
        )
        .get_column("_word")
    )
    # And a line abroad whose symbol has a shape almost only such lines have (B3's '34').
    digits = pl.col(symbol).str.extract(r"^[A-Za-z]+(\d+)(?:\.[A-Za-z]+)?$")
    shapes = frame.filter(~pl.col("_delisted")).select(
        symbol,
        abroad.alias("_abroad"),
        pl.concat_str(
            "_exchange", digits.str.slice(0, 1), digits.str.len_chars().cast(pl.String)
        ).alias("_shape"),
    )
    receipt_shapes = (
        shapes.drop_nulls("_shape")
        .group_by("_shape")
        .agg(pl.col("_abroad").sum().alias("_lines"), pl.len().alias("_total"))
        .filter(
            (pl.col("_lines") >= PRIOR_LISTINGS)
            & (pl.col("_lines") >= RECEIPT_WORD_SHARE * pl.col("_total"))
        )
        .get_column("_shape")
    )
    receipts = pl.concat(
        [
            receipts,
            names.filter(
                pl.col("_abroad")
                & pl.col("_word")
                .list.eval(pl.element().is_in(receipt_words.implode()))
                .list.any()
            ).get_column(symbol),
            shapes.filter(
                pl.col("_abroad") & pl.col("_shape").is_in(receipt_shapes.implode())
            ).get_column(symbol),
        ]
    )
    frame = frame.with_columns(
        (pl.col("_candidate") & ~pl.col(symbol).is_in(receipts.implode())).alias(
            "_candidate"
        )
    )
    frame = frame.with_columns(link_names(frame).alias("_name"))

    # A name without a home main-venue listing takes the country of one that has it.
    home_main = pl.col("_at_home") & pl.col("main_venue") & ~pl.col("_delisted")
    frame = frame.with_columns(
        home_main.any().over("_name", "_home").alias("_has_home"),
        pl.when(home_main).then(pl.col("_home")).alias("_main_home"),
    ).with_columns(
        pl.when(~pl.col("_has_home"))
        .then(
            pl.coalesce(
                pl.col("_main_home").drop_nulls().mode().min().over("_name"),
                pl.col("_home"),
            )
        )
        .otherwise(pl.col("_home"))
        .alias("_home")
    )

    # A symbol plus class suffix with the same name is a share class (FHN^E for FHN).
    parents = frame.select(
        pl.col(symbol).alias("_base"), pl.col("_name").alias("_parent")
    )
    frame = (
        frame.with_columns(
            pl.col(symbol).str.replace(CLASS_SUFFIX, "$1").alias("_base")
        )
        .join(parents, on="_base", how="left")
        .with_columns(
            (
                (pl.col("_base") != pl.col(symbol))
                & (
                    (pl.col("_name") == pl.col("_parent"))
                    | pl.col("_name").str.starts_with(pl.col("_parent") + " ")
                ).fill_null(False)
            ).alias("_class_line")
        )
        .with_columns(
            pl.when("_class_line")
            .then(pl.col("_parent"))
            .otherwise(pl.col("_name"))
            .alias("_name")
        )
        .drop("_base", "_parent")
    )
    # So is a line extending a symbol and name by the same issuer (GOOGM for GOOG).
    lines = frame.select(
        symbol, "_exchange", "_name", _issuer=pl.col("_isin").str.slice(0, 8)
    )
    others = lines.rename(
        {symbol: "_other", "_name": "_other_name", "_issuer": "_other_issuer"}
    )
    # Joined on each shorter start of the symbol, so the join stays as long as the data.
    extensions = (
        lines.with_columns(
            pl.int_ranges(1, pl.col(symbol).str.len_chars()).alias("_length")
        )
        .explode("_length")
        .drop_nulls("_length")
        .with_columns(pl.col(symbol).str.slice(0, pl.col("_length")).alias("_other"))
        .join(others, on=["_exchange", "_other"])
        .filter(
            pl.col("_name").str.starts_with(pl.col("_other_name") + " ")
            & (pl.col("_issuer") == pl.col("_other_issuer")).fill_null(
                pl.col(symbol).str.len_chars() == pl.col("_other").str.len_chars() + 1
            )
        )
        .sort(symbol, "_length", descending=[False, True])
        .unique(symbol, keep="first", maintain_order=True)
        .select(symbol, pl.col("_other_name").alias("_extended"))
    )
    frame = (
        frame.join(extensions, on=symbol, how="left")
        .with_columns(
            (pl.col("_class_line") | pl.col("_extended").is_not_null()).alias(
                "_class_line"
            ),
            pl.coalesce("_extended", "_name").alias("_name"),
        )
        .drop("_extended")
    )

    # The usual currency of a market: the most common one of its listings there.
    usual = (
        frame.filter(~pl.col("_delisted") & pl.col("_currency").is_not_null())
        .group_by("_exchange", "_home", "_currency")
        .len()
        .sort("len", "_currency", descending=[True, False])
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
        # Over one instrument: its linked name within a home, or any home without one.
        return (
            pl.when(pl.col("_home").is_null())
            .then(expression.max().over("_name"))
            .otherwise(expression.max().over("_name", "_home"))
        )

    # Abroad, a line without the share's ISIN only counts when no line abroad has one.
    line_abroad = pl.col("_candidate") & pl.col("main_venue") & ~pl.col("_home_line")
    with_isin = (
        (line_abroad & pl.col("_isin").is_not_null() & ~pl.col("_delisted"))
        .any()
        .over("_name", "_home")
    )
    frame = frame.with_columns(
        (
            pl.col("_candidate")
            & ~(line_abroad & pl.col("_isin").is_null() & with_isin)
        ).alias("_candidate")
    )
    best = pl.when(~pl.col("_delisted") & pl.col("_candidate")).then(
        pl.col("listing_score")
    )
    frame = frame.with_columns(spread(best).alias("_best"))
    frame = frame.with_columns(
        pl.when(pl.col("_isin").is_not_null())
        .then(pl.col("_best").max().over("_isin", "_home"))
        .otherwise(pl.col("_best"))
        .alias("_best")
    ).with_columns(spread(pl.col("_best")).alias("_best"))

    # Within the best level, listings close to the best one are primary as well.
    level = pl.col("_best").floor()
    threshold = level + PRIMARY_TOLERANCE * (pl.col("_best") - level)
    primary = pl.col("_candidate") & (
        pl.col("_best").is_null() | (pl.col("listing_score") >= threshold)
    )
    # One primary line per exchange: the shortest symbol (BAC, not BAC-PB).
    frame = frame.with_columns(primary.alias("_primary"))
    length = pl.col(symbol).str.len_chars()
    shortest = (
        pl.when(pl.col("_primary") & ~pl.col("_delisted"))
        .then(length)
        .min()
        .over("_name", "_home", "_exchange")
    )
    # A line off the main venues is only primary when no main venue lists the name.
    on_main_venue = (pl.col("main_venue") & ~pl.col("_delisted")).any().over("_name")
    # Equal-length share classes (BRK-A, BRK-B): the ISIN on most exchanges, then first.
    frame = frame.with_columns(
        pl.col("_isin").str.slice(0, 8).alias("_issuer"),
        pl.when(pl.col("_isin").is_not_null() & ~pl.col("_delisted"))
        .then(pl.col("_exchange").n_unique().over("_isin"))
        .fill_null(0)
        .alias("_reach"),
    )
    tied = pl.col("_primary") & ~pl.col("_delisted") & (length == shortest)
    groups = ["_full_name", "_issuer", "_home", "_exchange"]
    frame = frame.with_columns(tied.alias("_tied")).with_columns(
        pl.when("_tied").then("_reach").max().over(groups).alias("_widest")
    )
    frame = frame.with_columns(
        pl.when(pl.col("_tied") & (pl.col("_reach") == pl.col("_widest")))
        .then(pl.col(symbol))
        .min()
        .over(groups)
        .alias("_first")
    )
    first = pl.col("_first")
    primary = (
        pl.col("_primary")
        & ~pl.col("_class_line")
        & (shortest.is_null() | (length <= shortest))
        & (~pl.col("_tied") | first.is_null() | (pl.col(symbol) == first))
        & (pl.col("main_venue") | ~on_main_venue)
    )
    # Listings worldwide as a measure of prominence, counted as distinct exchanges.
    listed_exchange = pl.when(~pl.col("_delisted")).then(pl.col("_exchange"))
    frame = frame.with_columns(
        pl.when(pl.col("_home").is_null())
        .then(listed_exchange.n_unique().over("_name"))
        .otherwise(listed_exchange.n_unique().over("_name", "_home"))
        .cast(pl.Int32)
        .alias("_listings")
    )
    frame = frame.with_columns(
        pl.when(pl.col("_isin").is_not_null())
        .then(pl.col("_listings").max().over("_isin", "_home"))
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
