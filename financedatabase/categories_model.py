"""Categories Model"""

__docformat__ = "google"

from io import BytesIO

import pandas as pd
import requests

from financedatabase.cache_model import HEADERS, TIMEOUT


def get_categories(location: str, use_local_location: bool = False) -> pd.DataFrame:
    """
    Get the categories file of an asset class, one row per category.

    Args:
        location (str): The path or URL of the gzip-compressed categories file.
        use_local_location (bool, optional): Whether the location is a local path.
            Defaults to False.

    Returns:
        pd.DataFrame: The categories, indexed by category name.

    Raises:
        requests.exceptions.RequestException: If the file can't be downloaded.
    """
    if use_local_location:
        return pd.read_csv(location, compression="gzip", index_col=0, low_memory=False)

    response = requests.get(location, headers=HEADERS, timeout=TIMEOUT)
    response.raise_for_status()

    return pd.read_csv(
        BytesIO(response.content), compression="gzip", index_col=0, low_memory=False
    )
