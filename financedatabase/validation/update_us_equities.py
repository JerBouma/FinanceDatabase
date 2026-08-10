"""Conservatively import and classify US equity candidates.

The upstream NASDAQ screener contains several security types.  This module
admits only names that provide strong equity evidence, reports everything
else, and defaults to a dry run.  It is development tooling and is excluded
from the distributed package by ``pyproject.toml``.
"""

from __future__ import annotations

import argparse
import csv
import os
import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
EQUITIES_DIR = REPO_ROOT / "database" / "equities"
OVERRIDES_PATH = REPO_ROOT / "database" / "equity_instrument_type_overrides.csv"
CATEGORIES_PATH = (
    REPO_ROOT / "compression" / "categories" / "github_exchange_categories.xlsx"
)

ALLOWED_INSTRUMENT_TYPES = (
    "Common Stock",
    "Preferred Stock",
    "Depositary Receipt",
    "Partnership Interest",
)
EQUITY_COLUMNS = (
    "name",
    "instrument_type",
    "summary",
    "currency",
    "sector",
    "industry_group",
    "industry",
    "exchange",
    "mic",
    "market",
    "country",
    "state",
    "city",
    "zipcode",
    "website",
    "market_cap",
    "isin",
    "cusip",
    "figi",
    "composite_figi",
    "shareclass_figi",
    "delisted",
)
REJECTED_INSTRUMENT_TYPES = (
    "Warrant",
    "Unit",
    "Right",
    "Debt Security",
    "Hybrid Security",
    "Exchange-Traded Product",
    "Fund",
)

SOURCE_URLS = {
    "NASDAQ": "https://raw.githubusercontent.com/rreichel3/US-Stock-Symbols/main/nasdaq/nasdaq_full_tickers.json",
    "NYSE": "https://raw.githubusercontent.com/rreichel3/US-Stock-Symbols/main/nyse/nyse_full_tickers.json",
    "AMEX": "https://raw.githubusercontent.com/rreichel3/US-Stock-Symbols/main/amex/amex_full_tickers.json",
}
SOURCE_ROUTES = {
    "NASDAQ": {"exchange": "NMS", "mic": "XNAS", "market": "NASDAQ Global Select"},
    "NYSE": {"exchange": "NYQ", "mic": "XNYS", "market": "New York Stock Exchange"},
    "AMEX": {"exchange": "ASE", "mic": "XASE", "market": "NYSE MKT"},
}
BACKFILL_SOURCES = {
    "NMS": "NASDAQ",
    "NGM": "NASDAQ",
    "NCM": "NASDAQ",
    "NYQ": "NYSE",
    "ASE": "AMEX",
}

PARTNERSHIP_PATTERN = re.compile(
    r"\b(?:common )?units? representing (?:limited )?partner(?:ship)? interests?\b"
    r"|\blimited partnership interests?\b",
    re.IGNORECASE,
)
DEPOSITARY_PATTERN = re.compile(
    r"\b(?:american|global) depositary (?:shares?|receipts?)\b"
    r"|\b(?:ADR|ADS)\b(?!-)",
    re.IGNORECASE,
)
COMMON_PATTERN = re.compile(
    r"\bcommon (?:stock|shares?)\b|\bordinary shares?\b",
    re.IGNORECASE,
)
PREFERRED_PATTERN = re.compile(
    r"\bpreferred (?:stock|shares?|units?|series)\b"
    r"|\bdepositary shares?.{0,120}\bpreferred\b"
    r"|\bpreference shares?\b|\bpfd(?:\s+ser(?:ies)?)?\b",
    re.IGNORECASE,
)
REJECTION_PATTERNS = (
    (
        "Hybrid Security",
        re.compile(
            r"\btrust preferred securities\b"
            r"|\bcapital trust\b.{0,80}\bpfd\b"
            r"|\btr pfd (?:secs?|securities)\b",
            re.IGNORECASE,
        ),
    ),
    ("Warrant", re.compile(r"\bwarrants?\b", re.IGNORECASE)),
    ("Right", re.compile(r"\brights?\b", re.IGNORECASE)),
    ("Unit", re.compile(r"\bunits?\b", re.IGNORECASE)),
    (
        "Debt Security",
        re.compile(
            r"\b(?:senior|subordinated|convertible) notes?\b"
            r"|\bnotes? due \d{4}\b|\bdebentures?\b|\bbonds? due \d{4}\b",
            re.IGNORECASE,
        ),
    ),
    (
        "Exchange-Traded Product",
        re.compile(
            r"\b(?:ETF|ETN)\b|\bexchange[- ]traded (?:fund|note)\b", re.IGNORECASE
        ),
    ),
    (
        "Fund",
        re.compile(
            r"\bfunds?\b|\bterm trust\b|\bincome builder opportunities trust\b",
            re.IGNORECASE,
        ),
    ),
)


