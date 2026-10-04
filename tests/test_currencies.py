"""Currencies Test Module"""

from __future__ import annotations

import pytest

import financedatabase as fd
from tests.structure import check_search, check_select, check_show_options

currencies = fd.Currencies(use_local_location=True)


SELECT_CASES = [
    {},
    {"base_currency": "USD"},
    {"quote_currency": "EUR"},
    {"base_currency": "USD", "quote_currency": "CAD"},
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
    check_select(currencies, nonempty=len(filters) <= 1, **kwargs)


SHOW_OPTIONS_CASES = [
    {},
    {"selection": "base_currency"},
    {"selection": "quote_currency"},
    {"base_currency": "USD"},
    {"quote_currency": "EUR"},
    {"selection": "base_currency", "base_currency": "USD"},
    {"selection": "quote_currency", "quote_currency": "EUR"},
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
    check_show_options(currencies, nonempty=len(filters) <= 1, **kwargs)


SEARCH_CASES = [
    {"summary": "dollar"},
    {"index": "USD"},
    {"base_currency": "CAD"},
    {"quote_currency": "EUR"},
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
    check_search(currencies, nonempty=len(filters) <= 1, **kwargs)


def test_select_with_invalid_value_raises() -> None:
    """`select(<filter>=...)` raises ValueError for values not in show_options()."""

    for col in ["base_currency", "quote_currency"]:
        with pytest.raises(ValueError, match="not available in the database"):
            currencies.select(**{col: "__definitely_not_a_real_value__"})
