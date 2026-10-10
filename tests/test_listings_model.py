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
    assert {"inc", "v"} <= set(words)
    key = pl.select(
        listings_model.get_name_key(pl.lit("Nestlé S.A. Inc."), ["inc", "a", "s"])
    ).item()
    assert key == "nestle"
