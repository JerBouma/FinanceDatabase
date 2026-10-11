"""Listings Model Tests

The rules are tested on a small made-up market: Dutch, German and US companies on
their main venues, US companies only traded over the counter, and cross-listings on a
German regional venue and over the counter, where most companies are foreign.
"""

import polars as pl

from financedatabase import listings_model


def _create_frame(rows: list[tuple]) -> pl.LazyFrame:
    return pl.DataFrame(
        rows,
        schema=["symbol", "name", "exchange", "country", "isin"],
        orient="row",
    ).lazy()


HOME = [(f"NL{i}.AS", f"Dutch {i} N.V.", "AMS", "Netherlands", None) for i in range(20)]
HOME += [(f"DE{i}.DE", f"German {i} AG", "GER", "Germany", None) for i in range(20)]
US = [(f"US{i}", f"American {i} Inc.", "NYQ", "United States", None) for i in range(80)]
US += [(f"OTC{i}", f"Small {i} Inc.", "PNK", "United States", None) for i in range(10)]
CROSS = [
    (f"US{i}.F", f"American {i} Inc.", "FRA", "United States", None) for i in range(30)
]
CROSS += [(f"F{i}.F", f"Other {i} AG", "FRA", "Germany", None) for i in range(2)]
CROSS += [(f"F{i}F", f"Other {i} AG", "PNK", "Germany", None) for i in range(6)]
MARKET = [
    ("ASML.AS", "ASML Holding N.V.", "AMS", "Netherlands", "NL0010273215"),
    ("ASML", "ASML Holding N.V.", "NYQ", "Netherlands", "USN070592100"),
    ("ASMLF", "ASML Holding NV", "PNK", "Netherlands", "NL0010273215"),
    ("ASME.F", "ASML HOLDING EO -,09", "FRA", "Netherlands", None),
    ("ASML.TO", "ASML CDR (CAD Hedged)", "NYQ", "Netherlands", None),
    ("NXPI", "NXP Semiconductors N.V.", "NYQ", "Netherlands", None),
    ("NXP.F", "NXP Semiconductors N.V.", "FRA", "Netherlands", None),
    ("SAP.F", "Regional AG", "FRA", "Germany", None),
    ("TOMA.F", "Dutch 1 ADR", "FRA", None, None),
    *HOME,
    *US,
    *CROSS,
]


def _get_primary(rows: list[tuple]) -> set[str]:
    lazy = _create_frame(rows)
    ranks = listings_model.get_listing_ranks(lazy, listings_model.get_main_venues(lazy))
    return set(ranks.filter("primary_listing").get_column("symbol"))


def test_main_venues_lead_the_country_most_of_their_listings_come_from() -> None:
    """Test that the home exchanges are main venues and cross-trading venues are not."""
    venues = listings_model.get_main_venues(_create_frame(MARKET))
    assert {"AMS", "NYQ"} <= set(venues)
    assert not {"FRA", "PNK"} & set(venues)


def test_home_listing_is_primary() -> None:
    """Test that a company's listing on its home exchange is its primary listing."""
    primary = _get_primary(MARKET)
    assert "ASML.AS" in primary
    assert not {"ASML", "ASMLF", "ASME.F", "ASML.TO"} & primary


def test_largest_main_venue_abroad_without_a_home_listing() -> None:
    """Test a company that is only listed abroad, such as NXP in New York."""
    primary = _get_primary(MARKET)
    assert "NXPI" in primary
    assert "NXP.F" not in primary


def test_home_listing_off_the_main_venues() -> None:
    """Test companies only traded on a secondary venue of their own country."""
    primary = _get_primary(MARKET)
    assert {"OTC0", "SAP.F"} <= primary
    assert "US0.F" not in primary


def test_listing_without_a_country_joins_the_name_it_starts_with() -> None:
    """Test that 'Dutch 1 ADR' without a country is linked to 'Dutch 1 N.V.'."""
    assert "TOMA.F" not in _get_primary(MARKET)


def test_delisted_listings_never_hide_a_listed_one() -> None:
    """Test that a delisted home listing leaves the listing abroad primary."""
    lazy = _create_frame(MARKET).with_columns(
        (pl.col("symbol") == "ASML.AS").alias("delisted")
    )
    ranks = listings_model.get_listing_ranks(lazy, listings_model.get_main_venues(lazy))
    primary = set(ranks.filter("primary_listing").get_column("symbol"))
    assert "ASML" in primary


def test_trailing_words_are_measured_on_the_names() -> None:
    """Test that words ending many names are found and removed from name keys."""
    names = pl.Series(["Alpha Inc.", "Beta Inc", "Gamma N.V.", "Delta Holding"] * 100)
    words = listings_model.get_trailing_words(names)
    assert {"inc", "nv"} <= set(words)
    key = pl.select(
        listings_model.get_name_key(pl.lit("Nestlé S.A. Inc."), ["inc", "sa"])
    ).item()
    assert key == "nestle"


