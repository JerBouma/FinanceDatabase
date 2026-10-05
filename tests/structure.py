"""Structural checks for select(), search() and show_options().

These replace recorded snapshots of the first rows. Every call is compared with an independent
pandas filter of the same data, so the tests verify behaviour (the right rows, columns and
options) but keep passing when the weekly database update adds tickers or refreshes values.
"""

from __future__ import annotations

import inspect
import re
from typing import Any

import pandas as pd

CONTROL_ARGUMENTS = {"only_primary_listing", "exclude_delisted", "selection"}


def _rows(data: pd.DataFrame, mask: Any) -> pd.DataFrame:
    """Boolean row selection that stays row-wise for an empty mask (data[mask] would select columns)."""
    return data.loc[pd.Series(mask, index=data.index, dtype=bool)]


def _as_list(value: Any) -> list[str]:
    return [value] if isinstance(value, str) else list(value)


def _excludes_delisted_by_default(obj: Any, method: str) -> bool:
    parameters = inspect.signature(getattr(obj, method)).parameters
    return (
        "exclude_delisted" in parameters
        and parameters["exclude_delisted"].default is True
    )


def expected_selection(obj: Any, method: str = "select", **kwargs: Any) -> pd.DataFrame:
    """What select()/show_options() should return, computed directly with pandas."""
    data = obj.data
    exclude = kwargs.get("exclude_delisted", _excludes_delisted_by_default(obj, method))
    if exclude and "delisted" in data.columns:
        data = data[~data["delisted"].astype(bool)]
    for field, value in kwargs.items():
        if field in CONTROL_ARGUMENTS or value is None:
            continue
        wanted = {v.lower() for v in _as_list(value)}
        data = _rows(
            data,
            data[field].map(lambda x, w=wanted: isinstance(x, str) and x.lower() in w),
        )
    if kwargs.get("only_primary_listing"):
        primary = data[~data.index.str.contains(".", regex=False, na=False)]
        data = primary if not primary.empty else data
    return data


def expected_search(obj: Any, **kwargs: Any) -> pd.DataFrame:
    """What search() should return, computed directly with pandas and re."""
    data = obj.data
    case_sensitive = kwargs.pop("case_sensitive", False) in (True, "True")
    if (
        kwargs.pop("exclude_delisted", True) in (True, "True")
        and "delisted" in data.columns
    ):
        data = data[~data["delisted"].astype(bool)]
    flags = 0 if case_sensitive else re.IGNORECASE
    for key, value in kwargs.items():
        if key == "only_primary_listing":
            if value is True:
                data = data[~data.index.str.contains(".", regex=False, na=False)]
        elif key == "index":
            data = _rows(data, [bool(re.search(value, str(s))) for s in data.index])
        elif key in data.columns:
            if isinstance(value, list):
                hit = lambda x, vals=value: isinstance(x, str) and any(  # noqa: E731
                    v.lower() in x.lower() for v in vals
                )
            else:
                hit = lambda x, v=value: isinstance(x, str) and bool(  # noqa: E731
                    re.search(v, x, flags)
                )
            data = _rows(data, data[key].map(hit))
    return data


def _check_frame(obj: Any, result: pd.DataFrame, expected: pd.DataFrame) -> None:
    assert list(result.columns) == list(obj.data.columns), "columns changed"
    assert result.index.is_unique, "duplicate symbols in the result"
    assert not result.index.hasnans and (result.index != "").all(), "empty symbol"
    pd.testing.assert_frame_equal(pd.DataFrame(result), expected, check_freq=False)


def check_select(obj: Any, nonempty: bool = False, **kwargs: Any) -> pd.DataFrame:
    """select(**kwargs) returns exactly the rows matching every filter."""
    result = obj.select(**kwargs)
    expected = expected_selection(obj, **kwargs)
    _check_frame(obj, result, expected)
    if nonempty:
        assert len(result) > 0, f"select({kwargs}) unexpectedly returned no rows"
    excludes = kwargs.get(
        "exclude_delisted", _excludes_delisted_by_default(obj, "select")
    )
    if excludes and "delisted" in result:
        assert not result["delisted"].astype(bool).any(), "delisted rows returned"
    for field, value in kwargs.items():
        if field not in CONTROL_ARGUMENTS and value is not None and len(result):
            wanted = {v.lower() for v in _as_list(value)}
            assert (
                result[field].str.lower().isin(wanted).all()
            ), f"{field} filter not applied"
    return result


def check_search(obj: Any, nonempty: bool = False, **kwargs: Any) -> pd.DataFrame:
    """search(**kwargs) returns exactly the rows matching every query."""
    result = obj.search(**kwargs)
    _check_frame(obj, result, expected_search(obj, **dict(kwargs)))
    if nonempty:
        assert len(result) > 0, f"search({kwargs}) unexpectedly returned no rows"
    return result


def _option_values(values: Any) -> list:
    values = list(values)
    assert values == sorted(values, key=str), "options are not sorted"
    assert len(values) == len(set(values)), "options contain duplicates"
    return values


def check_show_options(obj: Any, nonempty: bool = False, **kwargs: Any) -> Any:
    """show_options(**kwargs) lists the sorted unique values of the filtered selection."""
    options = obj.show_options(**kwargs)
    selection = kwargs.get("selection")
    filters = {k: v for k, v in kwargs.items() if k != "selection"}
    data = expected_selection(obj, method="show_options", **filters)
    parameters = inspect.signature(obj.show_options).parameters
    fields = [p for p in parameters if p not in CONTROL_ARGUMENTS]
    if selection is None:
        assert isinstance(options, dict)
        assert set(options) == set(fields), "show_options() keys changed"
        for field, values in options.items():
            expected = sorted(data[field].dropna().unique(), key=str)
            assert _option_values(values) == expected, f"options for {field} differ"
        if nonempty:
            assert any(len(v) for v in options.values()), "no options at all"
    else:
        expected = sorted(data[selection].dropna().unique(), key=str)
        assert _option_values(options) == expected, f"options for {selection} differ"
        if nonempty:
            assert len(options) > 0, f"show_options({kwargs}) is empty"
    return options
