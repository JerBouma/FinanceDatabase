"""SEC-based enrichment for missing US security names and currencies."""

from __future__ import annotations

import argparse
import csv
import io
import json
import os
import zipfile
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

import pandas as pd
import requests

SEC_BASE = "https://www.sec.gov"
FIRST_SERIES_CLASS_YEAR = 2010
SERIES_CLASS_URL_CHANGE_YEAR = 2023
FIRST_NCEN_YEAR = 2018
FIRST_NCEN_QUARTER = 3
DEFAULT_DATASETS = (
    "database/equities.csv",
    "database/etfs.csv",
    "database/funds.csv",
    "database/moneymarkets.csv",
)
US_EXCHANGE_CODES = {
    "ASE",
    "BATS",
    "BTS",
    "NCM",
    "NGM",
    "NMS",
    "NAS",
    "NYQ",
    "NYS",
    "OBB",
    "OTC",
    "PCX",
    "PNK",
}
SEC_US_EXCHANGES = {
    "NYSE",
    "NYSE ARCA",
    "NYSE AMERICAN",
    "NASDAQ",
    "CBOE BZX",
    "OTC",
}
FOREIGN_SUFFIX_SEPARATOR = "."
GENERIC_FUND_CLASS_NAMES = {
    "A SHARES",
    "ADMINISTRATIVE CLASS",
    "ADMINISTRATIVE CLASS SHARES",
    "ADVISOR CLASS",
    "ADVISOR SHARES",
    "C SHARES",
    "CLASS A",
    "CLASS B",
    "CLASS C",
    "CLASS D",
    "CLASS I",
    "CLASS R",
    "CLASS S",
    "CLASS T",
    "CLASS Y",
    "D SHARES",
    "INSTITUTIONAL CLASS",
    "INSTITUTIONAL SHARES",
    "INVESTOR CLASS",
    "INVESTOR SHARES",
    "SERVICE CLASS",
    "Y SHARES",
}
GENERIC_FUND_SERIES_NAMES = {
    "CASH MANAGEMENT MONEY MARKET PORTFOLIO",
    "CASH MANAGEMENT PORTFOLIO",
    "CASH MANAGEMENT PRIME PORTFOLIO",
    "CONNECTICUT MUNICIPAL MONEY MARKET FUND",
    "CONNECTICUT MUNICIPAL MONEY-MARKET FUND",
    "GOVERNMENT PORTFOLIO",
    "INSTITUTIONAL MONEY MARKET SERIES",
    "LIQUID ASSETS FUND",
    "MONEY MARKET FUND",
    "MONEY MARKET PORTFOLIO",
    "MUNICIPAL MONEY MARKET FUND",
    "PRIMARY FUND",
    "PRIME PORTFOLIO",
    "PRIME RESERVE PORTFOLIO",
}


@dataclass(frozen=True)
class SourceRecord:
    """One SEC-side ticker/name candidate."""

    ticker: str
    name: str
    source: str
    security_types: frozenset[str]
    exchange: str = ""
    cik: str = ""
    series_id: str = ""
    class_id: str = ""
    series_name: str = ""
    class_name: str = ""
    identifiers: frozenset[str] = field(default_factory=frozenset)
    us_listing: bool = True


@dataclass(frozen=True)
class EnrichmentDecision:
    """A proposed enrichment for one CSV row."""

    status: str
    symbol: str
    proposed_name: str = ""
    proposed_currency: str = ""
    source: str = ""
    source_identifiers: str = ""
    confidence: str = ""
    reason: str = ""


def clean_text(value: object) -> str:
    """Return a stripped string for CSV values."""
    if value is None or pd.isna(value):
        return ""
    return str(value).strip()


def normalize_name(value: str) -> str:
    """Normalize names for ambiguity comparisons."""
    return " ".join(clean_text(value).upper().replace(".", "").replace(",", "").split())


