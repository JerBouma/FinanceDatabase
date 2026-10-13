"""Equities Controller"""

__docformat__ = "google"

import argparse
import glob
import os

import pandas as pd

from scripts.equities import equities_model, status_model
from scripts.listings.helpers import fetch_nasdaq_trader, write_csv


def update_us_equities(database: str = "database") -> int:
    """
    Add new NASDAQ, NYSE and NYSE American equities and refresh market cap tiers.

    Args:
        database (str): The database folder.

    Returns:
        int: The number of added or updated rows.
    """
    feeds = [
        feed
        for feed in (equities_model.load_feed(name) for name in equities_model.FEEDS)
        if feed is not None
    ]
    exchange_data = pd.concat(feeds) if feeds else pd.DataFrame()
    exchange_data = exchange_data[~exchange_data.index.duplicated(keep="first")]

    # Feed industry -> industry; labels spanning several industries are left out.
    fd_industries = (
        pd.read_csv("scripts/us_feed_industries.csv", dtype=str, keep_default_na=False)
        .set_index("feed_industry")["industry"]
        .to_dict()
    )
    equities = equities_model.read_equities(database)
    exchange_to_mic = (
        equities[equities["mic"] != ""]
        .drop_duplicates("exchange")
        .set_index("exchange")["mic"]
        .to_dict()
    )
    other_symbols = equities_model.get_other_symbols(database)

    # A delisted row whose ticker now belongs to another company makes way for it.
    reused = equities_model.find_reused_tickers(equities, exchange_data)
    if len(reused) > equities_model.MAX_REUSED_TICKERS:
        print(f"! {len(reused)} reused tickers looks implausible; replacing none")
        reused = []

    ticker_dict: dict = {}
    for symbol, row in exchange_data.iterrows():
        market_cap = equities_model.calculate_market_cap(
            pd.to_numeric(row.get("marketCap"), errors="coerce")
        )
        if symbol in reused:
            ticker_dict[symbol] = equities_model.build_new_ticker(
                row, fd_industries, equities, market_cap, exchange_to_mic
            )
        elif symbol in equities.index:
            existing = equities.loc[symbol]
            if isinstance(existing, pd.DataFrame):
                existing = existing.iloc[0]
            if pd.notna(market_cap) and existing["market_cap"] != market_cap:
                ticker_dict[symbol] = {**existing.to_dict(), "market_cap": market_cap}
        elif symbol not in other_symbols:
            ticker_dict[symbol] = equities_model.build_new_ticker(
                row, fd_industries, equities, market_cap, exchange_to_mic
            )

    # A feed glitch would move many tiers at once; such a run keeps the current tiers.
    known = exchange_data.index.isin(equities.index).sum()
    retiered = [s for s in ticker_dict if s in equities.index and s not in reused]
    if known and len(retiered) > equities_model.MAX_TIER_CHANGE_SHARE * known:
        print(f"! {len(retiered)} of {known} tiers would change; keeping the tiers")
        ticker_dict = {s: row for s, row in ticker_dict.items() if s not in retiered}

    updated = pd.DataFrame.from_dict(ticker_dict, orient="index")
    updated.index.name = "symbol"
    updated = updated.drop(columns=["symbol"], errors="ignore")
    print(f"There are {len(updated)} new updates!")
    if updated.empty:
        return 0

    replaced = updated.index.intersection(reused)
    equities = equities.drop(index=replaced)
    existing = updated.index.intersection(equities.index)
    if not existing.empty:
        equities.update(updated.loc[existing])
    new = updated.index.difference(equities.index)
    if not new.empty:
        equities = pd.concat([equities, updated.loc[new]])
    equities = equities[~equities.index.duplicated(keep="first")]
    # Existing rows without a symbol carry an empty string, new ones NaN.
    equities = equities[equities.index.notna() & (equities.index != "")]
    equities = equities.sort_index()

    # Only changed files are rewritten, each through a temporary file.
    unknown_exchange = equities["exchange"].isna() | (equities["exchange"] == "")
    for exchange, group in equities[~unknown_exchange].groupby("exchange"):
        write_csv(group, f"{database}/equities/{exchange}.csv")
    if unknown_exchange.any():
        write_csv(equities[unknown_exchange], f"{database}/equities/NAN.csv")
    return len(updated)


def remove_non_shares(database: str, dry_run: bool = False) -> list[str]:
    """
    Remove the rows of the equities files that are not company shares.

    Args:
        database (str): The database folder.
        dry_run (bool): Only report the rows, change nothing.

    Returns:
        list[str]: The removed rows as "symbol (exchange file): name".
    """
    removed = []
    for path in sorted(glob.glob(os.path.join(database, "equities", "*.csv"))):
        frame = pd.read_csv(path, index_col=0, dtype=str, keep_default_na=False)
        mask = equities_model.find_non_shares(frame)
        if not mask.any():
            continue
        file_name = os.path.basename(path)
        removed += [
            f"{s} ({file_name}): {frame.loc[s, 'name']}" for s in frame.index[mask]
        ]
        if not dry_run:
            write_csv(frame[~mask], path)
    return removed


