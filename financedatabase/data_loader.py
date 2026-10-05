"""Data Loader Module"""

__docformat__ = "google"

import bz2
import hashlib
import json
import os
import sys
import tempfile
import time
from pathlib import Path

import numpy as np
import pandas as pd
import polars as pl
import requests

# The database files are published as bz2-compressed CSVs (compression/<asset>.bz2). They are
# downloaded once, stored as Parquet in a local cache and scanned lazily with Polars, so a query
# only reads what it needs and nothing is downloaded again until the published file changes.
# The cache lives in $FINANCEDATABASE_CACHE_DIR or the platform's user cache directory.

# How often a cached remote file is checked for a newer version (a conditional ETag request).
REFRESH_SECONDS = 24 * 60 * 60

# Seconds before a download is given up; the cached copy is used when there is one.
TIMEOUT = 60

# Some networks block requests without a browser User-Agent.
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/58.0.3029.110 Safari/537.3"
}


def cache_dir() -> Path:
    """
    Get the directory holding the cached database files, creating it when needed.

    The FINANCEDATABASE_CACHE_DIR environment variable overrides the platform default:
    ~/.cache/financedatabase on Linux, ~/Library/Caches/financedatabase on macOS and
    %LOCALAPPDATA%\\financedatabase\\Cache on Windows.

    Returns:
        Path: The cache directory.
    """
    override = os.environ.get("FINANCEDATABASE_CACHE_DIR")
    if override:
        path = Path(override)
    elif sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local"
        path = Path(base) / "financedatabase" / "Cache"
    elif sys.platform == "darwin":
        path = Path.home() / "Library" / "Caches" / "financedatabase"
    else:
        path = (
            Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache")
            / "financedatabase"
        )
    path.mkdir(parents=True, exist_ok=True)
    return path


def _bz2_csv_to_parquet(content: bytes, target: Path) -> None:
    """
    Decompress a bz2 CSV and store it as Parquet, with all columns as text, atomically.

    Every column is read as a string so values such as the ticker NA or a zipcode keep
    their exact text; empty fields become nulls, matching the pandas reader used before.

    Args:
        content (bytes): The bz2-compressed CSV.
        target (Path): The Parquet file to write.
    """
    frame = pl.read_csv(bz2.decompress(content), infer_schema=False)
    handle, temporary = tempfile.mkstemp(dir=target.parent, suffix=".parquet.tmp")
    os.close(handle)
    try:
        frame.write_parquet(temporary)
        os.replace(temporary, target)
    finally:
        if os.path.exists(temporary):
            os.remove(temporary)


def _cache_name(source: str) -> str:
    """
    Get a short, stable file name for a source.

    Args:
        source (str): A URL or a description of a local file.

    Returns:
        str: The first 16 characters of the SHA-256 hash of the source.
    """
    return hashlib.sha256(source.encode()).hexdigest()[:16]


def _local(path: Path) -> Path:
    """
    Get the Parquet cache of a local bz2 file, rebuilt when the file changes.

    Args:
        path (Path): The local bz2 file.

    Returns:
        Path: The cached Parquet file.
    """
    stat = path.stat()
    key = _cache_name(f"{path.resolve()}|{stat.st_size}|{stat.st_mtime_ns}")
    target = cache_dir() / f"local-{path.stem}-{key}.parquet"
    if not target.exists():
        for stale in cache_dir().glob(f"local-{path.stem}-*.parquet"):
            stale.unlink(missing_ok=True)
        _bz2_csv_to_parquet(path.read_bytes(), target)
    return target


def _remote(url: str) -> Path:
    """
    Get the Parquet cache of a remote bz2 file, checked for changes at most once a day.

    If the server can't be reached, the cached copy is used.

    Args:
        url (str): The URL of the bz2 file.

    Returns:
        Path: The cached Parquet file.

    Raises:
        requests.exceptions.RequestException: If the download fails and there is no cache.
    """
    key = _cache_name(url)
    target = cache_dir() / f"remote-{key}.parquet"
    meta_path = cache_dir() / f"remote-{key}.json"
    meta = json.loads(meta_path.read_text()) if meta_path.exists() else {}
    if target.exists() and time.time() - meta.get("checked", 0) < REFRESH_SECONDS:
        return target

    headers = dict(HEADERS)
    if target.exists() and meta.get("etag"):
        headers["If-None-Match"] = meta["etag"]
    try:
        response = requests.get(url, headers=headers, timeout=TIMEOUT)
        if response.status_code == 304 and target.exists():
            meta["checked"] = time.time()
        else:
            response.raise_for_status()
            _bz2_csv_to_parquet(response.content, target)
            meta = {
                "url": url,
                "etag": response.headers.get("ETag"),
                "checked": time.time(),
            }
        meta_path.write_text(json.dumps(meta))
    except requests.exceptions.RequestException:
        # Offline or GitHub unavailable: keep using the cached copy.
        if target.exists():
            return target
        raise
    return target


def load_lazy(file_name: str, base_url: str, local_dir: Path | None) -> pl.LazyFrame:
    """
    Get a lazy scan of one database file from the local cache, downloading it if needed.

    Args:
        file_name (str): The compressed file, e.g. "equities.bz2".
        base_url (str): The URL the file is published under.
        local_dir (Path | None): The local directory holding the file, or None to download.

    Returns:
        pl.LazyFrame: A lazy scan of the cached Parquet file.
    """
    source = (
        _local(local_dir / file_name) if local_dir else _remote(base_url + file_name)
    )
    return pl.scan_parquet(source)


def string_dtype() -> object:
    """
    Get the dtype pandas.read_csv gives text columns.

    Returns:
        object: The str dtype on pandas 3, object before.
    """
    return pd.Series(["text"]).dtype


def to_pandas(frame: pl.DataFrame) -> pd.DataFrame:
    """
    Convert to the pandas frame the package always returned, without needing pyarrow.

    The first column (symbol) becomes the index, text columns get the dtype pandas' CSV
    reader would give them with missing values as NaN, and delisted is boolean.

    Args:
        frame (pl.DataFrame): The collected rows, all columns as text.

    Returns:
        pd.DataFrame: The rows indexed by symbol.
    """
    text = string_dtype()
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


def from_pandas(frame: pd.DataFrame) -> pl.DataFrame:
    """
    Convert a pandas frame back to text columns, the inverse of to_pandas.

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
