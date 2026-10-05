"""Listings Module"""

__docformat__ = "google"

import argparse
import os
import re
from collections.abc import Callable

import pandas as pd

from scripts.listings.database_model import Database
from scripts.listings.enrichment_model import (
    SecFunds,
    compose_summary,
    enrich_with_openfigi,
    learn_categories,
)
from scripts.listings.helpers import (
    SUFFIX,
    US_ETF_FILES,
    get_symbol_key,
    normalize_name,
)
from scripts.listings.sources_model import SourceResult, load_sources

MAX_DELISTINGS_PER_SOURCE = 50


def apply_source(
    db: Database,
    name: str,
    result: SourceResult,
    family: Callable[[str], str],
    api_key: str | None = None,
    use_openfigi: bool = True,
    sec: SecFunds | None = None,
) -> dict:
    """
    Add a source's new listings and delist superseded tickers. Returns a summary.
    """
    added, skipped_format, delist = [], [], []
    seen = set()
    for listing in result.listings:
        if listing.symbol in db.symbols or listing.symbol in seen:
            continue
        seen.add(listing.symbol)
        frame = db.get_frame(listing.kind, listing.file)
        existing = db.get_symbol_keys(listing.kind, listing.file).get(
            get_symbol_key(listing.symbol)
        )
        if existing and re.search(SUFFIX, listing.symbol):
            a, b = normalize_name(frame.loc[existing, "name"]), normalize_name(
                listing.name
            )
            if a and b and (a in b or b in a):
                skipped_format.append(f"{listing.symbol} (exists as {existing})")
                continue
        added.append(listing)

    rejected: list[str] = []
    if use_openfigi and added:
        added, rejected = enrich_with_openfigi(added, api_key)
    categories = {
        file: learn_categories(db.get_frame("equities", file), labels)
        for file, labels in result.classifications.items()
        if labels
    }
    for listing in added:
        learned = categories.get(listing.file, {}).get(listing.classification)
        if listing.kind == "equities" and learned and not listing.sector:
            listing.sector = learned.get("sector", "")
            listing.industry_group = learned.get("industry_group", "")
            listing.industry = learned.get("industry", "")

    # Ticker changes: a live row in the same file with the same ISIN or name whose symbol has
    # dropped off the exchange's official list is superseded by the new listing.
    official_keys_by_file: dict[str, set[str]] = {}
    for listing in added:
        official = result.official.get(listing.file)
        if official is None:
            continue
        if listing.file not in official_keys_by_file:
            official_keys_by_file[listing.file] = {get_symbol_key(s) for s in official}
        official_keys = official_keys_by_file[listing.file]
        frame = db.get_frame(listing.kind, listing.file)
        key = normalize_name(listing.name)
        matches = (
            set(db.get_live_by_name(listing.kind, listing.file).get(key, []))
            if key
            else set()
        )
        if listing.isin:
            live = frame[frame["delisted"] == "False"]
            matches |= set(live.index[live["isin"] == listing.isin])
        for old in sorted(matches):
            if old not in official and get_symbol_key(old) not in official_keys:
                delist.append((listing.kind, listing.file, old, listing.symbol))

    if len(delist) > MAX_DELISTINGS_PER_SOURCE:
        print(
            f"  ! {len(delist)} ticker changes look implausible; not delisting anything for {name}"
        )
        delist = []
    for kind, file, old, new in delist:
        frame = db.get_frame(kind, file)
        frame.loc[old, "delisted"] = "True"
        frame.attrs["changed"] = True

    for listing in added:
        frame = db.get_frame(listing.kind, listing.file)
        defaults = db.get_defaults(listing.kind, listing.file)
        row = dict.fromkeys(db.columns[listing.kind], "")
        row.update(
            name=listing.name,
            currency=listing.currency,
            exchange=listing.file,
            mic=listing.mic or defaults["mic"],
            delisted="False",
        )
        if listing.kind == "equities":
            row.update(
                market=defaults["market"],
                country=listing.country,
                sector=listing.sector,
                industry_group=listing.industry_group,
                industry=listing.industry,
                isin=listing.isin,
                figi=listing.figi,
                composite_figi=listing.composite_figi,
                shareclass_figi=listing.shareclass_figi,
            )
        else:
            row.update(isin=listing.isin, family=family(listing.name))
            if sec and listing.file in US_ETF_FILES:
                if not row["family"]:
                    if "sec_families" not in db.cache:
                        db.cache["sec_families"] = sec.get_registrant_families(db)
                    row["family"] = db.cache["sec_families"].get(
                        sec.get_registrant(listing.symbol), ""
                    )
                listing.summary = listing.summary or sec.get_objective(listing.symbol)
        row["summary"] = compose_summary(
            listing.summary, listing.symbol, row, listing.kind
        )
        db.added[db.get_path(listing.kind, listing.file)].append(
            pd.Series(row, name=listing.symbol)
        )
        db.symbols.add(listing.symbol)

    return {
        "added": added,
        "skipped_format": skipped_format,
        "delisted": delist,
        "rejected": rejected,
    }


