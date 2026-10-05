"""DataFrame Model"""

__docformat__ = "google"

import numpy as np
import pandas as pd
import polars as pl


def get_string_dtype() -> object:
    """
    Get the dtype pandas.read_csv gives text columns.

    Returns:
        object: The str dtype on pandas 3, object before.
    """
    return pd.Series(["text"]).dtype


def convert_to_pandas(frame: pl.DataFrame) -> pd.DataFrame:
    """
    Convert a text-only Polars frame to the pandas frame the package returns.

    The first column becomes the index, text columns get the dtype pandas' CSV reader
    would give them with missing values as NaN, and delisted becomes boolean. No
    pyarrow is needed.

    Args:
        frame (pl.DataFrame): The collected rows, all columns as text.

    Returns:
        pd.DataFrame: The rows indexed by symbol.
    """
    text = get_string_dtype()
    columns = {}
    for name in frame.columns[1:]:
        values = frame.get_column(name).to_list()
        if name == "delisted":
            columns[name] = pd.Series([v == "True" for v in values], dtype=bool)
        else:
            columns[name] = pd.Series(
                [np.nan if v is None else v for v in values], dtype=text
            )
    index = pd.Index(frame.get_column(frame.columns[0]).to_list(), dtype=text)
    result = pd.DataFrame(columns, index=range(frame.height))
    result.index = index
    result.index.name = frame.columns[0]
    return result


def convert_from_pandas(frame: pd.DataFrame) -> pl.DataFrame:
    """
    Convert a pandas frame to a text-only Polars frame, the inverse of convert_to_pandas.

    Args:
        frame (pd.DataFrame): The rows indexed by symbol.

    Returns:
        pl.DataFrame: Every column as text, with the index as the first column.
    """
    data = {
        frame.index.name
        or "symbol": [None if pd.isna(v) else str(v) for v in frame.index]
    }
    for name in frame.columns:
        data[str(name)] = [None if pd.isna(v) else str(v) for v in frame[name].tolist()]
    return pl.DataFrame(data, schema={name: pl.String for name in data})
