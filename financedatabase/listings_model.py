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
# A currency of at least this share of a country's listings at home is one of its
# home currencies.
HOME_CURRENCY_SHARE = 0.1
# A word of at least this share of the names that carry it naming lines abroad in
# another currency marks such lines as local receipts ('CDR', 'DRN').
RECEIPT_WORD_SHARE = 0.95
# Listings scoring within this fraction of the best one are primary as well (the
# National Stock Exchange and BSE for an Indian company).
PRIMARY_TOLERANCE = 0.9
# A word that ends at least this share of the names of an asset class is ignored at
# the end of names ('Inc', 'Limited', 'AG', 'Index', 'USD').
TRAILING_WORD_SHARE = 0.003
MAXIMUM_TRAILING_WORDS = 2
# A first word shared by at most this many names of a home links a lone listing to
# the most listed of them.
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
    # Runs of single letters are joined, so 'N.V.', 'S.p.A.' and 'A/S' read as 'nv',
    # 'spa' and 'as' like their spellings without dots.
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
    of an instrument are its best scoring ones, one per exchange (the shortest symbol);
    a listing abroad off the main venues is never primary. Delisted entries never hide
    a listed one.

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
    # A listing without a country takes the one its other listings agree on: the
    # most common country of its ISIN, else of its name.
    frame = frame.with_columns(
        pl.coalesce(
            "_home",
            pl.when(pl.col("_isin").is_not_null()).then(
                pl.col("_home").drop_nulls().mode().first().over("_isin")
            ),
            pl.col("_home").drop_nulls().mode().first().over("_name"),
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
    sizes = (
        listed.filter(pl.col("_exchange").is_in(main_venues))
        .group_by("_exchange")
        .len()
        .with_columns((pl.col("len") / pl.col("len").sum()).alias("_size"))
        .drop("len")
    )

    # The currencies a country's companies trade in at home: those of a tenth or more
    # of their listings on main venues where they make up a share of the listings
    # (yuan and Hong Kong dollars for Chinese companies, not Canadian dollars for US
    # ones).
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
    # The country that leads a venue: the home most of its listings come from.
    venue_countries = (
        listed.filter(pl.col("_home").is_not_null())
        .group_by("_exchange", "_home")
        .len()
        .sort("len", "_home", descending=[True, False])
        .unique("_exchange", keep="first", maintain_order=True)
        .select("_exchange", pl.col("_home").alias("_venue_country"))
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
            # A listing at home only counts as one in a home currency (when its home
            # has any), or on a main venue its home leads (UK companies in dollars in London): a US company
            # in euros in Düsseldorf or in Canadian dollars in Toronto is a line
            # abroad, however many such lines there are.
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
    # A line abroad in another currency whose name starts with that of a share listed
    # at home is a local receipt of it ('GE Aerospace CDR (CAD Hedged)' in Toronto).
    home_names = (
        frame.filter(pl.col("main_venue") & pl.col("_home_line") & ~pl.col("_delisted"))
        .select("_home", pl.col("_name").alias("_prefix"))
        .unique()
    )
    abroad = (
        pl.col("main_venue")
        & ~pl.col("_home_line")
        & ~pl.col("_home_currency").fill_null(False)
        & pl.col("_currency").is_not_null()
    )
    words = pl.col("_name").str.split(" ")
    lines_abroad = frame.filter(abroad).select(
        symbol,
        "_home",
        pl.int_ranges(1, words.list.len()).alias("_length"),
        words.alias("_words"),
    )
    receipts = (
        lines_abroad.explode("_length")
        .drop_nulls("_length")
        .select(
            symbol,
            "_home",
            pl.col("_words")
            .list.head(pl.col("_length"))
            .list.join(" ")
            .alias("_prefix"),
        )
        .join(home_names, on=["_home", "_prefix"], how="semi")
        .get_column(symbol)
        if lines_abroad.height
        else pl.Series(symbol, [], dtype=pl.String)
    )
    # And so is a line abroad with a word that almost only names such lines ('CDR',
    # 'Hedged', 'DRN' for a Brazilian depositary receipt).
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
    receipts = pl.concat(
        [
            receipts,
            names.filter(
                pl.col("_abroad")
                & pl.col("_word")
                .list.eval(pl.element().is_in(receipt_words.implode()))
                .list.any()
            ).get_column(symbol),
        ]
    )
    frame = frame.with_columns(
        (pl.col("_candidate") & ~pl.col(symbol).is_in(receipts.implode())).alias(
            "_candidate"
        )
    )
    frame = frame.with_columns(link_names(frame).alias("_name"))

    # An instrument without a listing on a main venue at home, whose name is that of
    # an instrument with one in another country, is that instrument with a wrong
    # country (American Express Company on Toronto, tagged Canada).
    home_main = pl.col("_at_home") & pl.col("main_venue") & ~pl.col("_delisted")
    frame = frame.with_columns(
        home_main.any().over("_name", "_home").alias("_has_home"),
        pl.when(home_main).then(pl.col("_home")).alias("_main_home"),
    ).with_columns(
        pl.when(~pl.col("_has_home"))
        .then(
            pl.coalesce(
                pl.col("_main_home").drop_nulls().mode().first().over("_name"),
                pl.col("_home"),
            )
        )
        .otherwise(pl.col("_home"))
        .alias("_home")
    )

    # A line whose symbol is another listing's symbol plus a class suffix (FHN^E for
    # FHN, POW-PC.TO for POW.TO) and whose name starts with that listing's name is a
    # share class or preferred share of that company, and never its primary listing.
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
    # Likewise a line whose symbol and name extend those of a listing on the same
    # exchange, by the same issuer (the first eight characters of the ISIN) or by one
    # letter when an ISIN is missing (GOOGM, 'Alphabet Inc. Depositary Shares ...
    # Preferred Stock', for GOOG, but not BXMT, Blackstone Mortgage Trust, for BX).
    lines = frame.select(
        symbol,
        "_exchange",
        "_home",
        "_name",
        _first=pl.col("_name").str.extract(r"^(\S+)"),
        _issuer=pl.col("_isin").str.slice(0, 8),
    )
    extensions = (
        lines.join(
            lines.rename(
                {symbol: "_other", "_name": "_other_name", "_issuer": "_other_issuer"}
            ).drop("_home"),
            on=["_exchange", "_first"],
        )
        .filter(
            (pl.col(symbol) != pl.col("_other"))
            & pl.col(symbol).str.starts_with(pl.col("_other"))
            & pl.col("_name").str.starts_with(pl.col("_other_name") + " ")
            & (pl.col("_issuer") == pl.col("_other_issuer")).fill_null(
                pl.col(symbol).str.len_chars() == pl.col("_other").str.len_chars() + 1
            )
        )
        .unique(symbol)
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
        .then(pl.col("_best").max().over("_isin", "_home"))
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
    # On one exchange an instrument has one primary line: the shortest symbol, so BAC
    # and not its preferred shares BAC-PB, GOOG and not GOOGL, TSI.BK and not its
    # NVDR TSI-R.BK.
    frame = frame.with_columns(primary.alias("_primary"))
    length = pl.col(symbol).str.len_chars()
    shortest = (
        pl.when(pl.col("_primary") & ~pl.col("_delisted"))
        .then(length)
        .min()
        .over("_name", "_home", "_exchange")
    )
    # A line off the main venues is only primary when no main venue lists the same name
    # in any country, which guards against a wrong country on a regional line.
    on_main_venue = (pl.col("main_venue") & ~pl.col("_delisted")).any().over("_name")
    # Share classes of one name and issuer with symbols of the same length (BRK-A,
    # BRK-B): the one whose ISIN is listed on the most exchanges, the first symbol when
    # that ties.
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
    # How many listings the instrument has worldwide, a measure of its prominence.
    # Counted as exchanges, so preferred shares on the same exchange add nothing.
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
