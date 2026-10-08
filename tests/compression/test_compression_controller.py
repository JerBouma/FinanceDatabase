"""Compression Controller Tests"""

import bz2
import gzip
import io
from pathlib import Path

import pandas as pd
import polars as pl
import pytest

from scripts.compression import compression_controller

EQUITIES = {
    "AMS.csv": "symbol,name,summary,sector,website,isin,delisted\n"
    "ASML.AS,ASML Holding,Chips,Information Technology,,NL0010273215,False\n"
    'OLD.AS,Old Co,"Line one, with comma",Industrials,,,True\n',
    "NMS.csv": "symbol,name,summary,sector,website,isin,delisted\n"
    "NA,Nano Labs,,Information Technology,,,False\n"
    "AAPL,Apple Inc.,Phones,Information Technology,,US0378331005,False\n",
}


@pytest.fixture
def database(tmp_path: Path) -> Path:
    root = tmp_path / "database"
    (root / "equities").mkdir(parents=True)
    for name, text in EQUITIES.items():
        (root / "equities" / name).write_text(text)
    for asset_class in ["etfs", "funds"]:
        (root / asset_class).mkdir()
        (root / asset_class / "AMS.csv").write_text(
            "symbol,name,summary,category_group,category,family,exchange,delisted\n"
            "IWDA.AS,iShares World,World,Equities,Developed Markets,BlackRock,AMS,False\n"
        )
    for name in ["cryptos", "currencies", "indices", "moneymarkets"]:
        (root / f"{name}.csv").write_text(
            "symbol,name,currency\nX,Name,USD\nN/A,Other,EUR\n"
        )
    return root


def write_with_pandas(database: Path, asset_class: str) -> bytes:
    """The CSV the pandas workflow wrote before, for comparison."""
    files = sorted((database / asset_class).glob("*.csv")) or [
        database / f"{asset_class}.csv"
    ]
    frame = pd.concat(
        [pd.read_csv(f, dtype=str, keep_default_na=False) for f in files],
        ignore_index=True,
    )
    return (
        frame.sort_values(frame.columns[0])
        .reset_index(drop=True)
        .to_csv(index=False)
        .encode()
    )


def test_compressed_csv_is_what_pandas_wrote(database: Path, tmp_path: Path) -> None:
    """Test that the bz2 CSV is byte for byte the file older versions read."""
    target = tmp_path / "compression"
    target.mkdir()
    compression_controller.update_datasets(str(database), str(target))
    for asset_class in [
        "equities",
        "etfs",
        "funds",
        "cryptos",
        "currencies",
        "indices",
        "moneymarkets",
    ]:
        written = bz2.decompress((target / f"{asset_class}.bz2").read_bytes())
        assert written == write_with_pandas(database, asset_class)


def test_typed_parquet_needs_no_conversion(database: Path, tmp_path: Path) -> None:
    """Test that the Parquet file holds the final types and the NA ticker."""
    target = tmp_path / "compression"
    target.mkdir()
    compression_controller.update_datasets(str(database), str(target))
    frame = pl.read_parquet(target / "equities.parquet")
    assert frame.get_column("symbol").to_list() == ["AAPL", "ASML.AS", "NA", "OLD.AS"]
    assert frame.schema["delisted"] == pl.Boolean
    assert frame.get_column("delisted").to_list() == [False, False, False, True]
    assert frame.schema["website"] == pl.Float64
    assert frame.schema["isin"] == pl.String


def test_categories_read_as_before(database: Path, tmp_path: Path) -> None:
    """Test that older versions read the same options from the gzip file."""
    target = tmp_path / "compression"
    target.mkdir()
    compression_controller.update_categories(str(database), str(target))
    with gzip.open(target / "categories" / "equities_categories.gzip") as handle:
        old = pd.read_csv(io.BytesIO(handle.read()), index_col=0, low_memory=False)
    options = {index: list(old.loc[index].dropna()) for index in old.index}
    assert options == {
        "sector": ["Industrials", "Information Technology"],
        "isin": ["NL0010273215", "US0378331005"],
    }
    lists = pl.read_parquet(target / "categories" / "equities_categories.parquet")
    assert (
        dict(
            zip(
                lists.get_column("category").to_list(),
                lists.get_column("values").to_list(),
            )
        )
        == options
    )


def test_pandas_missing_strings_stay_out_of_categories(
    database: Path, tmp_path: Path
) -> None:
    """Test that values pandas reads as missing are left out, as before."""
    target = tmp_path / "compression"
    target.mkdir()
    compression_controller.update_categories(str(database), str(target))
    lists = pl.read_parquet(target / "categories" / "cryptos_categories.parquet")
    assert lists.filter(pl.col("category") == "currency").get_column(
        "values"
    ).item().to_list() == ["EUR", "USD"]
