"""Markets Helpers"""

__docformat__ = "google"

import glob

import pandas as pd

from scripts.listings.helpers import write_csv


def write(frame: pd.DataFrame, path: str, sort: bool) -> None:
    """
    Write a file, sorted by symbol when it was sorted before.

    Args:
        frame (pd.DataFrame): The rows, indexed by symbol.
        path (str): The CSV file.
        sort (bool): Whether to sort by symbol.
    """
    frame = frame.sort_index() if sort else frame
    frame.index.name = "symbol"
    write_csv(frame, path)


def get_other_symbols(database: str, own: str) -> set[str]:
    """
    The symbols of every asset class except one, so no symbol lands in two classes.

    Args:
        database (str): The database folder.
        own (str): The file of the asset class itself.

    Returns:
        set[str]: The symbols.
    """
    symbols: set[str] = set()
    for path in glob.glob(f"{database}/*/*.csv") + glob.glob(f"{database}/*.csv"):
        if not path.endswith(f"/{own}.csv"):
            symbols |= set(
                pd.read_csv(path, usecols=[0], dtype=str, keep_default_na=False).iloc[
                    :, 0
                ]
            )
    return symbols
