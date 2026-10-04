"""Funds Test Module"""

from __future__ import annotations

from typing import Any

import pytest

import financedatabase as fd
from tests.structure import check_search, check_select, check_show_options

funds = fd.Funds(use_local_location=True)


SELECT_CASES = [
    {},
    {"currency": "TWD"},
    {"category": "Energy"},
    {"category_group": "Miscellaneous"},
    {"family": "13D Activist Fund"},
    {"exchange": "PAR"},
    {"exchange": "FRA", "category": "Energy"},
]


@pytest.mark.parametrize("kwargs", SELECT_CASES, ids=str)
def test_select(kwargs: dict) -> None:
    """select() matches an independent pandas filter of the same data (structure, not a snapshot)."""
    filters = [
        k
        for k in kwargs
        if k
        not in [
            "case_sensitive",
            "exclude_delisted",
            "only_primary_listing",
            "selection",
        ]
    ]
    check_select(funds, nonempty=len(filters) <= 1, **kwargs)


SHOW_OPTIONS_CASES = [
    {},
    {"selection": "category"},
    {"selection": "category_group"},
    {"selection": "family"},
    {"selection": "currency"},
    {"selection": "exchange"},
    {"exchange": "PAR"},
    {"category": "Energy"},
]


@pytest.mark.parametrize("kwargs", SHOW_OPTIONS_CASES, ids=str)
def test_show_options(kwargs: dict) -> None:
    """show_options() matches an independent pandas filter of the same data (structure, not a snapshot)."""
    filters = [
        k
        for k in kwargs
        if k
        not in [
            "case_sensitive",
            "exclude_delisted",
            "only_primary_listing",
            "selection",
        ]
    ]
    check_show_options(funds, nonempty=len(filters) <= 1, **kwargs)


SEARCH_CASES = [
    {"summary": "Shares"},
    {"index": "GSPX"},
    {"category": "Utilities"},
    {"category_group": "Miscellaneous"},
    {"family": "ivari"},
    {"exchange": "NZE"},
    {"summary": "Pension", "category": "Energy"},
]


@pytest.mark.parametrize("kwargs", SEARCH_CASES, ids=str)
def test_search(kwargs: dict) -> None:
    """search() matches an independent pandas filter of the same data (structure, not a snapshot)."""
    filters = [
        k
        for k in kwargs
        if k
        not in [
            "case_sensitive",
            "exclude_delisted",
            "only_primary_listing",
            "selection",
        ]
    ]
    check_search(funds, nonempty=len(filters) <= 1, **kwargs)


def test_select_with_invalid_value_raises() -> None:
    """`select(<filter>=...)` raises ValueError for values not in show_options()."""

    for col in [
        "category_group",
        "category",
        "family",
        "currency",
        "exchange",
        "mic",
    ]:
        kwargs: dict[str, Any] = {col: "__definitely_not_a_real_value__"}
        with pytest.raises(ValueError, match="not available in the database"):
            funds.select(**kwargs)


def test_select_mic() -> None:
    """`select(mic=...)` filters funds by their ISO 10383 MIC code."""
    assert "mic" in funds.show_options()
    mic = list(funds.show_options(selection="mic"))[0]
    result = funds.select(mic=mic)
    assert not result.empty
    assert (result["mic"] == mic).all()
