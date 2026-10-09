"""Shared pytest setup.

Before tests are collected, the compression artifacts that the package loads
(`compression/<asset>.bz2`, `compression/<asset>.parquet` and the category files in
`compression/categories/`) are regenerated from the `database/` CSVs of the checked-out
branch with the same pipeline as the Database-Update workflow, so the tests run against the
data under review rather than the last CI build. The original bytes are restored when the
session ends, so the working tree stays clean.
"""

import os
import pathlib

from scripts.compression.compression_controller import update_categories
from scripts.compression.compression_model import (
    ASSET_CLASSES,
    get_typed_frame,
    scan_asset_class,
    write_compressed_csv,
)

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
DATABASE = str(REPO_ROOT / "database")
COMPRESSION = str(REPO_ROOT / "compression")


def _get_artifact_paths() -> list[pathlib.Path]:
    """List every compression artifact the regeneration writes."""
    compression = REPO_ROOT / "compression"
    paths = []
    for asset in ASSET_CLASSES:
        paths += [
            compression / f"{asset}.bz2",
            compression / f"{asset}.parquet",
            compression / "categories" / f"{asset}_categories.gzip",
            compression / "categories" / f"{asset}_categories.parquet",
        ]
    return paths


def _regenerate_compression_artifacts() -> None:
    """Rebuild the compression artifacts from the checked-out `database/` CSVs.

    The Parquet files are written with Polars' default compression instead of the
    workflow's slower maximum level: the content is the same, only the file is larger.
    """
    for asset in ASSET_CLASSES:
        frame = scan_asset_class(DATABASE, asset).collect()
        write_compressed_csv(frame, os.path.join(COMPRESSION, f"{asset}.bz2"))
        get_typed_frame(frame).write_parquet(
            os.path.join(COMPRESSION, f"{asset}.parquet"), statistics=True
        )
    update_categories(DATABASE, COMPRESSION)


def _snapshot_compression_artifacts() -> dict[pathlib.Path, bytes | None]:
    """Capture the current bytes of the compression artifacts (None when missing)."""
    return {
        path: path.read_bytes() if path.exists() else None
        for path in _get_artifact_paths()
    }


def _restore_compression_artifacts(snapshot: dict[pathlib.Path, bytes | None]) -> None:
    """Restore the compression artifacts to their pre-test contents."""
    for path, data in snapshot.items():
        try:
            if data is None:
                path.unlink(missing_ok=True)
            else:
                path.write_bytes(data)
        except OSError:
            pass


# Regenerate compression artifacts BEFORE pytest collects test modules. The
# asset-class test modules instantiate `fd.X(use_local_location=True)` at
# import time, so the artifacts must already be in sync with the checked-out
# CSVs by then — a session-scoped fixture runs too late. A snapshot of the
# original bytes is taken first; `pytest_sessionfinish` restores them so the
# working tree stays clean for contributors.
_compression_snapshot = _snapshot_compression_artifacts()
_regenerate_compression_artifacts()


def pytest_sessionfinish(session, exitstatus) -> None:  # noqa: ARG001
    """Restore compression artifacts after the pytest session ends."""
    _restore_compression_artifacts(_compression_snapshot)
