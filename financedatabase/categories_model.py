"""Categories Model"""

__docformat__ = "google"

from io import BytesIO
from pathlib import Path

import pandas as pd
import polars as pl
import requests

from financedatabase.cache_model import HEADERS, TIMEOUT


def read_source(location: str, use_local_location: bool) -> bytes:
    """
    Read a file from a local path or a URL.

    Args:
        location (str): The path or URL.
        use_local_location (bool): Whether the location is a local path.

    Returns:
        bytes: The file.

    Raises:
        FileNotFoundError: If a local file doesn't exist.
        requests.exceptions.RequestException: If the file can't be downloaded.
    """
    if use_local_location:
        return Path(location).read_bytes()
    response = requests.get(location, headers=HEADERS, timeout=TIMEOUT)
    response.raise_for_status()
    return response.content


def get_categories(
    location: str, use_local_location: bool = False
) -> dict[str, list[str]]:
    """
    Get the category options of an asset class.

    The Parquet file holds one list of values per category. When it isn't published,
    the gzip CSV older versions read is used instead.

    Args:
        location (str): The path or URL of the categories file, without extension.
        use_local_location (bool, optional): Whether the location is a local path.
            Defaults to False.

    Returns:
        dict[str, list[str]]: Category names mapped to their sorted values.

    Raises:
        requests.exceptions.RequestException: If no categories file can be loaded.
    """
    try:
        frame = pl.read_parquet(
            BytesIO(read_source(location + ".parquet", use_local_location))
        )
        return dict(
            zip(
                frame.get_column("category").to_list(),
                frame.get_column("values").to_list(),
            )
        )
    except (FileNotFoundError, requests.exceptions.HTTPError):
        pass
    content = read_source(location + ".gzip", use_local_location)
    frame = pd.read_csv(BytesIO(content), compression="gzip", index_col=0, dtype=str)
    return {name: frame.loc[name].dropna().tolist() for name in frame.index}