@dataclass(frozen=True)
class InstrumentDecision:
    status: str
    instrument_type: str
    reason: str


@dataclass(frozen=True)
class InstrumentOverride:
    decision: str
    instrument_type: str
    evidence_url: str
    notes: str


def _normalized(value: object) -> str:
    return str(value or "").strip()


def classify_instrument(
    name: object, override: InstrumentOverride | None = None
) -> InstrumentDecision:
    """Classify a security name, failing closed when evidence conflicts."""
    if override is not None:
        status = "accepted" if override.decision == "allow" else "rejected"
        return InstrumentDecision(status, override.instrument_type, "reviewed_override")

    normalized_name = _normalized(name)
    if not normalized_name:
        return InstrumentDecision("quarantined", "", "missing_name")

    partnership = bool(PARTNERSHIP_PATTERN.search(normalized_name))
    depositary = bool(DEPOSITARY_PATTERN.search(normalized_name))
    common = bool(COMMON_PATTERN.search(normalized_name))
    preferred = bool(PREFERRED_PATTERN.search(normalized_name))
    rejected = [
        instrument_type
        for instrument_type, pattern in REJECTION_PATTERNS
        if pattern.search(normalized_name)
    ]

    # A genuine partnership phrase contains "unit" by definition.  It is the
    # only accepted exception to the generic bundled-unit rejection rule.
    if partnership:
        rejected = [value for value in rejected if value != "Unit"]

    if preferred:
        accepted_type = "Preferred Stock"
    elif partnership:
        accepted_type = "Partnership Interest"
    elif depositary:
        accepted_type = "Depositary Receipt"
    elif common:
        accepted_type = "Common Stock"
    else:
        accepted_type = ""
    if rejected:
        # Explicit non-equity evidence wins over words describing the security
        # into which it converts or the ownership interest it bundles.
        return InstrumentDecision("rejected", rejected[0], "name_pattern")
    if accepted_type:
        return InstrumentDecision("accepted", accepted_type, "name_pattern")
    return InstrumentDecision("quarantined", "", "insufficient_name_evidence")


def load_overrides(
    path: Path = OVERRIDES_PATH,
) -> dict[tuple[str, str], InstrumentOverride]:
    """Load and validate reviewed source-exchange/symbol decisions."""
    if not path.exists():
        return {}
    overrides: dict[tuple[str, str], InstrumentOverride] = {}
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {
            "source_exchange",
            "symbol",
            "decision",
            "instrument_type",
            "evidence_url",
            "notes",
        }
        if not reader.fieldnames or set(reader.fieldnames) != required:
            raise ValueError(f"Unexpected override schema in {path}")
        for line_number, row in enumerate(reader, start=2):
            source_exchange = _normalized(row["source_exchange"]).upper()
            symbol = _normalized(row["symbol"]).upper()
            decision = _normalized(row["decision"]).lower()
            instrument_type = _normalized(row["instrument_type"])
            evidence_url = _normalized(row["evidence_url"])
            if source_exchange not in SOURCE_ROUTES or not symbol:
                raise ValueError(f"Invalid override key at {path}:{line_number}")
            if decision not in {"allow", "reject"}:
                raise ValueError(f"Invalid override decision at {path}:{line_number}")
            valid_types = (
                ALLOWED_INSTRUMENT_TYPES
                if decision == "allow"
                else REJECTED_INSTRUMENT_TYPES
            )
            if instrument_type not in valid_types or not evidence_url:
                raise ValueError(
                    f"Invalid override evidence/type at {path}:{line_number}"
                )
            key = (source_exchange, symbol)
            if key in overrides:
                raise ValueError(
                    f"Duplicate override for {key} at {path}:{line_number}"
                )
            overrides[key] = InstrumentOverride(
                decision=decision,
                instrument_type=instrument_type,
                evidence_url=evidence_url,
                notes=_normalized(row["notes"]),
            )
    return overrides


