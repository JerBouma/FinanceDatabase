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
    Convert collected rows to the pandas frame the package returns.

    The first column becomes the index, text columns get the dtype pandas' CSV reader
    would give them with missing values as NaN; the Boolean delisted and Float64 empty
    columns keep their type. No pyarrow is needed.

    Args:
        frame (pl.DataFrame): The collected rows, typed as the dataset stores them.

    Returns:
        pd.DataFrame: The rows indexed by symbol.
    """
    text = get_string_dtype()
    columns = {}
    for name in frame.columns[1:]:
        series = frame.get_column(name)
        if series.dtype == pl.String:
            columns[name] = pd.Series(convert_to_object_array(series), dtype=text)
        elif series.dtype == pl.Boolean:
            columns[name] = series.fill_null(False).to_numpy()
        else:
            columns[name] = series.to_numpy()
    index = pd.Index(convert_to_object_array(frame.get_column(frame.columns[0])))
    result = pd.DataFrame(columns, index=range(frame.height))
    result.index = index.astype(text)
    result.index.name = frame.columns[0]
    return result


def convert_to_object_array(series: pl.Series) -> np.ndarray:
    """
    Convert a text column to a numpy object array with missing values as NaN.

    Args:
        series (pl.Series): The text column.

    Returns:
        np.ndarray: The values, NaN where the column is null.
    """
    values = series.to_numpy().astype(object, copy=False)
    if series.null_count():
        values[series.is_null().to_numpy()] = np.nan
    return values


def convert_from_pandas(frame: pd.DataFrame) -> pl.DataFrame:
    """
    Convert a pandas frame to Polars, the inverse of convert_to_pandas.

    Args:
        frame (pd.DataFrame): The rows indexed by symbol.

    Returns:
        pl.DataFrame: Text columns and a Boolean delisted, the index as the first column.
    """
    data = {frame.index.name or "symbol": convert_to_text_array(frame.index)}
    schema = {name: pl.String for name in data}
    for name in frame.columns:
        if name == "delisted":
            data[name] = frame[name].isin([True, "True"]).tolist()
            schema[name] = pl.Boolean
        elif pd.api.types.is_float_dtype(frame[name]) and frame[name].isna().all():
            data[str(name)] = frame[name].tolist()
            schema[str(name)] = pl.Float64
        else:
            data[str(name)] = convert_to_text_array(frame[name])
            schema[str(name)] = pl.String
    return pl.DataFrame(data, schema=schema)


def convert_to_text_array(values: pd.Index | pd.Series) -> list[str | None]:
    """
    Convert values to text, as str() does, with missing values as None.

    Args:
        values (pd.Index | pd.Series): The values.

    Returns:
        list[str | None]: The text values, None where a value is missing.
    """
    array = values.to_numpy(dtype=object)
    missing = pd.isna(array)
    text = array.astype(str).astype(object)
    text[missing] = None
    return text.tolist()