def title_case_sec_name(value: str) -> str:
    """Title-case SEC names only when they are fully uppercase."""
    cleaned = clean_text(value)
    if cleaned and cleaned == cleaned.upper():
        return cleaned.title()
    return cleaned


def compose_series_class_name(series_name: str, class_name: str, entity_name: str = "") -> str:
    """Create a display name from SEC series/class fields."""
    series = title_case_sec_name(series_name)
    class_value = title_case_sec_name(class_name)
    entity = title_case_sec_name(entity_name)
    original_normalized_series = normalize_name(series)
    if (
        entity
        and original_normalized_series in GENERIC_FUND_SERIES_NAMES
        and normalize_name(entity) not in original_normalized_series
    ):
        series = f"{entity} - {series}"
    if not series:
        return class_value
    if not class_value:
        return series
    normalized_class = normalize_name(class_value)
    if original_normalized_series == normalized_class or normalized_class in original_normalized_series:
        return series
    if normalized_class.startswith(f"{original_normalized_series} "):
        class_value = class_value[len(title_case_sec_name(series_name)) :].strip(" -")
    return f"{series} - {class_value}"


def normalize_ticker(symbol: object) -> str:
    """Normalize a FinanceDatabase symbol to an SEC ticker candidate."""
    ticker = clean_text(symbol).upper()
    if not ticker or ticker.startswith("^"):
        return ""
    return ticker


def dataset_kind(path: str | Path) -> str:
    """Return the logical dataset kind from a CSV path."""
    stem = Path(path).stem.lower()
    if stem == "moneymarkets":
        return "moneymarkets"
    return stem


def has_foreign_suffix(symbol: str, row: pd.Series) -> bool:
    """Detect Yahoo-style non-US suffixes conservatively."""
    if FOREIGN_SUFFIX_SEPARATOR not in symbol:
        return False
    return clean_text(row.get("exchange")).upper() not in US_EXCHANGE_CODES


def row_identifiers(row: pd.Series) -> frozenset[str]:
    """Collect row identifiers that can disambiguate ticker reuse."""
    identifiers = set()
    for column in ("isin", "cusip", "figi", "composite_figi", "shareclass_figi"):
        value = clean_text(row.get(column))
        if value:
            identifiers.add(value.upper())
    return frozenset(identifiers)


def is_us_candidate_row(row: pd.Series) -> bool:
    """Return True when a row is worth attempting against SEC datasets."""
    symbol = normalize_ticker(row.get("symbol"))
    if not symbol or has_foreign_suffix(symbol, row):
        return False
    if clean_text(row.get("country")).upper() == "UNITED STATES":
        return True
    if clean_text(row.get("exchange")).upper() in US_EXCHANGE_CODES:
        return True
    return FOREIGN_SUFFIX_SEPARATOR not in symbol


def wanted_fields_missing(row: pd.Series) -> bool:
    """Return True when a row needs a name or currency fill."""
    return not clean_text(row.get("name")) or not clean_text(row.get("currency"))


def has_incomplete_fund_name(row: pd.Series, dataset: str) -> bool:
    """Return True when an existing fund name is only a generic class label."""
    if dataset not in {"funds", "moneymarkets"}:
        return False
    normalized_name = normalize_name(clean_text(row.get("name")))
    return (
        normalized_name in GENERIC_FUND_CLASS_NAMES
        or any(generic_series in normalized_name for generic_series in GENERIC_FUND_SERIES_NAMES)
    )


def should_upgrade_fund_name(row: pd.Series, dataset: str, candidate_name: str) -> bool:
    """Return True when SEC gives a fuller fund name than the current value."""
    if dataset not in {"funds", "moneymarkets"}:
        return False
    current_name = clean_text(row.get("name"))
    if not current_name:
        return False
    normalized_current = normalize_name(current_name)
    normalized_candidate = normalize_name(candidate_name)
    if normalized_candidate == normalized_current:
        return False
    return normalized_current in GENERIC_FUND_CLASS_NAMES or normalized_candidate.endswith(normalized_current)


