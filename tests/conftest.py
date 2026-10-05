"""Shared pytest setup.

Before tests are collected, the compression artifacts that the package loads
(`compression/<asset>.bz2` and `compression/categories/<asset>_categories.gzip`) are
regenerated from the `database/` CSVs of the checked-out branch, so the tests run against the
data under review rather than the last CI build. The original bytes are restored when the
session ends, so the working tree stays clean.
"""

import pathlib
from typing import Any

import pandas as pd

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]

# Columns excluded per asset class when building the `<asset>_categories.gzip`
# files. Must stay in sync with the `Update-Categorization-Files` job in
# `.github/workflows/database_update.yml`.
ASSET_CATEGORY_SKIP_COLS = {
    "cryptos": {"name", "summary"},
    "currencies": {"name"},
    "equities": {"name", "summary", "website", "delisted"},
    "etfs": {"name", "summary", "delisted"},
    "funds": {"name", "summary", "manager_name", "manager_bio"},
    "indices": {"name"},
    "moneymarkets": {"name"},
}

# Asset classes stored as one CSV per exchange under `database/<asset>/`
# rather than a single `database/<asset>.csv`.
ASSETS_SPLIT_BY_EXCHANGE = {"equities", "etfs", "funds"}


def _load_asset_frame(asset: str) -> pd.DataFrame | None:
    """Load an asset class from `database/` the same way the
    Database-Update workflow does before compressing it."""
    read_options = {"dtype": str, "keep_default_na": False}
    if asset in ASSETS_SPLIT_BY_EXCHANGE:
        files = sorted((REPO_ROOT / "database" / asset).glob("*.csv"))
        if not files:
            return None
        df = pd.concat(
            [pd.read_csv(f, **read_options) for f in files],
            ignore_index=True,
        )
    else:
        csv_path = REPO_ROOT / "database" / f"{asset}.csv"
        if not csv_path.exists():
            return None
        df = pd.read_csv(csv_path, **read_options)
    return df.sort_values(df.columns[0]).reset_index(drop=True)


def _regenerate_compression_artifacts() -> None:
    """Mirror the Database-Update workflow so tests run against compression
    artifacts derived from the *checked-out* CSV files.

    The financedatabase library reads `compression/<asset>.bz2` and
    `compression/categories/<asset>_categories.gzip`; without this step those
    artifacts lag the `database/` CSVs on a PR branch and tests silently
    validate against `main` instead of the PR change.
    """
    compression_dir = REPO_ROOT / "compression"
    categories_dir = compression_dir / "categories"
    for asset, skip_cols in ASSET_CATEGORY_SKIP_COLS.items():
        df = _load_asset_frame(asset)
        if df is None:
            continue
        df.to_csv(compression_dir / f"{asset}.bz2", index=False, compression="bz2")
        # Compression preserves empty cells as empty strings. Categorization
        # intentionally treats those cells as missing so they are not emitted
        # as valid options, matching the workflow's default NA handling.
        indexed = df.set_index(df.columns[0]).replace("", pd.NA)
        categories: dict[str, Any] = {}
        for column in indexed.columns:
            if column in skip_cols:
                continue
            categories[column] = sorted(indexed[column].dropna().unique(), key=str)
        cat_df = pd.DataFrame.from_dict(categories, orient="index").reset_index()
        cat_df.to_csv(
            categories_dir / f"{asset}_categories.gzip",
            index=False,
            compression={"method": "gzip", "mtime": 0},
        )


def _snapshot_compression_artifacts() -> dict[pathlib.Path, bytes]:
    """Capture current bytes of compression artifacts so they can be restored."""
    compression_dir = REPO_ROOT / "compression"
    snapshot: dict[pathlib.Path, bytes] = {}
    for asset in ASSET_CATEGORY_SKIP_COLS:
        for path in (
            compression_dir / f"{asset}.bz2",
            compression_dir / "categories" / f"{asset}_categories.gzip",
        ):
            if path.exists():
                snapshot[path] = path.read_bytes()
    return snapshot


def _restore_compression_artifacts(snapshot: dict[pathlib.Path, bytes]) -> None:
    """Restore compression artifacts to their pre-test contents."""
    for path, data in snapshot.items():
        try:
            path.write_bytes(data)
        except Exception:
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
