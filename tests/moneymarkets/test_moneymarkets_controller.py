"""Money Markets Controller Tests"""

import pytest

import financedatabase as fd
from tests.helpers import check_search, check_select, check_show_options

moneymarkets = fd.Moneymarkets(use_local_location=True)


SELECT_CASES = [
    {},
    {"currency": "USD"},
    {"family": "BlackRock Funds"},
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
    check_select(moneymarkets, nonempty=len(filters) <= 1, **kwargs)


SHOW_OPTIONS_CASES = [
    {},
    {"selection": "currency"},
    {"selection": "family"},
    {"family": "BlackRock Funds"},
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
    check_show_options(moneymarkets, nonempty=len(filters) <= 1, **kwargs)


SEARCH_CASES = [
    {"summary": "Government"},
    {"index": "RXX"},
    {"currency": "USD"},
    {"family": "BlackRock Funds"},
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
    check_search(moneymarkets, nonempty=len(filters) <= 1, **kwargs)


def test_select_with_invalid_value_raises() -> None:
    """`select(<filter>=...)` raises ValueError for values not in show_options()."""

    for col in ["currency", "family"]:
        with pytest.raises(ValueError, match="not available in the database"):
            moneymarkets.select(**{col: "__definitely_not_a_real_value__"})