def run(
    database: str,
    sources: dict[str, Callable[[], SourceResult]] | None = None,
    dry_run: bool = False,
    use_openfigi: bool = True,
    api_key: str | None = None,
    sec_contact: str | None = None,
) -> list[str]:
    """
    Update the database from every source; returns the names of skipped sources.

    A source that cannot be downloaded (blocked, rate limited, offline), no longer has the
    expected format, or fails while being applied is skipped: its partial changes are rolled
    back and the other sources continue.
    """
    db = Database(database)
    family = db.get_etf_families()
    sec = SecFunds(sec_contact) if sec_contact else None
    if sources is None:
        sources = load_sources(db.get_group_sector())
    failures = []
    for name, load in sources.items():
        added_before = {path: len(rows) for path, rows in db.added.items()}
        delisted_before = {path: f["delisted"].copy() for path, f in db.frames.items()}
        symbols_before = set(db.symbols)
        try:
            result = load()
            summary = apply_source(db, name, result, family, api_key, use_openfigi, sec)
        except Exception as error:
            for path in list(db.added):
                del db.added[path][added_before.get(path, 0) :]
            for path, column in delisted_before.items():
                db.frames[path]["delisted"] = column
            for path in [p for p in db.frames if p not in delisted_before]:
                del (
                    db.frames[path],
                    db.added[path],
                )
            db.symbols = symbols_before
            failures.append(name)
            print(f"{name}: skipped ({type(error).__name__}: {error})")
            continue
        counts = pd.Series(
            [f"{x.kind}/{x.file}" for x in summary["added"]], dtype=str
        ).value_counts()
        print(
            f"{name}: {len(summary['added'])} added {counts.to_dict()}, "
            f"{len(summary['delisted'])} superseded tickers delisted, "
            f"{len(summary['skipped_format'])} skipped as symbol-format duplicates, "
            f"{len(summary['rejected'])} re-filed by security type"
        )
        for note in summary["rejected"]:
            print(f"  {note}")
        for kind, file, old, new in summary["delisted"]:
            print(f"  delisted {kind}/{file} {old} (now listed as {new})")
    if not dry_run:
        db.write()
    if failures:
        print(f"Sources skipped this run: {', '.join(failures)}")
    return failures


def main() -> None:
    """
    Run the listings update from the command line; a failure is reported, never raised.
    """
    parser = argparse.ArgumentParser(
        description="Add newly listed equities and ETFs from official exchange symbol directories."
    )
    parser.add_argument("--database", default="database")
    parser.add_argument(
        "--dry-run", action="store_true", help="report only, write nothing"
    )
    parser.add_argument(
        "--no-openfigi", action="store_true", help="skip the OpenFIGI enrichment"
    )
    args = parser.parse_args()
    try:
        run(
            args.database,
            dry_run=args.dry_run,
            use_openfigi=not args.no_openfigi,
            api_key=os.environ.get("OPENFIGI_API_KEY") or None,
            sec_contact=os.environ.get("SEC_USER_AGENT_EMAIL") or None,
        )
    except Exception as error:
        print(f"Listings update skipped entirely ({type(error).__name__}: {error})")
