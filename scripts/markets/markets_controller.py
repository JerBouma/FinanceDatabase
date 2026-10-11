"""Markets Controller"""

__docformat__ = "google"

import argparse
from collections.abc import Callable

from scripts.listings.helpers import read_csv_text
from scripts.markets import sources_model
from scripts.markets.helpers import get_other_symbols, write
from scripts.markets.markets_model import (
    align_inav_categories,
    update_cryptos,
    update_currencies,
    update_indices,
)


def run(database: str = "database", dry_run: bool = False) -> list[str]:
    """
    Update cryptos, currencies and indices, each on its own so one failure stays isolated.

    Args:
        database (str): The database folder.
        dry_run (bool): Report without writing.

    Returns:
        list[str]: The updates that were skipped.
    """
    failures = []

    def apply(name: str, update: Callable[[], str]) -> None:
        try:
            print(f"{name}: {update()}")
        except Exception as error:  # noqa: BLE001
            failures.append(name)
            print(f"{name}: skipped ({type(error).__name__}: {error})")

    def cryptos() -> str:
        path = f"{database}/cryptos.csv"
        coins, tickers = sources_model.fetch_coins()
        frame, added, gone = update_cryptos(
            read_csv_text(path),
            coins,
            tickers,
            sources_model.fetch_coin_website,
            get_other_symbols(database, "cryptos"),
        )
        if not dry_run:
            write(frame, path, read_csv_text(path).index.is_monotonic_increasing)
        return f"{len(added)} coins added, {len(gone)} coins no longer listed removed {gone[:20]}"

    def currencies() -> str:
        path = f"{database}/currencies.csv"
        active, withdrawn, usable = sources_model.fetch_iso_currencies()
        frame, added, gone = update_currencies(
            read_csv_text(path),
            active,
            withdrawn,
            get_other_symbols(database, "currencies"),
            set(usable),
        )
        if not dry_run:
            write(frame, path, read_csv_text(path).index.is_monotonic_increasing)
        return f"currencies added {added}, withdrawn currencies removed {gone}"

    def indices() -> str:
        path = f"{database}/indices.csv"
        frame, added = update_indices(
            read_csv_text(path),
            sources_model.fetch_euronext_indices(),
            get_other_symbols(database, "indices"),
        )
        frame, aligned = align_inav_categories(frame)
        if not dry_run:
            write(frame, path, read_csv_text(path).index.is_monotonic_increasing)
        return (
            f"{len(added)} Euronext indices added, "
            f"{len(aligned)} iNAV categories aligned with their index"
        )

    apply("Cryptos (CoinGecko)", cryptos)
    apply("Currencies (ISO 4217)", currencies)
    apply("Indices (Euronext)", indices)
    if failures:
        print(f"Updates skipped this run: {', '.join(failures)}")
    return failures


def main() -> None:
    """
    Command line entry: update cryptos, currencies and indices, never failing the pipeline.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", default="database")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    try:
        run(args.database, args.dry_run)
    except Exception as error:  # noqa: BLE001
        print(f"Market update stopped: {type(error).__name__}: {error}")