def test_share_classes_and_preferred_shares_are_not_primary() -> None:
    """Test that a company has one primary line per exchange: not its preferreds."""
    market = [
        *MARKET,
        (
            "US0^A",
            "American 0 Inc. Depositary Shares Series A",
            "NYQ",
            "United States",
            None,
        ),
        ("US1-PB", "American 1 Inc.", "NYQ", "United States", None),
        ("US2B", "American 2 Inc.", "NYQ", "United States", None),
    ]
    primary = _get_primary(market)
    assert {"US0", "US1", "US2"} <= primary
    assert not {"US0^A", "US1-PB", "US2B"} & primary


def test_names_match_with_or_without_dots() -> None:
    """Test that 'N.V.' and 'NV' or 'A/S' and 'AS' read the same."""
    words = pl.select(
        listings_model.get_words(pl.lit(pl.Series(["Novo A/S", "Novo AS", "Xyz N.V."])))
    ).to_series()
    assert words.to_list() == ["novo as", "novo as", "xyz nv"]


def test_names_match_without_accents() -> None:
    """Test that accented letters read as their plain letters, not as separators."""
    words = pl.select(
        listings_model.get_words(
            pl.lit(pl.Series(["L’Oréal", "Hermès", "Nestlé S.A.", "Ørsted"]))
        )
    ).to_series()
    assert words.to_list() == ["l oreal", "hermes", "nestle sa", "orsted"]


CURRENCIES = {"AMS": "EUR", "GER": "EUR", "FRA": "EUR", "NYQ": "USD", "PNK": "USD"}
CANADA = [(f"CA{i}.TO", f"Canadian {i} Inc.", "TOR", "Canada", None) for i in range(20)]


def _get_primary_with_currencies(rows: list[tuple]) -> set[str]:
    lazy = pl.DataFrame(
        [(*row, CURRENCIES.get(row[2], "CAD")) for row in rows],
        schema=["symbol", "name", "exchange", "country", "isin", "currency"],
        orient="row",
    ).lazy()
    ranks = listings_model.get_listing_ranks(lazy, listings_model.get_main_venues(lazy))
    return set(ranks.filter("primary_listing").get_column("symbol"))


def test_lines_abroad_in_another_currency_are_not_primary() -> None:
    """Test that a US company in euros on a regional venue full of US lines is not
    at home there, while a German company in euros is."""
    market = [
        *MARKET,
        *CANADA,
        ("GEC.F", "GENL EL CO DL", "FRA", "United States", None),
    ]
    primary = _get_primary_with_currencies(market)
    assert "GEC.F" not in primary
    assert "SAP.F" in primary


def test_local_receipts_are_not_primary() -> None:
    """Test that Canadian receipts of US companies in Toronto are not primary: by a
    name that starts with the company's, or by a word that names such lines only."""
    receipts = [
        (f"US{i}.TO", f"American {i} CDR (CAD Hedged)", "TOR", "United States", None)
        for i in range(25)
    ]
    receipts.append(("MU.TO", "Micron CDR (CAD Hedged)", "TOR", "United States", None))
    primary = _get_primary_with_currencies([*MARKET, *CANADA, *receipts])
    assert "US0" in primary
    assert not {symbol for symbol, *_ in receipts} & primary
    assert "CA0.TO" in primary


def test_one_primary_line_per_company_and_exchange() -> None:
    """Test share classes of the same length (BRK-A, BRK-B) and a symbol that extends
    the company's by a letter (GOOGM), but not a company with a longer symbol."""
    market = [
        *MARKET,
        ("BRK-A", "Berkshire Hathaway Inc.", "NYQ", "United States", "US0846701086"),
        ("BRK-B", "Berkshire Hathaway Inc.", "NYQ", "United States", "US0846707026"),
        ("BRYN.F", "Berkshire Hathaway Inc.", "FRA", "United States", "US0846707026"),
        ("GOOG", "Alphabet Inc.", "NYQ", "United States", "US02079K1079"),
        (
            "GOOGM",
            "Alphabet Inc. Depositary Shares Series A Preferred",
            "NYQ",
            "United States",
            "US02079K4040",
        ),
        ("BX", "Blackstone Inc.", "NYQ", "United States", "US09260D1072"),
        ("BXMT", "Blackstone Mortgage Trust", "NYQ", "United States", "US09257W1009"),
        ("FBNC", "First Bancorp", "NYQ", "United States", "US3189101062"),
        ("FNLC", "First Bancorp", "NYQ", "United States", "US31866P1021"),
    ]
    primary = _get_primary(market)
    assert "BRK-B" in primary
    assert "BRK-A" not in primary
    assert "GOOG" in primary
    assert "GOOGM" not in primary
    assert {"BX", "BXMT", "FBNC", "FNLC"} <= primary


def test_lines_without_a_home_are_never_receipts() -> None:
    """Test that ETFs, which have no country, keep their primary listings on the main
    venues the equities define."""
    rows = [
        (f"E{i}", f"Fund {i} Bitcoin ETF", f"EX{i % 3}", None, None) for i in range(60)
    ]
    lazy = pl.DataFrame(
        [(*row, "USD") for row in rows],
        schema={
            column: pl.String
            for column in ["symbol", "name", "exchange", "country", "isin", "currency"]
        },
        orient="row",
    ).lazy()
    ranks = listings_model.get_listing_ranks(lazy, ["EX0", "EX1", "EX2"])
    assert ranks["primary_listing"].all()
