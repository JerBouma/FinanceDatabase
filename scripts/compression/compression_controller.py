"""Compression Controller"""

__docformat__ = "google"

import argparse
import os

from scripts.compression.compression_model import (
    ASSET_CLASSES,
    get_categories,
    get_category_lists,
    get_typed_frame,
    scan_asset_class,
    write_compressed_categories,
    write_compressed_csv,
    write_typed_parquet,
)


def update_datasets(database: str, compression: str) -> None:
    """
    Write the compressed dataset of every asset class: a bz2 CSV for every version of the
    package and a typed Parquet file for the versions that read it.

    Args:
        database (str): The database directory.
        compression (str): The compression directory.
    """
    for asset_class in ASSET_CLASSES:
        frame = scan_asset_class(database, asset_class).collect()
        write_compressed_csv(frame, os.path.join(compression, f"{asset_class}.bz2"))
        write_typed_parquet(
            get_typed_frame(frame), os.path.join(compression, f"{asset_class}.parquet")
        )
        print(f"{asset_class}: {frame.height:,} rows")


def update_categories(database: str, compression: str) -> None:
    """
    Write the category options of every asset class: a gzip CSV for every version of the
    package and a Parquet file with one list of values per category.

    Args:
        database (str): The database directory.
        compression (str): The compression directory.
    """
    folder = os.path.join(compression, "categories")
    os.makedirs(folder, exist_ok=True)
    for asset_class in ASSET_CLASSES:
        categories = get_categories(
            scan_asset_class(database, asset_class), asset_class
        )
        write_compressed_categories(
            categories, os.path.join(folder, f"{asset_class}_categories.gzip")
        )
        get_category_lists(categories).write_parquet(
            os.path.join(folder, f"{asset_class}_categories.parquet")
        )
        print(f"{asset_class}: {categories.height} categories")


def main() -> None:
    """
    Regenerate the compressed files from the command line.
    """
    parser = argparse.ArgumentParser(
        description="Regenerate compression/ from database/."
    )
    parser.add_argument("--database", default="database")
    parser.add_argument("--compression", default="compression")
    parser.add_argument("--only", choices=["datasets", "categories"], default=None)
    args = parser.parse_args()
    if args.only in (None, "datasets"):
        update_datasets(args.database, args.compression)
    if args.only in (None, "categories"):
        update_categories(args.database, args.compression)
