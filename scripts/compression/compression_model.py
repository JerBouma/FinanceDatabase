"""Compression Model"""

__docformat__ = "google"

import bz2
import glob
import gzip
import io
import os

import polars as pl

ASSET_CLASSES = [
    "cryptos",
    "currencies",
    "equities",
    "etfs",
    "funds",
    "indices",
    "moneymarkets",
]
CATEGORY_EXCLUDED = {
    "cryptos": ["name", "summary"],
    "currencies": ["name"],
    "equities": ["name", "summary", "website", "delisted"],
    "etfs": ["name", "summary", "delisted"],
    "funds": ["name", "summary", "manager_name", "manager_bio"],
    "indices": ["name"],
    "moneymarkets": ["name"],
}
# The strings pandas.read_csv reads as missing by default; the category files have
# always been built with them, so older package versions expect them left out.
PANDAS_MISSING = [
    "",
    "#N/A",
    "#N/A N/A",
    "#NA",
    "-1.#IND",
    "-1.#QNAN",
    "-NaN",
    "-nan",
    "1.#IND",
    "1.#QNAN",
    "<NA>",
    "N/A",
    "NA",
    "NULL",
    "NaN",
    "None",
    "n/a",
    "nan",
    "null",
]


def get_source_files(database: str, asset_class: str) -> list[str]:
    """
    Get the CSV files of an asset class, one per exchange or a single file.

    Args:
        database (str): The database directory.
        asset_class (str): The asset class.

    Returns:
        list[str]: The CSV files, sorted.
    """
    folder = os.path.join(database, asset_class)
    if os.path.isdir(folder):
        return sorted(glob.glob(os.path.join(folder, "*.csv")))
    return [os.path.join(database, f"{asset_class}.csv")]


def scan_asset_class(database: str, asset_class: str) -> pl.LazyFrame:
    """
    Scan every CSV of an asset class as text, sorted by symbol.

    Args:
        database (str): The database directory.
        asset_class (str): The asset class.

    Returns:
        pl.LazyFrame: The rows of the asset class, every column as text.
    """
    lazy = pl.concat(
        [
            pl.scan_csv(path, infer_schema=False)
            for path in get_source_files(database, asset_class)
        ],
        how="diagonal",
    )
    return lazy.sort(lazy.collect_schema().names()[0], maintain_order=True)


def write_compressed_csv(frame: pl.DataFrame, target: str) -> None:
    """
    Write rows as a bz2-compressed CSV, byte for byte as pandas.to_csv(compression="bz2").

    Args:
        frame (pl.DataFrame): The rows.
        target (str): The file to write.
    """
    with open(target, "wb") as handle:
        handle.write(bz2.compress(frame.write_csv().encode(), 9))


def get_typed_frame(frame: pl.DataFrame) -> pl.DataFrame:
    """
    Give rows the types the package returns, so readers need no conversion.

    The delisted flag becomes a Boolean and a column that is empty in every row becomes
    Float64, as pandas reads an empty CSV column; every other column stays text.

    Args:
        frame (pl.DataFrame): The rows, every column as text.

    Returns:
        pl.DataFrame: The typed rows.
    """
    empty = [
        name
        for name in frame.columns[1:]
        if frame.get_column(name).null_count() == frame.height
    ]
    return frame.with_columns(
        [pl.col("delisted").eq("True").fill_null(False)]
        if "delisted" in frame.columns
        else []
    ).with_columns(
        [pl.col(name).cast(pl.Float64) for name in empty if name != "delisted"]
    )


def write_typed_parquet(frame: pl.DataFrame, target: str) -> None:
    """
    Write typed rows as Parquet.

    Args:
        frame (pl.DataFrame): The typed rows.
        target (str): The file to write.
    """
    frame.write_parquet(target, compression="zstd", statistics=True)


def get_categories(lazy: pl.LazyFrame, asset_class: str) -> pl.DataFrame:
    """
    Get the sorted unique values of every category column, one row per column.

    Args:
        lazy (pl.LazyFrame): The rows of the asset class.
        asset_class (str): The asset class.

    Returns:
        pl.DataFrame: A column "index" with the column names and the values in 0..n.
    """
    names = lazy.collect_schema().names()[1:]
    columns = [name for name in names if name not in CATEGORY_EXCLUDED[asset_class]]
    unique = lazy.select(
        [
            pl.col(name)
            .filter(~pl.col(name).is_in(PANDAS_MISSING))
            .drop_nulls()
            .unique()
            .sort()
            .implode()
            for name in columns
        ]
    ).collect()
    values = {name: unique.get_column(name).item().to_list() for name in columns}
    width = max((len(v) for v in values.values()), default=0)
    rows = [
        [name] + values[name] + [None] * (width - len(values[name])) for name in columns
    ]
    schema = {"index": pl.String} | {str(i): pl.String for i in range(width)}
    return pl.DataFrame(rows, schema=schema, orient="row")


def get_category_lists(frame: pl.DataFrame) -> pl.DataFrame:
    """
    Turn padded category rows into one list of values per category.

    Args:
        frame (pl.DataFrame): The category rows from get_categories.

    Returns:
        pl.DataFrame: The columns "category" (text) and "values" (list of text).
    """
    values = (
        frame.select(pl.concat_list(pl.exclude("index")).list.drop_nulls())
        if frame.width > 1
        else None
    )
    return pl.DataFrame(
        {
            "category": frame.get_column("index"),
            "values": (
                values.to_series()
                if values is not None
                else [[] for _ in range(frame.height)]
            ),
        },
        schema={"category": pl.String, "values": pl.List(pl.String)},
    )


def write_compressed_categories(frame: pl.DataFrame, target: str) -> None:
    """
    Write category rows as a gzip-compressed CSV in the layout older versions read.

    The gzip member is named after the file and its mtime fixed at 0, so unchanged
    content gives an identical file.

    Args:
        frame (pl.DataFrame): The category rows.
        target (str): The file to write.
    """
    buffer = io.BytesIO()
    name = os.path.basename(target)
    with gzip.GzipFile(filename=name, mode="wb", fileobj=buffer, mtime=0) as handle:
        handle.write(frame.write_csv().encode())
    with open(target, "wb") as handle:
        handle.write(buffer.getvalue())