def wanted_fields_or_name_upgrade(row: pd.Series, dataset: str) -> bool:
    """Return True when a row needs a fill or conservative name upgrade."""
    return wanted_fields_missing(row) or has_incomplete_fund_name(row, dataset)


def security_type_allowed(dataset: str, record: SourceRecord) -> bool:
    """Return True when a source record is suitable for a target dataset."""
    if dataset == "equities":
        return "equities" in record.security_types
    if dataset in {"etfs", "funds", "moneymarkets"}:
        return bool(record.security_types & {"etfs", "funds", "moneymarkets"})
    return False


def choose_candidate(
    row: pd.Series,
    records: Iterable[SourceRecord],
    dataset: str,
) -> EnrichmentDecision:
    """Choose a conservative enrichment candidate for one row."""
    symbol = normalize_ticker(row.get("symbol"))
    matching = [record for record in records if security_type_allowed(dataset, record)]
    if not is_us_candidate_row(row):
        return EnrichmentDecision(status="skipped", symbol=symbol, reason="not_us_candidate")
    if not wanted_fields_or_name_upgrade(row, dataset):
        return EnrichmentDecision(status="skipped", symbol=symbol, reason="no_missing_target_fields")
    if not matching:
        return EnrichmentDecision(status="skipped", symbol=symbol, reason="no_sec_match")

    row_ids = row_identifiers(row)
    source_ids = frozenset().union(*(record.identifiers for record in matching))
    if row_ids and not row_ids.intersection(source_ids):
        best = matching[0]
        proposed_name = ""
        if not clean_text(row.get("name")) or should_upgrade_fund_name(row, dataset, best.name):
            proposed_name = best.name
        return EnrichmentDecision(
            status="review",
            symbol=symbol,
            proposed_name=proposed_name,
            proposed_currency="USD" if not clean_text(row.get("currency")) and best.us_listing else "",
            source=best.source,
            source_identifiers=";".join(sorted(source_ids)),
            confidence="low",
            reason="row_has_identifier_without_sec_identifier_match",
        )

    normalized_names = {normalize_name(record.name) for record in matching if clean_text(record.name)}
    if len(normalized_names) > 1:
        return EnrichmentDecision(
            status="review",
            symbol=symbol,
            source=";".join(sorted({record.source for record in matching})),
            source_identifiers=";".join(sorted(source_ids)),
            confidence="low",
            reason="ambiguous_sec_names",
        )

    chosen = next((record for record in matching if record.name), matching[0])
    current_name = clean_text(row.get("name"))
    proposed_name = ""
    reason = "exact_unambiguous_sec_match"
    if not current_name:
        proposed_name = chosen.name
    elif should_upgrade_fund_name(row, dataset, chosen.name):
        proposed_name = chosen.name
        reason = "incomplete_name_sec_series_class_match"
    proposed_currency = "USD" if not clean_text(row.get("currency")) and chosen.us_listing else ""
    if not proposed_name and not proposed_currency:
        return EnrichmentDecision(status="skipped", symbol=symbol, reason="no_applicable_fill")

    confidence = "high"
    if row_ids and row_ids.intersection(source_ids):
        confidence = "high_identifier_match"

    return EnrichmentDecision(
        status="accepted",
        symbol=symbol,
        proposed_name=proposed_name,
        proposed_currency=proposed_currency,
        source=chosen.source,
        source_identifiers=";".join(sorted(source_ids)),
        confidence=confidence,
        reason=reason,
    )