def calculate_market_cap(value: object) -> str | float:
    if pd.isna(value) or not value:
        return np.nan
    amount = float(value)
    for label, threshold in (
        ("Mega Cap", 200_000_000_000),
        ("Large Cap", 10_000_000_000),
        ("Mid Cap", 2_000_000_000),
        ("Small Cap", 300_000_000),
        ("Micro Cap", 50_000_000),
        ("Nano Cap", 0),
    ):
        if amount >= threshold:
            return label
    return np.nan


def _lookup_industry(raw: object, industries: pd.DataFrame) -> str | float:
    try:
        result = industries.loc[raw].iloc[0]
        return result.iloc[0] if isinstance(result, pd.Series) else result
    except KeyError:
        return np.nan


def build_new_equity(
    row: pd.Series,
    decision: InstrumentDecision,
    route: Mapping[str, str],
    industries: pd.DataFrame,
    equities: pd.DataFrame,
) -> dict[str, object]:
    industry = _lookup_industry(row.get("industry", ""), industries)
    group_rows = (
        equities[equities["industry"] == industry]
        if pd.notna(industry)
        else equities.iloc[0:0]
    )
    industry_group = (
        group_rows["industry_group"].mode().iloc[0] if not group_rows.empty else np.nan
    )
    sector_rows = equities[
        (equities["industry"] == industry)
        & (equities["industry_group"] == industry_group)
    ]
    sector = sector_rows["sector"].mode().iloc[0] if not sector_rows.empty else np.nan
    return {
        "name": row.get("name", np.nan),
        "instrument_type": decision.instrument_type,
        "summary": np.nan,
        "currency": "USD",
        "sector": sector,
        "industry_group": industry_group,
        "industry": industry,
        "exchange": route["exchange"],
        "mic": route["mic"],
        "market": route["market"],
        "country": row.get("country", np.nan),
        "state": np.nan,
        "city": np.nan,
        "zipcode": np.nan,
        "website": np.nan,
        "market_cap": calculate_market_cap(row.get("marketCap")),
        "isin": np.nan,
        "cusip": np.nan,
        "figi": np.nan,
        "composite_figi": np.nan,
        "shareclass_figi": np.nan,
        "delisted": False,
    }


def load_equities(equities_dir: Path = EQUITIES_DIR) -> pd.DataFrame:
    files = sorted(equities_dir.glob("*.csv"))
    if not files:
        raise RuntimeError(f"No equity CSVs found under {equities_dir}")
    frames = [
        pd.read_csv(path, index_col=0, dtype=str, keep_default_na=False)
        for path in files
    ]
    expected = list(EQUITY_COLUMNS)
    for path, frame in zip(files, frames):
        if list(frame.columns) != expected:
            raise RuntimeError(f"Equity schema mismatch in {path}")
    return pd.concat(frames)


def fetch_sources() -> dict[str, pd.DataFrame]:
    return {
        source: pd.read_json(url).set_index("symbol")
        for source, url in SOURCE_URLS.items()
    }


