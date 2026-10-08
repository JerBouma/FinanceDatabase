"""Query Model Tests"""

import logging

import polars as pl
import pytest

from financedatabase import query_model

FRAME = pl.DataFrame(
    {
        "symbol": ["AAA", "AAA.L", "BBB", "OLD"],
        "name": ["Alpha Bank", "Alpha Bank", "Beta Energy", None],
        "sector": ["Financials", "Financials", "Energy", "Energy"],
        "delisted": [False, False, False, True],
    }
).lazy()


def test_exclude_delisted_rows() -> None:
    """Test that delisted rows are only excluded when requested."""
    assert query_model.count_rows(query_model.exclude_delisted_rows(FRAME, True)) == 3
    assert query_model.count_rows(query_model.exclude_delisted_rows(FRAME, False)) == 4


def test_validate_filter_values_ignores_case() -> None:
    """Test that filter values are validated case-insensitively."""
    options = query_model.get_lowercase_options(FRAME, "sector")
    query_model.validate_filter_values(["ENERGY"], options, "sector", "sectors")
    with pytest.raises(ValueError, match="The sector 'Tech' is not available"):
        query_model.validate_filter_values(["Tech"], options, "sector", "sectors")


def test_filter_rows_and_primary_listings() -> None:
    """Test that filters ignore case and primary listings drop exchange suffixes."""
    financials = query_model.filter_rows(FRAME, "sector", ["financials"])
    primary = query_model.filter_primary_listings(financials, "symbol")
    assert primary.collect().get_column("symbol").to_list() == ["AAA"]


def test_match_pattern_falls_back_to_python_regex() -> None:
    """Test that look-ahead, which Polars doesn't support, still matches."""
    expression = query_model.match_pattern(pl.col("name"), "^(?=.*Alpha)", False)
    assert FRAME.filter(expression).collect().height == 2


def test_search_rows_ignores_unknown_columns(caplog) -> None:
    """Test that an unknown search column is logged and ignored."""
    logger = logging.getLogger("financedatabase")
    logger.addHandler(caplog.handler)
    try:
        result = query_model.search_rows(
            FRAME, {"unknown": "x", "name": "beta"}, FRAME.collect_schema().names()
        )
    finally:
        logger.removeHandler(caplog.handler)
    assert result.collect().get_column("symbol").to_list() == ["BBB"]
    assert "unknown is not a valid column" in caplog.text


def test_get_sorted_options() -> None:
    """Test that options are sorted, unique and without missing values."""
    unique = query_model.get_unique_values(FRAME, ["sector", "name"])
    assert list(query_model.get_sorted_options(unique["sector"])) == [
        "Energy",
        "Financials",
    ]
    assert query_model.get_sorted_options(
        unique["name"], as_pandas=False
    ).to_list() == [
        "Alpha Bank",
        "Beta Energy",
    ]