class SecCache:
    """Small SEC downloader with on-disk cache."""

    def __init__(self, cache_dir: str | Path, user_agent: str) -> None:
        if not user_agent:
            raise ValueError("Provide --user-agent or set SEC_USER_AGENT for SEC requests.")
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": user_agent})

    def get(self, url: str) -> bytes:
        """Fetch a URL, using a filename-safe cache path."""
        cache_name = url.replace("https://", "").replace("/", "__")
        cache_path = self.cache_dir / cache_name
        if cache_path.exists():
            return cache_path.read_bytes()
        response = self.session.get(url, timeout=60)
        response.raise_for_status()
        cache_path.write_bytes(response.content)
        return response.content


def rows_from_sec_table(payload: bytes) -> Iterable[dict[str, str]]:
    """Yield dictionaries from an SEC JSON table with fields/data keys."""
    sec_table = json.loads(payload)
    fields = sec_table["fields"]
    for data_row in sec_table["data"]:
        yield {field: clean_text(value) for field, value in zip(fields, data_row)}


def load_company_records(cache: SecCache) -> list[SourceRecord]:
    """Load operating-company ticker records."""
    records = []
    payload = cache.get(f"{SEC_BASE}/files/company_tickers_exchange.json")
    for row in rows_from_sec_table(payload):
        exchange = clean_text(row.get("exchange"))
        records.append(
            SourceRecord(
                ticker=normalize_ticker(row.get("ticker")),
                name=clean_text(row.get("name")),
                source="company_tickers_exchange",
                security_types=frozenset({"equities"}),
                exchange=exchange,
                cik=clean_text(row.get("cik")),
                us_listing=exchange.upper() in SEC_US_EXCHANGES,
            )
        )
    return records


def series_class_urls(years: Iterable[int]) -> Iterable[tuple[int, str]]:
    """Yield known SEC investment company series/class CSV URLs."""
    current = (
        f"{SEC_BASE}/files/investment/data/other/investment-company-series-class-information/"
        "investment_company_series_class.csv"
    )
    yield 0, current
    for year in years:
        if year == FIRST_SERIES_CLASS_YEAR:
            filename = "investmentcompanyseriesclass2010.csv"
            folder = "investment-company-series-and-class-information"
        elif year >= SERIES_CLASS_URL_CHANGE_YEAR:
            filename = f"investment-company-series-class-{year}.csv"
            folder = "investment-company-series-class-information"
        else:
            filename = f"investment_company_series_class_{year}.csv"
            folder = "investment-company-series-and-class-information"
        yield year, f"{SEC_BASE}/files/investment/data/other/{folder}/{filename}"


def load_series_class_records(cache: SecCache, years: Iterable[int]) -> list[SourceRecord]:
    """Load current and historical investment company class records."""
    records = []
    for year, url in series_class_urls(years):
        try:
            payload = cache.get(url).decode("utf-8-sig")
        except requests.HTTPError:
            continue
        source = "investment_company_series_class" if year == 0 else f"investment_company_series_class_{year}"
        reader = csv.DictReader(io.StringIO(payload))
        for row in reader:
            ticker = normalize_ticker(row.get("Class Ticker"))
            class_name = clean_text(row.get("Class Name"))
            series_name = clean_text(row.get("Series Name"))
            if not ticker or not (class_name or series_name):
                continue
            records.append(
                SourceRecord(
                    ticker=ticker,
                    name=compose_series_class_name(series_name, class_name, clean_text(row.get("Entity Name"))),
                    source=source,
                    security_types=frozenset({"etfs", "funds", "moneymarkets"}),
                    cik=clean_text(row.get("CIK Number")),
                    series_id=clean_text(row.get("Series ID")),
                    class_id=clean_text(row.get("Class ID")),
                    series_name=series_name,
                    class_name=class_name,
                    identifiers=frozenset(
                        value
                        for value in (
                            clean_text(row.get("Series ID")).upper(),
                            clean_text(row.get("Class ID")).upper(),
                        )
                        if value
                    ),
                )
            )
    return records