def update_us_listing_status(
    database: str = "database", nasdaq: bytes | None = None, other: bytes | None = None
) -> tuple[int, int]:
    """
    Delist the US equities and ETFs the Nasdaq Trader directory no longer lists and
    relist the ones it lists again; delistings are skipped when implausibly many.

    Args:
        database (str): The database folder.
        nasdaq (bytes | None): nasdaqlisted.txt, downloaded when not given.
        other (bytes | None): otherlisted.txt, downloaded when not given.

    Returns:
        tuple[int, int]: The number of delisted and relisted rows.
    """
    listed = status_model.read_directory(
        nasdaq or fetch_nasdaq_trader("nasdaqlisted"),
        other or fetch_nasdaq_trader("otherlisted"),
    )
    if len(listed) < status_model.MINIMUM_DIRECTORY:
        raise ValueError(f"Nasdaq Trader directory too short ({len(listed)})")
    delisted = relisted = 0
    for folder, files in (
        ("equities", status_model.US_FILES),
        ("etfs", status_model.US_ETF_FILES),
    ):
        frames, changes, live = {}, {}, 0
        for file in files:
            path = os.path.join(database, folder, f"{file}.csv")
            if os.path.exists(path):
                frames[path] = pd.read_csv(
                    path, index_col=0, dtype=str, keep_default_na=False
                )
                changes[path] = status_model.get_status_changes(
                    frames[path], listed, shares=folder == "equities"
                )
                live += (frames[path]["delisted"] != "True").sum()
        gone = sum(len(delist) for delist, _ in changes.values())
        if gone > status_model.MAX_DELISTED_SHARE * live:
            print(
                f"  ! {gone} US {folder} delistings looks implausible; delisting none"
            )
            changes = {path: ([], relist) for path, (_, relist) in changes.items()}
            gone = 0
        delisted += gone
        for path, (delist, relist) in changes.items():
            if delist or relist:
                frames[path].loc[delist, "delisted"] = "True"
                frames[path].loc[relist, "delisted"] = "False"
                write_csv(frames[path], path)
                relisted += len(relist)
    return delisted, relisted


def delist_stale_lines(database: str = "database") -> int:
    """
    Delist the lines abroad of shares whose home listings are all delisted, and the
    regional German lines of tickers delisted on Xetra and Frankfurt.

    Args:
        database (str): The database folder.

    Returns:
        int: The number of delisted rows.
    """
    paths = sorted(glob.glob(os.path.join(database, "equities", "*.csv")))
    columns = ["symbol", "exchange", "country", "isin", "delisted"]
    equities = pd.concat(
        pd.read_csv(p, usecols=columns, dtype=str, keep_default_na=False).assign(
            _path=p
        )
        for p in paths
    ).set_index("symbol")
    stale = equities.loc[
        sorted(
            set(status_model.find_stale_lines(equities))
            | set(status_model.find_stale_german_lines(equities))
        )
    ]
    for path, rows in stale.groupby("_path"):
        frame = pd.read_csv(path, index_col=0, dtype=str, keep_default_na=False)
        frame.loc[rows.index.intersection(frame.index), "delisted"] = "True"
        write_csv(frame, path)
    return len(stale)


def run_us_equities_update() -> None:
    """
    Command line entry of the US equities update.
    """
    parser = argparse.ArgumentParser(description="Update the US equities.")
    parser.add_argument("--database", default="database")
    database = parser.parse_args().database
    try:
        update_us_equities(database)
    except Exception as error:  # noqa: BLE001
        print(f"US equities update stopped: {type(error).__name__}: {error}")
    try:
        delisted, relisted = update_us_listing_status(database)
        print(f"{delisted} US equities and ETFs delisted, {relisted} relisted")
        print(
            f"{delist_stale_lines(database)} lines abroad of delisted shares delisted"
        )
    except Exception as error:  # noqa: BLE001
        print(f"US listing status stopped: {type(error).__name__}: {error}")


def run_non_share_removal() -> None:
    """
    Command line entry of the removal of rows that are not company shares.
    """
    parser = argparse.ArgumentParser(description="Remove equities that are not shares.")
    parser.add_argument("--database", default="database")
    parser.add_argument("--dry-run", action="store_true")
    arguments = parser.parse_args()
    removed = remove_non_shares(arguments.database, arguments.dry_run)
    print(f"{len(removed)} rows that are not company shares", end="")
    print(" found:" if arguments.dry_run else " removed:" if removed else ".")
    for row in removed:
        print(f"  {row}")
