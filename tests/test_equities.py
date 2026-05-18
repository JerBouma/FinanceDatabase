"""Currencies Test Module"""

import financedatabase as fd

equities = fd.Equities()


# pylint: disable=missing-function-docstring


def test_select(recorder):
    recorder.capture(equities.select().iloc[:5])
    recorder.capture(equities.select(country="Canada").iloc[:5])
    recorder.capture(equities.select(sector="Communication Services").iloc[:5])
    recorder.capture(equities.select(industry_group="Insurance").iloc[:5])
    recorder.capture(equities.select(market_cap="Large Cap").iloc[:5])
    recorder.capture(equities.select(exchange="AMS").iloc[:5])
    recorder.capture(
        equities.select(country="United States", sector="Financials").iloc[:5]
    )
    recorder.capture(
        equities.select(
            country="United States", industry_group="Media & Entertainment"
        ).iloc[:5]
    )
    recorder.capture(equities.select(sector="Energy", industry_group="Energy").iloc[:5])
    recorder.capture(
        equities.select(
            country="United States",
            sector="Health Care",
            industry_group="Pharmaceuticals, Biotechnology & Life Sciences",
        ).iloc[:5]
    )
    recorder.capture(
        equities.select(
            country="United States",
            sector="Utilities",
            industry_group="Utilities",
            industry="Electric Utilities",
            market="NASDAQ Global Select",
        ).iloc[:5]
    )
    recorder.capture(
        equities.select(
            country="United States",
            sector="Materials",
            industry_group="Materials",
            market="Johannesburg Stock Exchange",
            currency="USD",
        ).iloc[:5]
    )
    recorder.capture(
        equities.select(
            country="Japan",
            sector="Energy",
            industry_group="Energy",
            market="Tokyo Stock Exchange",
            currency="JPY",
            only_primary_listing=True,
        ).iloc[:5]
    )


def test_show_options(recorder):
    recorder.capture(list(equities.show_options()))
    recorder.capture(list(equities.show_options(selection="country")))
    recorder.capture(list(equities.show_options(selection="sector")))
    recorder.capture(list(equities.show_options(selection="industry_group")))
    recorder.capture(list(equities.show_options(selection="market_cap")))
    recorder.capture(list(equities.show_options(country="Canada")))
    recorder.capture(list(equities.show_options(sector="Communication Services")))
    recorder.capture(list(equities.show_options(industry_group="Insurance")))
    recorder.capture(list(equities.show_options(market_cap="Large Cap")))
    recorder.capture(
        list(equities.show_options(selection="country", country="United States"))
    )
    recorder.capture(
        list(equities.show_options(selection="sector", sector="Financials"))
    )
    recorder.capture(
        list(
            equities.show_options(
                selection="industry_group", industry_group="Media & Entertainment"
            )
        )
    )
    recorder.capture(
        list(equities.show_options(selection="market_cap", market_cap="Large Cap"))
    )


def test_exchange_market_one_to_one():
    """Each `exchange` code must map to exactly one `market` label.

    Drift between these two columns is a recurring data-quality issue.
    This test fails fast if any exchange code becomes
    ambiguous, preventing future PRs from re-introducing the
    inconsistency.

    The reverse direction is not asserted: one `market` label may
    legitimately cover several exchange tiers (e.g. "OTC Bulletin
    Board" covers PNK / OQB / OID / OEM / OQX).

    Reads `database/equities.csv` directly so the assertion is against
    the source of truth — the compressed library payload lags the CSV
    until the maintainer regenerates it post-merge.
    """
    import pandas as pd

    df = pd.read_csv("database/equities.csv", dtype=str)
    pairs = df.dropna(subset=["exchange", "market"])

    by_exchange = pairs.groupby("exchange")["market"].nunique()
    ambiguous = by_exchange[by_exchange > 1]
    assert (
        ambiguous.empty
    ), f"Exchange codes mapping to multiple market labels: {ambiguous.to_dict()}"


def test_search(recorder):
    recorder.capture(equities.search(summary="apple").iloc[:5])
    recorder.capture(equities.search(index="AAPL").iloc[:5])
    recorder.capture(equities.search(country="Canada").iloc[:5])
    recorder.capture(equities.search(sector="Communication Services").iloc[:5])
    recorder.capture(equities.search(industry_group="Insurance").iloc[:5])
    recorder.capture(equities.search(market_cap="Large Cap").iloc[:5])
    recorder.capture(
        equities.search(country="United States", sector="Financials").iloc[:5]
    )
    recorder.capture(
        equities.search(
            country="United States", industry_group="Media & Entertainment"
        ).iloc[:5]
    )
    recorder.capture(equities.search(sector="Energy", industry_group="Energy").iloc[:5])
    recorder.capture(
        equities.search(
            country="United States", sector="Industrials", industry_group="Software"
        ).iloc[:5]
    )