def load_mutual_fund_ticker_records(cache: SecCache) -> list[SourceRecord]:
    """Load fund ticker identifier records that lack names but help identifier reports."""
    records = []
    payload = cache.get(f"{SEC_BASE}/files/company_tickers_mf.json")
    for row in rows_from_sec_table(payload):
        ticker = normalize_ticker(row.get("symbol"))
        if not ticker:
            continue
        records.append(
            SourceRecord(
                ticker=ticker,
                name="",
                source="company_tickers_mf",
                security_types=frozenset({"etfs", "funds", "moneymarkets"}),
                cik=clean_text(row.get("cik")),
                series_id=clean_text(row.get("seriesId")),
                class_id=clean_text(row.get("classId")),
                identifiers=frozenset(
                    value
                    for value in (
                        clean_text(row.get("seriesId")).upper(),
                        clean_text(row.get("classId")).upper(),
                    )
                    if value
                ),
            )
        )
    return records


def ncen_quarters(start_year: int, end_year: int) -> Iterable[str]:
    """Yield N-CEN quarter labels from 2018 Q3 onward."""
    for year in range(start_year, end_year + 1):
        first_quarter = FIRST_NCEN_QUARTER if year == FIRST_NCEN_YEAR else 1
        for quarter in range(first_quarter, 5):
            yield f"{year}q{quarter}"


def load_ncen_records(cache: SecCache, quarters: Iterable[str]) -> list[SourceRecord]:
    """Load ETF and fund records from SEC Form N-CEN quarterly zips."""
    records = []
    for quarter in quarters:
        url = f"{SEC_BASE}/files/dera/data/form-n-cen-data-sets/{quarter}_ncen.zip"
        try:
            payload = cache.get(url)
        except requests.HTTPError:
            continue
        with zipfile.ZipFile(io.BytesIO(payload)) as archive:
            if "SECURITY_EXCHANGE.tsv" in archive.namelist() and "FUND_REPORTED_INFO.tsv" in archive.namelist():
                records.extend(load_ncen_etf_records(archive, quarter))
    return records


def load_ncen_etf_records(archive: zipfile.ZipFile, quarter: str) -> list[SourceRecord]:
    """Load ETF ticker/name rows from one N-CEN zip."""
    fund_names = {}
    fund_payload = archive.read("FUND_REPORTED_INFO.tsv").decode("utf-8-sig")
    for row in csv.DictReader(io.StringIO(fund_payload), delimiter="\t"):
        fund_id = clean_text(row.get("FUND_ID"))
        fund_name = clean_text(row.get("FUND_NAME"))
        series_id = clean_text(row.get("SERIES_ID"))
        if fund_id and fund_name:
            fund_names[fund_id] = (fund_name, series_id)

    records = []
    exchange_payload = archive.read("SECURITY_EXCHANGE.tsv").decode("utf-8-sig")
    for row in csv.DictReader(io.StringIO(exchange_payload), delimiter="\t"):
        ticker = normalize_ticker(row.get("FUND_TICKER_SYMBOL"))
        fund_id = clean_text(row.get("FUND_ID"))
        fund_name, series_id = fund_names.get(fund_id, ("", ""))
        if not ticker or not fund_name:
            continue
        records.append(
            SourceRecord(
                ticker=ticker,
                name=fund_name,
                source=f"ncen_{quarter}",
                security_types=frozenset({"etfs", "funds"}),
                exchange=clean_text(row.get("FUND_EXCHANGE")),
                series_id=series_id,
                identifiers=frozenset({series_id.upper()} if series_id else set()),
            )
        )
    return records


def build_source_index(records: Iterable[SourceRecord]) -> dict[str, list[SourceRecord]]:
    """Build a ticker -> records index, dropping nameless records when named records exist."""
    index: dict[str, list[SourceRecord]] = {}
    for record in records:
        if record.ticker:
            index.setdefault(record.ticker, []).append(record)

    compacted = {}
    for ticker, ticker_records in index.items():
        named = [record for record in ticker_records if record.name]
        compacted[ticker] = named or ticker_records
    return compacted


