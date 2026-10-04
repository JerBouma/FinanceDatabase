"""ETFs Test Module"""

from __future__ import annotations

from typing import Any

import pytest

import financedatabase as fd
from tests.structure import check_search, check_select, check_show_options

etfs = fd.ETFs(use_local_location=True)


SELECT_CASES = [
    {},
    {"category": "Blend"},
    {"category_group": "Materials"},
    {"family": "ProShares"},
    {"exchange": "PCX"},
    {"exchange": "CPH", "category": "Financials"},
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
    check_select(etfs, nonempty=len(filters) <= 1, **kwargs)


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
    check_show_options(etfs, nonempty=len(filters) <= 1, **kwargs)


SEARCH_CASES = [
    {"summary": "Apple"},
    {"index": "VOO"},
    {"category": "Utilities"},
    {"category_group": "Materials"},
    {"family": "ASYMshares"},
    {"exchange": "PCX"},
    {"summary": "North America", "category": "Financials"},
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
    check_search(etfs, nonempty=len(filters) <= 1, **kwargs)


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
            etfs.select(**kwargs)


def test_select_mic() -> None:
    """`select(mic=...)` filters ETFs by their ISO 10383 MIC code."""
    assert "mic" in etfs.show_options()
    mic = list(etfs.show_options(selection="mic"))[0]
    result = etfs.select(mic=mic)
    assert not result.empty
    assert (result["mic"] == mic).all()


def test_select_excludes_delisted_by_default() -> None:
    """Delisted ETFs are hidden unless `exclude_delisted=False` is passed."""
    everything = etfs.select(exclude_delisted=False)
    listed = etfs.select()
    assert everything["delisted"].any()
    assert not listed["delisted"].any()
    assert len(listed) == (~everything["delisted"]).sum()
    assert set(etfs.show_options(selection="exchange")) <= set(
        etfs.show_options(selection="exchange", exclude_delisted=False)
    )
