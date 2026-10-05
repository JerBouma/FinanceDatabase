"""Data loading for the Finance Database: a local cache plus lazy Polars scans.

The database files are published as bz2-compressed CSVs (``compression/<asset>.bz2``). They are
downloaded once, stored as Parquet in a local cache and scanned lazily with Polars, so a query
only reads what it needs and nothing is downloaded again until the published file changes:

- Remote files are checked for changes at most once per ``REFRESH_SECONDS`` (a conditional
  request with the stored ETag); an unchanged file is not downloaded again. If GitHub cannot be
  reached, the cached copy is used.
- Local files (``use_local_location=True``) are re-cached whenever the file changes on disk.

The cache lives in ``$FINANCEDATABASE_CACHE_DIR`` or the platform's user cache directory
(``~/.cache/financedatabase``, ``~/Library/Caches/financedatabase`` or
``%LOCALAPPDATA%\\financedatabase\\Cache``).
"""

from __future__ import annotations

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

REFRESH_SECONDS = 24 * 60 * 60
TIMEOUT = 60
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/58.0.3029.110 Safari/537.3"
}


def cache_dir() -> Path:
    """The directory holding the cached database files."""
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
    """Decompress a bz2 CSV and store it as Parquet (all columns as text, written atomically).

    Every column is read as a string so values such as the ticker ``NA`` or a zipcode keep
    their exact text; empty fields become nulls, matching the pandas reader used before.
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
    return hashlib.sha256(source.encode()).hexdigest()[:16]


def _local(path: Path) -> Path:
    """Parquet cache of a local bz2 file, rebuilt when the file changes."""
    stat = path.stat()
    key = _cache_name(f"{path.resolve()}|{stat.st_size}|{stat.st_mtime_ns}")
    target = cache_dir() / f"local-{path.stem}-{key}.parquet"
    if not target.exists():
        for stale in cache_dir().glob(f"local-{path.stem}-*.parquet"):
            stale.unlink(missing_ok=True)
        _bz2_csv_to_parquet(path.read_bytes(), target)
    return target


def _remote(url: str) -> Path:
    """Parquet cache of a remote bz2 file, checked for changes at most once a day."""
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
        if target.exists():  # offline or GitHub unavailable: keep using the cached copy
            return target
        raise
    return target


def load_lazy(file_name: str, base_url: str, local_dir: Path | None) -> pl.LazyFrame:
    """A lazy scan of one database file, from the local cache (downloading it if needed)."""
    source = (
        _local(local_dir / file_name) if local_dir else _remote(base_url + file_name)
    )
    return pl.scan_parquet(source)


def string_dtype() -> object:
    """The dtype pandas.read_csv gives text columns (``str`` in pandas 3, ``object`` before)."""
    return pd.Series(["text"]).dtype


def to_pandas(frame: pl.DataFrame) -> pd.DataFrame:
    """Convert to the pandas frame the package always returned (no pyarrow needed).

    The first column (``symbol``) becomes the index, text columns get the dtype pandas'
    CSV reader would give them with missing values as NaN, and ``delisted`` is boolean.
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
    """The inverse of ``to_pandas``: every column as text, the index as the first column."""
    data = {
        frame.index.name
        or "symbol": [None if pd.isna(v) else str(v) for v in frame.index]
    }
    for name in frame.columns:
        data[str(name)] = [None if pd.isna(v) else str(v) for v in frame[name].tolist()]
    return pl.DataFrame(data, schema={name: pl.String for name in data})
