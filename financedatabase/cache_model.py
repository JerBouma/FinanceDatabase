"""Cache Model"""

__docformat__ = "google"

import bz2
import hashlib
import json
import os
import sys
import tempfile
import time
from pathlib import Path

import polars as pl
import requests

REFRESH_SECONDS = 24 * 60 * 60
TIMEOUT = 60
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/58.0.3029.110 Safari/537.3"
}


def get_cache_directory() -> Path:
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


def convert_bz2_to_parquet(content: bytes, target: Path) -> None:
    """
    Convert a bz2-compressed CSV to Parquet, with every column as text, atomically.

    Reading every column as text keeps values such as the ticker NA or a zipcode
    exactly as written; empty fields become nulls.

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


def get_cache_name(source: str) -> str:
    """
    Get a short, stable file name for a source.

    Args:
        source (str): A URL or a description of a local file.

    Returns:
        str: The first 16 characters of the SHA-256 hash of the source.
    """
    return hashlib.sha256(source.encode()).hexdigest()[:16]


def get_local_cache(path: Path) -> Path:
    """
    Get the Parquet cache of a local bz2 file, rebuilt when the file changes.

    Args:
        path (Path): The local bz2 file.

    Returns:
        Path: The cached Parquet file.
    """
    stat = path.stat()
    key = get_cache_name(f"{path.resolve()}|{stat.st_size}|{stat.st_mtime_ns}")
    target = get_cache_directory() / f"local-{path.stem}-{key}.parquet"
    if not target.exists():
        for stale in get_cache_directory().glob(f"local-{path.stem}-*.parquet"):
            stale.unlink(missing_ok=True)
        convert_bz2_to_parquet(path.read_bytes(), target)
    return target


def get_remote_cache(url: str) -> Path:
    """
    Get the Parquet cache of a remote bz2 file, checked for changes at most once a day.

    The check is a conditional request with the stored ETag, so an unchanged file is
    not downloaded again. If the server can't be reached, the cached copy is used.

    Args:
        url (str): The URL of the bz2 file.

    Returns:
        Path: The cached Parquet file.

    Raises:
        requests.exceptions.RequestException: If the download fails and there is no cache.
    """
    key = get_cache_name(url)
    target = get_cache_directory() / f"remote-{key}.parquet"
    meta_path = get_cache_directory() / f"remote-{key}.json"
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
            convert_bz2_to_parquet(response.content, target)
            meta = {
                "url": url,
                "etag": response.headers.get("ETag"),
                "checked": time.time(),
            }
        meta_path.write_text(json.dumps(meta))
    except requests.exceptions.RequestException:
        if target.exists():
            return target
        raise
    return target


def load_lazy_frame(
    file_name: str, base_url: str, local_directory: Path | None
) -> pl.LazyFrame:
    """
    Load a lazy scan of one database file from the local cache, downloading it if needed.

    Args:
        file_name (str): The compressed file, e.g. "equities.bz2".
        base_url (str): The URL the file is published under.
        local_directory (Path | None): The local directory holding the file, or None
            to download it.

    Returns:
        pl.LazyFrame: A lazy scan of the cached Parquet file.
    """
    source = (
        get_local_cache(local_directory / file_name)
        if local_directory
        else get_remote_cache(base_url + file_name)
    )
    return pl.scan_parquet(source)
