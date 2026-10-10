"""Query Model"""

__docformat__ = "google"

import re

import numpy as np
import pandas as pd
import polars as pl

from financedatabase.helpers import check_list_like
from financedatabase.utilities import logger_model
from financedatabase.utilities.dataframe_model import get_string_dtype

logger = logger_model.get_logger()


def exclude_delisted_rows(lazy: pl.LazyFrame, exclude_delisted: bool) -> pl.LazyFrame:
    """
    Exclude the rows marked as delisted when requested and the column exists.

    Args:
        lazy (pl.LazyFrame): The dataset.
        exclude_delisted (bool): Whether to exclude delisted rows.

    Returns:
        pl.LazyFrame: The dataset without delisted rows when requested.
    """
    if exclude_delisted and "delisted" in lazy.collect_schema():
        return lazy.filter(~pl.col("delisted").fill_null(False))
    return lazy


def get_lowercase_options(lazy: pl.LazyFrame, column: str) -> set[str]:
    """
    Get the unique lowercase values of a column.

    Args:
        lazy (pl.LazyFrame): The dataset.
        column (str): The column name.

    Returns:
        set[str]: The unique lowercase values, without missing values.
    """
    values = (
        lazy.select(pl.col(column).drop_nulls().str.to_lowercase().unique())
        .collect()
        .get_column(column)
    )
    return set(values.to_list())


def validate_filter_values(
    values: list[str], options: set[str], label: str, plural: str
) -> None:
    """
    Validate that every filter value exists in the database, ignoring case.

    Args:
        values (list[str]): The requested values.
        options (set[str]): The lowercase values available in the database.
        label (str): The name of the filter in the error message, e.g. "sector".
        plural (str): The plural of the label, e.g. "sectors".

    Raises:
        ValueError: If a value is not available in the database.
    """
    for value in values:
        if value.lower() not in options:
            raise ValueError(
                f"The {label} '{value}' is not available in the database. "
                f"Please check the available {plural} using the 'show_options' method."
            )


def filter_rows(lazy: pl.LazyFrame, column: str, values: list[str]) -> pl.LazyFrame:
    """
    Filter the rows whose value in a column equals one of the values, ignoring case.

    Args:
        lazy (pl.LazyFrame): The dataset.
        column (str): The column name.
        values (list[str]): The values to keep.

    Returns:
        pl.LazyFrame: The matching rows.
    """
    values_lower = [value.lower() for value in values]
    return lazy.filter(pl.col(column).str.to_lowercase().is_in(values_lower))


def filter_primary_listings(
    lazy: pl.LazyFrame, symbol_column: str, primary_symbols: pl.Series | None = None
) -> pl.LazyFrame:
    """
    Filter the primary listings: the given symbols, or without them the symbols
    without an exchange suffix.

    Args:
        lazy (pl.LazyFrame): The dataset.
        symbol_column (str): The name of the symbol column.
        primary_symbols (pl.Series | None, optional): The symbols of the primary
            listings, see listings_model. Defaults to None.

    Returns:
        pl.LazyFrame: The primary listings.
    """
    if primary_symbols is not None:
        return lazy.filter(pl.col(symbol_column).is_in(primary_symbols.implode()))
    return lazy.filter(~pl.col(symbol_column).str.contains(".", literal=True))


def count_rows(lazy: pl.LazyFrame) -> int:
    """
    Count the rows of a lazy dataset.

    Args:
        lazy (pl.LazyFrame): The dataset.

    Returns:
        int: The number of rows.
    """
    return lazy.select(pl.len()).collect().item()


