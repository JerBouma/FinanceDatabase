"""Helpers Module"""

__docformat__ = "google"

from typing import Any

import pandas as pd
import polars as pl


def convert_to_list(value: str | list | Any) -> list:
    """
    Convert a single value or a collection of values to a list.

    Args:
        value (str | list | Any): A string or an iterable of strings.

    Returns:
        list: The values as a list.
    """
    return [value] if isinstance(value, str) else list(value)


def check_list_like(value: Any) -> bool:
    """
    Check whether a value is a list, pandas Index or Polars Series.

    Args:
        value (Any): The value to check.

    Returns:
        bool: Whether the value holds several items.
    """
    return isinstance(value, list | pd.Index | pl.Series)
