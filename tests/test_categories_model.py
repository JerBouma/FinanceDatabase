"""Categories Model Tests"""

import pandas as pd

from scripts.listings import categories_model


def _etfs(rows: list[tuple]) -> pd.DataFrame:
    return pd.DataFrame(
        rows, columns=["symbol", "name", "isin", "family", "category_group", "category"]
    ).set_index("symbol")


def test_blank_categories_are_learned_from_name_terms_and_isins() -> None:
    """Test that a decisive term fills a consistent pair and issuer words decide nothing."""
    rows = [
        (
            f"T{i}",
            f"Brand{i % 7} Treasury Bond {i}",
            "",
            f"F{i % 7}",
            "Fixed Income",
            "Treasury Bonds",
        )
        for i in range(30)
    ]
    rows += [
        (f"D{i}", f"Deka Fund {i}", "", "Deka", "Fixed Income", "Corporate Bonds")
        for i in range(25)
    ]
    rows += [
        ("NEW1", "Acme Treasury Bond 1-3Y", "", "", "", ""),
        ("NEW2", "Deka Industrie 4.0", "", "Deka", "", ""),
        ("NEW3", "Some fund line", "IE00TEST0001", "", "", ""),
        ("OLD3", "Some fund line other", "IE00TEST0001", "", "Equities", "Small Cap"),
    ]
    frame = _etfs(rows)
    filled = categories_model.fill_etf_categories([frame])
    assert filled == 4
    assert tuple(frame.loc["NEW1", ["category_group", "category"]]) == (
        "Fixed Income",
        "Treasury Bonds",
    )
    assert tuple(frame.loc["NEW2", ["category_group", "category"]]) == ("", "")
    assert tuple(frame.loc["NEW3", ["category_group", "category"]]) == (
        "Equities",
        "Small Cap",
    )