def write_report(path: Path, rows: Iterable[dict[str, object]]) -> None:
    fieldnames = [
        "source_exchange",
        "symbol",
        "name",
        "status",
        "instrument_type",
        "reason",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _write_summary(counts: Mapping[str, int]) -> None:
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    lines = ["## US equity import", "", "| Result | Count |", "|---|---:|"]
    lines.extend(f"| {key} | {value} |" for key, value in sorted(counts.items()))
    rendered = "\n".join(lines) + "\n"
    print(rendered)
    if summary:
        with Path(summary).open("a", encoding="utf-8") as handle:
            handle.write(rendered)


def run_import(
    *,
    apply: bool,
    report_path: Path,
    equities_dir: Path = EQUITIES_DIR,
    overrides_path: Path = OVERRIDES_PATH,
    categories_path: Path = CATEGORIES_PATH,
    source_frames: Mapping[str, pd.DataFrame] | None = None,
    industries: pd.DataFrame | None = None,
) -> dict[str, int]:
    equities = load_equities(equities_dir)
    existing = set(equities.index)
    overrides = load_overrides(overrides_path)
    sources = dict(source_frames) if source_frames is not None else fetch_sources()
    if industries is None:
        industries = pd.read_excel(categories_path, sheet_name="industry", index_col=1)

    accepted_by_exchange: dict[str, dict[str, dict[str, object]]] = {}
    report_rows: list[dict[str, object]] = []
    counts = {"accepted": 0, "rejected": 0, "quarantined": 0, "already_present": 0}
    for source_name, source in sources.items():
        source_exchange = source_name.upper()
        route = SOURCE_ROUTES[source_exchange]
        for raw_symbol, row in source.iterrows():
            symbol = _normalized(raw_symbol).upper()
            if not symbol or symbol in existing:
                counts["already_present"] += 1
                continue
            decision = classify_instrument(
                row.get("name", ""), overrides.get((source_exchange, symbol))
            )
            counts[decision.status] += 1
            if decision.status == "accepted":
                accepted_by_exchange.setdefault(route["exchange"], {})[symbol] = (
                    build_new_equity(row, decision, route, industries, equities)
                )
                existing.add(symbol)
            report_rows.append(
                {
                    "source_exchange": source_exchange,
                    "symbol": symbol,
                    "name": row.get("name", ""),
                    "status": decision.status,
                    "instrument_type": decision.instrument_type,
                    "reason": decision.reason,
                }
            )

    if apply:
        for exchange, additions in accepted_by_exchange.items():
            path = equities_dir / f"{exchange}.csv"
            current = pd.read_csv(path, index_col=0, dtype=str, keep_default_na=False)
            incoming = pd.DataFrame.from_dict(additions, orient="index")
            incoming.index.name = "symbol"
            incoming = incoming[current.columns]
            updated = pd.concat([current, incoming]).sort_index()
            updated.to_csv(path, lineterminator="\n")

    write_report(report_path, report_rows)
    _write_summary(counts)
    return counts


def run_backfill(
    *,
    apply: bool,
    report_path: Path,
    equities_dir: Path = EQUITIES_DIR,
    overrides_path: Path = OVERRIDES_PATH,
) -> dict[str, int]:
    overrides = load_overrides(overrides_path)
    report_rows: list[dict[str, object]] = []
    counts = {
        "accepted": 0,
        "rejected": 0,
        "quarantined": 0,
        "removed": 0,
        "updated": 0,
    }
    for exchange, source_exchange in BACKFILL_SOURCES.items():
        path = equities_dir / f"{exchange}.csv"
        if not path.exists():
            continue
        frame = pd.read_csv(path, index_col=0, dtype=str, keep_default_na=False)
        remove: list[str] = []
        file_updated = 0
        for symbol, row in frame.iterrows():
            decision = classify_instrument(
                row.get("name", ""),
                overrides.get((source_exchange, _normalized(symbol).upper())),
            )
            if decision.status == "accepted":
                current = _normalized(row.get("instrument_type", ""))
                if not current:
                    frame.loc[symbol, "instrument_type"] = decision.instrument_type
                    counts["updated"] += 1
                    file_updated += 1
                elif current != decision.instrument_type:
                    decision = InstrumentDecision(
                        "quarantined", "", "existing_type_conflict"
                    )
            elif decision.status == "rejected":
                remove.append(symbol)
            counts[decision.status] += 1
            if decision.status != "accepted":
                report_rows.append(
                    {
                        "source_exchange": source_exchange,
                        "symbol": symbol,
                        "name": row.get("name", ""),
                        "status": decision.status,
                        "instrument_type": decision.instrument_type,
                        "reason": decision.reason,
                    }
                )
        if remove:
            frame = frame.drop(index=remove)
            counts["removed"] += len(remove)
        if apply and (remove or file_updated):
            frame.sort_index().to_csv(path, lineterminator="\n")
    write_report(report_path, report_rows)
    _write_summary(counts)
    return counts


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="write accepted changes")
    parser.add_argument(
        "--backfill", action="store_true", help="classify the targeted US files"
    )
    parser.add_argument(
        "--report", type=Path, required=True, help="CSV report destination"
    )
    parser.add_argument("--equities-dir", type=Path, default=EQUITIES_DIR)
    parser.add_argument("--overrides", type=Path, default=OVERRIDES_PATH)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    runner = run_backfill if args.backfill else run_import
    runner(
        apply=args.apply,
        report_path=args.report,
        equities_dir=args.equities_dir,
        overrides_path=args.overrides,
    )
    if not args.apply:
        print("Dry run only; pass --apply to update equity CSVs.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