def enrich_dataset(path: str | Path, source_index: dict[str, list[SourceRecord]], apply: bool) -> list[dict[str, str]]:
    """Create enrichment decisions for one dataset and optionally update it."""
    dataset = dataset_kind(path)
    dataframe = pd.read_csv(path, dtype=str, keep_default_na=False)
    report_rows = []
    changed = False

    for index, row in dataframe.iterrows():
        symbol = normalize_ticker(row.get("symbol"))
        decision = choose_candidate(row, source_index.get(symbol, []), dataset)
        if decision.status == "accepted" and apply:
            if decision.proposed_name:
                dataframe.loc[index, "name"] = decision.proposed_name
                changed = True
            if decision.proposed_currency:
                dataframe.loc[index, "currency"] = decision.proposed_currency
                changed = True

        if decision.status != "skipped":
            report_rows.append(
                {
                    "dataset": str(path),
                    "symbol": symbol,
                    "status": decision.status,
                    "proposed_name": decision.proposed_name,
                    "proposed_currency": decision.proposed_currency,
                    "source": decision.source,
                    "source_identifiers": decision.source_identifiers,
                    "confidence": decision.confidence,
                    "reason": decision.reason,
                }
            )

    if changed:
        dataframe.to_csv(path, index=False)
    return report_rows


def write_report(path: str | Path, rows: list[dict[str, str]]) -> None:
    """Write the enrichment audit report."""
    report_path = Path(path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    dataframe = pd.DataFrame(
        rows,
        columns=[
            "dataset",
            "symbol",
            "status",
            "proposed_name",
            "proposed_currency",
            "source",
            "source_identifiers",
            "confidence",
            "reason",
        ],
    )
    dataframe.to_csv(report_path, index=False)


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="Enrich missing US names/currencies from SEC public data.")
    parser.add_argument("--datasets", nargs="+", default=list(DEFAULT_DATASETS), help="CSV datasets to inspect.")
    parser.add_argument("--cache-dir", default=".cache/sec_enrichment", help="SEC download cache directory.")
    parser.add_argument("--report", default=".cache/sec_enrichment/sec_enrichment_report.csv", help="Audit report path.")
    parser.add_argument("--apply", action="store_true", help="Apply accepted high-confidence fills to CSV files.")
    parser.add_argument("--user-agent", default=os.getenv("SEC_USER_AGENT", ""), help="SEC-compliant User-Agent.")
    parser.add_argument("--start-year", type=int, default=2010, help="First series/class year to download.")
    parser.add_argument("--end-year", type=int, default=date.today().year, help="Last series/class year to download.")
    parser.add_argument("--include-ncen", action=argparse.BooleanOptionalAction, default=True, help="Include N-CEN data.")
    return parser.parse_args()


def main() -> None:
    """Run SEC enrichment."""
    args = parse_args()
    cache = SecCache(args.cache_dir, args.user_agent)
    years = range(args.start_year, args.end_year + 1)

    records = []
    records.extend(load_company_records(cache))
    records.extend(load_mutual_fund_ticker_records(cache))
    records.extend(load_series_class_records(cache, years))
    if args.include_ncen:
        records.extend(load_ncen_records(cache, ncen_quarters(2018, args.end_year)))

    source_index = build_source_index(records)
    report_rows = []
    for dataset_path in args.datasets:
        report_rows.extend(enrich_dataset(dataset_path, source_index, args.apply))

    write_report(args.report, report_rows)
    accepted = sum(row["status"] == "accepted" for row in report_rows)
    review = sum(row["status"] == "review" for row in report_rows)
    mode = "applied" if args.apply else "dry-run"
    print(f"SEC enrichment {mode}: {accepted} accepted, {review} review rows. Report: {args.report}")


if __name__ == "__main__":
    main()