def match_pattern(column: pl.Expr, pattern: str, case_sensitive: bool) -> pl.Expr:
    """
    Match a regular expression with Python's semantics, as pandas' str.contains does.

    Polars' regex engine is used when it supports the pattern; patterns it doesn't
    support (e.g. look-around or backreferences) fall back to Python's re module.

    Args:
        column (pl.Expr): The column to search.
        pattern (str): The regular expression.
        case_sensitive (bool): Whether the match is case-sensitive.

    Returns:
        pl.Expr: A boolean expression that is False for missing values.

    Raises:
        re.error: If the pattern is not a valid regular expression.
    """
    try:
        re.compile(pattern)
    except re.error as error:
        raise re.error(f"Invalid search pattern {pattern!r}: {error}") from error
    flagged = pattern if case_sensitive else f"(?i){pattern}"
    try:
        pl.select(pl.lit("").str.contains(flagged))
        return column.str.contains(flagged).fill_null(False)
    except pl.exceptions.ComputeError:
        compiled = re.compile(pattern, 0 if case_sensitive else re.IGNORECASE)
        return column.map_elements(
            lambda value: value is not None and bool(compiled.search(value)),
            return_dtype=pl.Boolean,
            skip_nulls=False,
        ).fill_null(False)


def search_rows(
    lazy: pl.LazyFrame,
    queries: dict,
    columns: list[str],
    case_sensitive: bool = False,
    primary_symbols: pl.Series | None = None,
) -> pl.LazyFrame:
    """
    Search the rows matching every query.

    A query is a regular expression matched anywhere in the value; a list of queries
    keeps rows that contain any of them. The keys only_primary_listing and index
    filter on the symbol column, unknown columns are logged and ignored.

    Args:
        lazy (pl.LazyFrame): The dataset.
        queries (dict): Column names mapped to a query or a list of queries.
        columns (list[str]): The columns of the dataset, the symbol column first.
        case_sensitive (bool, optional): Whether the search is case-sensitive.
            Defaults to False.
        primary_symbols (pl.Series | None, optional): The symbols of the primary
            listings. Defaults to None, the symbols without an exchange suffix.

    Returns:
        pl.LazyFrame: The matching rows.
    """
    symbol_column = columns[0]

    for key, value in queries.items():
        if key == "only_primary_listing":
            if value is True:
                lazy = filter_primary_listings(lazy, symbol_column, primary_symbols)
        elif key == "index":
            if check_list_like(value):
                lazy = lazy.filter(pl.col(symbol_column).is_in(list(value)))
            else:
                lazy = lazy.filter(match_pattern(pl.col(symbol_column), value, True))
        elif key not in columns[1:]:
            logger.warning("%s is not a valid column.", key)
        elif isinstance(value, list):
            if case_sensitive:
                lazy = lazy.filter(pl.col(key).is_in(value))
            else:
                lowered = pl.col(key).str.to_lowercase()
                hits = [lowered.str.contains(v.lower(), literal=True) for v in value]
                lazy = lazy.filter(pl.any_horizontal(hits).fill_null(False))
        else:
            lazy = lazy.filter(match_pattern(pl.col(key), value, case_sensitive))

    return lazy


def get_unique_values(lazy: pl.LazyFrame, columns: list[str]) -> dict[str, pl.Series]:
    """
    Get the unique values of columns in one pass, without collecting their rows.

    Args:
        lazy (pl.LazyFrame): The dataset.
        columns (list[str]): The column names.

    Returns:
        dict[str, pl.Series]: The unique values of each column, without missing values.
    """
    row = lazy.select(
        [pl.col(column).drop_nulls().unique().implode() for column in columns]
    ).collect()
    return {column: row.get_column(column).explode() for column in columns}


def get_sorted_options(
    values: pl.Series, as_pandas: bool = True
) -> np.ndarray | pl.Series:
    """
    Sort the unique values of a column.

    Args:
        values (pl.Series): The unique values, without missing values.
        as_pandas (bool, optional): Whether to return a numpy array (True) or a Polars
            Series (False). Defaults to True.

    Returns:
        np.ndarray | pl.Series: The sorted unique values.
    """
    if not as_pandas:
        return values.sort()
    return pd.Series(values.to_list(), dtype=get_string_dtype()).sort_values().unique()
