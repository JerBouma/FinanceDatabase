"""Indices Test Module"""

from __future__ import annotations

import pytest

import financedatabase as fd
from tests.structure import check_search, check_select, check_show_options

indices = fd.Indices(use_local_location=True)


SELECT_CASES = [
    {},
    {"currency": "NOK"},
    {"category": "Industrials"},
    {"category_group": "Cash"},
    {"exchange": "ASX"},
    {"exchange": "ASX", "category": "REITs"},
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
    check_select(indices, nonempty=len(filters) <= 1, **kwargs)


SHOW_OPTIONS_CASES = [
    {},
    {"selection": "category"},
    {"selection": "category_group"},
    {"selection": "currency"},
    {"selection": "exchange"},
    {"exchange": "ASX"},
    {"category": "REITs"},
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
    check_show_options(indices, nonempty=len(filters) <= 1, **kwargs)


SEARCH_CASES = [
    {"summary": "S&P"},
    {"index": "GSPC"},
    {"category": "Industrials"},
    {"category_group": "Energy"},
    {"exchange": "SHH"},
    {"summary": "S&P", "category": "Financials"},
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
    check_search(indices, nonempty=len(filters) <= 1, **kwargs)


def test_select_with_invalid_value_raises() -> None:
    """`select(<filter>=...)` raises ValueError for values not in show_options()."""
    for col in ["currency", "exchange", "mic"]:
        with pytest.raises(ValueError, match="not available in the database"):
            indices.select(**{col: "__definitely_not_a_real_value__"})


def test_select_mic() -> None:
    """`select(mic=...)` filters indices by their ISO 10383 MIC code."""
    assert "mic" in indices.show_options()
    mic = list(indices.show_options(selection="mic"))[0]
    result = indices.select(mic=mic)
    assert not result.empty
    assert (result["mic"] == mic).all()
