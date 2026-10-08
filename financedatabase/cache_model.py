"""Cache Model"""

__docformat__ = "google"

import bz2
import hashlib
import io
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


def write_atomically(target: Path, write) -> None:
    """
    Write a file through a temporary file, so readers never see a partial file.

    Args:
        target (Path): The file to write.
        write (Callable[[str], None]): Writes the content to the given path.
    """
    handle, temporary = tempfile.mkstemp(dir=target.parent, suffix=".parquet.tmp")
    os.close(handle)
    try:
        write(temporary)
        os.replace(temporary, target)
    finally:
        if os.path.exists(temporary):
            os.remove(temporary)


def convert_bz2_to_parquet(content: bytes, target: Path) -> None:
    """
    Convert a bz2-compressed CSV to Parquet with the types of the published Parquet files.

    Only used for compressed files published before the typed Parquet files. Every
    column is read as text, so values such as the ticker NA stay as written; delisted
    becomes a Boolean and a column empty in every row Float64, as the pipeline writes.

    Args:
        content (bytes): The bz2-compressed CSV.
        target (Path): The Parquet file to write.
    """
    frame = pl.read_csv(bz2.decompress(content), infer_schema=False)
    if "delisted" in frame.columns:
        frame = frame.with_columns(pl.col("delisted").eq("True").fill_null(False))
    empty = [
        name
        for name in frame.columns[1:]
        if frame.schema[name] == pl.String
        and frame.get_column(name).null_count() == frame.height
    ]
    frame = frame.with_columns([pl.col(name).cast(pl.Float64) for name in empty])
    write_atomically(target, frame.write_parquet)


def store_parquet(content: bytes, target: Path) -> None:
    """
    Store a published Parquet file as it is, after checking that it is one.

    Args:
        content (bytes): The Parquet file.
        target (Path): The file to write.

    Raises:
        ValueError: If the content isn't a Parquet file.
    """
    if len(content) < 12 or content[:4] != b"PAR1" or content[-4:] != b"PAR1":
        raise ValueError("The downloaded file is not a Parquet file.")
    pl.read_parquet_schema(io.BytesIO(content))
    write_atomically(target, lambda path: Path(path).write_bytes(content))


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
    Get the Parquet cache of a remote file, checked for changes at most once a day.

    A published Parquet file is stored as it is; a bz2 CSV is converted.

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
            if url.endswith(".parquet"):
                store_parquet(response.content, target)
            else:
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

    The typed Parquet file published next to the bz2 CSV is used when it exists, so no
    conversion is needed; otherwise the bz2 CSV is converted to the same types.

    Args:
        file_name (str): The compressed file, e.g. "equities.bz2".
        base_url (str): The URL the file is published under.
        local_directory (Path | None): The local directory holding the file, or None
            to download it.

    Returns:
        pl.LazyFrame: A lazy scan of the cached Parquet file.
    """
    parquet_name = Path(file_name).with_suffix(".parquet").name
    if local_directory:
        if (local_directory / parquet_name).exists():
            return pl.scan_parquet(local_directory / parquet_name)
        return pl.scan_parquet(get_local_cache(local_directory / file_name))
    parquet_url = base_url + parquet_name
    marker = get_cache_directory() / f"remote-{get_cache_name(parquet_url)}.missing"
    if not marker.exists() or time.time() - marker.stat().st_mtime >= REFRESH_SECONDS:
        try:
            source = get_remote_cache(parquet_url)
            marker.unlink(missing_ok=True)
            return pl.scan_parquet(source)
        except (requests.exceptions.HTTPError, ValueError):
            marker.touch()
        except requests.exceptions.RequestException:
            pass
    return pl.scan_parquet(get_remote_cache(base_url + file_name))
