"""ETFs Test Module"""

from __future__ import annotations

import re
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
    {"family": "ProShares"},
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


def test_search_excludes_delisted_by_default() -> None:
    """search() leaves delisted symbols out unless exclude_delisted=False, like select()."""
    data = etfs.data
    delisted = data.index[data["delisted"].astype(bool)][0]
    query = f"^{re.escape(delisted)}$"
    assert delisted not in etfs.search(index=query).index
    assert delisted not in etfs.search(index=query, exclude_delisted=True).index
    assert delisted in etfs.search(index=query, exclude_delisted=False).index
    assert (
        not etfs.search(name=data.loc[delisted, "name"])["delisted"].astype(bool).any()
    )


def test_delisted_only_values_are_valid_when_delisted_etfs_are_included() -> None:
    """Like equities (#171): a value that only delisted ETFs have is accepted with
    exclude_delisted=False and rejected otherwise."""
    data = etfs.data
    delisted = data[data["delisted"].astype(bool)]
    listed_families = set(data.loc[~data["delisted"].astype(bool), "family"].dropna())
    family = next(
        f for f in delisted["family"].dropna().unique() if f not in listed_families
    )

    result = etfs.select(family=family, exclude_delisted=False)
    assert len(result) > 0 and result["delisted"].all()
    assert (
        etfs.show_options(selection="family", exclude_delisted=False)
        .tolist()
        .count(family)
        == 1
    )
    with pytest.raises(ValueError, match="is not available in the database"):
        etfs.select(family=family)
    with pytest.raises(ValueError, match="is not available in the database"):
        etfs.select(family=family, exclude_delisted=True)
