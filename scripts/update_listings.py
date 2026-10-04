"""Add newly listed equities and ETFs from official exchange symbol directories.

Run weekly by `.github/workflows/database_update.yml` (Add-New-Ticker job) and locally with

    python scripts/update_listings.py [--dry-run] [--database database]

Sources (all public, official):

- Nasdaq Trader symbol directory: US-listed ETFs (US equities are added by the workflow's
  own NASDAQ/NYSE/AMEX step).
- HKEX List of Securities: Hong Kong equities, REITs and ETPs (HKD counters).
- NSE equity and ETF lists: India.
- JPX list of TSE-listed issues: Japan equities and ETFs.
- ASX listed companies: Australia equities with their GICS industry group.
- TSX / TSXV company directory: Canada equities and ETFs.

Safety rules, so an automated run never adds junk or duplicates:

- Each source is fetched, parsed and applied on its own. A blocked download (bot check, rate
  limit, HTTP error, timeout), a format change, a suspiciously short list or an unexpected
  error skips that source only: its partial changes are rolled back and the other sources
  continue. Enrichment failures (OpenFIGI, optional lists) only mean fewer filled fields.
  An error outside the sources writes nothing and still exits cleanly, so this script can
  never fail the weekly pipeline (the workflow step is also `continue-on-error`).
- Rows are only ever added; nothing is removed. A symbol is added only when it exists in no
  asset class at all (no cross-asset collisions).
- A candidate is skipped when an existing row in the same exchange file has the same symbol
  apart from separators (`HCO.P.V` vs `HCO-P.V`) and the same company name.
- Ticker changes: when a new listing matches a live existing row in the same exchange file by
  ISIN or company name, and that row's symbol is no longer on the exchange's official list,
  the old row is marked `delisted=True`. More than `MAX_DELISTINGS_PER_SOURCE` such changes
  for one source is treated as a parsing problem and no rows are delisted for that source.
- Values the source does not provide are left blank, never guessed.

Enrichment of new rows (each step is optional: if it fails, rows are still added):

- OpenFIGI (open FIGI standard, https://www.openfigi.com): FIGI, composite FIGI and share-class
  FIGI for new equities, and the full instrument name for HKEX rows (HKEX only publishes
  abbreviations) when OpenFIGI's name is complete (its names are cut at 28 characters). A row
  whose OpenFIGI security type contradicts its asset class (an ETP among equities, a common
  stock among ETFs) is not added. Set OPENFIGI_API_KEY for higher rate limits.
- Sector / industry group / industry from the exchange's own classification (JPX 33 sectors,
  NSE Nifty Total Market industries), translated through the existing rows of the same file:
  a level is filled only when >= 90% of >= 10 existing rows with that classification agree.
- ETF family (issuer) from the first words of the name, when >= 95% of existing ETFs with the
  same opening words belong to one family.
"""

from __future__ import annotations

import argparse
import glob
import io
import json
import os
import re
import time
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass, field

import pandas as pd
import requests

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    )
}
TIMEOUT = 120
MAX_DELISTINGS_PER_SOURCE = 50
OPENFIGI_URL = "https://api.openfigi.com/v3/mapping"
# Database suffix -> OpenFIGI exchange code (Hong Kong, Tokyo, NSE, ASX, TSX, TSXV).
FIGI_EXCHANGES = {
    ".HK": "HK",
    ".T": "JT",
    ".NS": "IS",
    ".AX": "AT",
    ".TO": "CT",
    ".V": "CV",
}
MIN_AGREEMENT, MIN_ROWS = 0.9, 10
US_ETF_FILES = {"NMS", "NGM", "NCM", "NYQ", "ASE", "PCX", "BTS"}

# Exchange suffixes used by the sources below, kept when comparing symbol formats.
SUFFIX = r"\.(?:TO|V|HK|NS|T|AX)$"
NAME_STOPWORDS = (
    r"\b(inc|incorporated|corp|corporation|ltd|limited|plc|co|company|holdings?|group|"
    r"sa|ag|nv|se|the|class [a-z]|common stock|ordinary shares|shares|stock|llc|lp)\b"
)


@dataclass
class Listing:
    """One listed instrument as published by an exchange."""

    kind: str  # "equities" or "etfs"
    file: str  # exchange file, e.g. "HKG" -> database/<kind>/HKG.csv
    symbol: str
    name: str
    currency: str
    isin: str = ""
    country: str = ""
    sector: str = ""
    industry_group: str = ""
    industry: str = ""
    mic: str = ""
    classification: str = ""  # the exchange's own sector label, e.g. JPX "Banks"
    figi: str = ""
    composite_figi: str = ""
    shareclass_figi: str = ""


@dataclass
class SourceResult:
    """Parsed source: listings to consider adding and every symbol currently listed."""

    listings: list[Listing] = field(default_factory=list)
    official: dict[str, set[str]] = field(default_factory=dict)
    # exchange file -> {symbol: exchange sector label} for every listed symbol, used to learn
    # how the exchange's classification translates to the database's categories.
    classifications: dict[str, dict[str, str]] = field(default_factory=dict)


# --------------------------------------------------------------------------- helpers


def fetch(url: str) -> bytes:
    """Download a URL with a browser user agent; raises on HTTP errors."""
    response = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
    response.raise_for_status()
    return response.content


def fetch_nasdaq_trader(name: str) -> bytes:
    """Nasdaq Trader symbol directory file over HTTPS, falling back to its official FTP copy.

    The HTTPS endpoint sometimes answers automated clients with a bot-check page instead.
    """
    try:
        content = fetch(f"https://www.nasdaqtrader.com/dynamic/SymDir/{name}.txt")
        if b"|" in content.split(b"\n", 1)[0]:
            return content
    except requests.RequestException:
        pass
    url = f"ftp://ftp.nasdaqtrader.com/symboldirectory/{name}.txt"
    with urllib.request.urlopen(
        url, timeout=TIMEOUT
    ) as response:  # noqa: S310 (fixed URL)
        return response.read()


def optional_fetch(url: str) -> bytes | None:
    """Download an enrichment-only file; a failure just means less enrichment."""
    try:
        return fetch(url)
    except Exception as error:  # enrichment only: never fatal
        print(f"  optional download failed ({url}): {type(error).__name__}: {error}")
        return None


def require(condition: bool, message: str) -> None:
    """Abort the current source when its data does not look like the expected format."""
    if not condition:
        raise ValueError(message)


def read_csv_text(path: str) -> pd.DataFrame:
    """Read a database CSV as text, keeping values like the ticker 'NA' intact."""
    return pd.read_csv(path, index_col=0, dtype=str, keep_default_na=False)


def normalise_name(name: str) -> str:
    """Company name reduced to its distinctive words, for duplicate detection."""
    name = re.sub(r"\(.*?\)", " ", name.lower())
    name = re.sub(r"[^a-z0-9 ]", " ", name)
    return re.sub(r"\s+", " ", re.sub(NAME_STOPWORDS, " ", name)).strip()


def symbol_key(symbol: str) -> str:
    """Symbol without separators, keeping the exchange suffix (HCO.P.V == HCO-P.V)."""
    match = re.search(SUFFIX, symbol)
    suffix = match.group(0) if match else ""
    return re.sub(r"[-.^/]", "", symbol[: len(symbol) - len(suffix)]) + suffix


def yahoo_canada(symbol: str) -> str:
    """TSX symbol to the database's Yahoo-style form.

    'BCE.PR.A' -> 'BCE-PA', 'TD.PF.A' -> 'TD-PFA', 'GASX.WT.A' -> 'GASX-WTA', 'AD.UN' -> 'AD-UN'.
    """
    base, _, rest = symbol.partition(".")
    if not rest:
        return base
    if rest.startswith("PR."):
        rest = "P" + rest[3:]
    return base + "-" + rest.replace(".", "")


def canada_name(company: str, symbol: str) -> str:
    """Company name for the primary instrument; other classes and series name the instrument."""
    if "." not in symbol or symbol.split(".", 1)[1] in ("P", "H"):
        return (
            company  # TSXV capital pool (.P) and NEX (.H) listings are the only listing
        )
    kind = symbol.split(".", 1)[1]
    if kind.startswith(("PR.", "PF.")):
        return f"{company} Preferred Shares ({symbol})"
    label = {
        "U": "USD",
        "UN": "Units",
        "WT": "Warrants",
        "A": "Class A",
        "B": "Class B",
    }
    text = "Warrants" if kind.startswith("WT.") else label.get(kind)
    return f"{company} {text} ({symbol})" if text else f"{company} ({symbol})"


# --------------------------------------------------------------------------- sources


def parse_nasdaq_trader(nasdaq_listed: bytes, other_listed: bytes) -> SourceResult:
    """US ETFs from the Nasdaq Trader symbol directory."""
    result = SourceResult()
    read = lambda b: pd.read_csv(  # noqa: E731
        io.BytesIO(b), sep="|", dtype=str, keep_default_na=False
    )
    nasdaq, other = read(nasdaq_listed), read(other_listed)
    require({"Symbol", "ETF", "Market Category"} <= set(nasdaq.columns), "nasdaqlisted")
    require({"NASDAQ Symbol", "ETF", "Exchange"} <= set(other.columns), "otherlisted")
    require(len(nasdaq) > 3000 and len(other) > 5000, "symbol directory too short")
    nasdaq = nasdaq[~nasdaq["Symbol"].str.startswith("File Creation")]
    other = other[~other["NASDAQ Symbol"].str.startswith("File Creation")]
    listed = (
        set(nasdaq["Symbol"]) | set(other["NASDAQ Symbol"]) | set(other["ACT Symbol"])
    )
    result.official = {f: listed for f in US_ETF_FILES}

    tiers = {"Q": "NMS", "G": "NGM", "S": "NCM"}
    for _, row in nasdaq[
        (nasdaq["Test Issue"] == "N") & (nasdaq.ETF == "Y")
    ].iterrows():
        if row["Market Category"] in tiers:
            result.listings.append(
                Listing(
                    "etfs",
                    tiers[row["Market Category"]],
                    row.Symbol,
                    row["Security Name"].strip(),
                    "USD",
                )
            )
    exchanges = {"N": "NYQ", "A": "ASE", "P": "PCX", "Z": "BTS"}
    for _, row in other[(other["Test Issue"] == "N") & (other.ETF == "Y")].iterrows():
        symbol = row["NASDAQ Symbol"]
        if row.Exchange in exchanges and re.fullmatch(r"[A-Z]+", symbol):
            result.listings.append(
                Listing(
                    "etfs",
                    exchanges[row.Exchange],
                    symbol,
                    row["Security Name"].strip(),
                    "USD",
                )
            )
    return result


def parse_hkex(xlsx: bytes) -> SourceResult:
    """Hong Kong equities, REITs and ETPs traded in HKD."""
    result = SourceResult()
    data = pd.read_excel(io.BytesIO(xlsx), header=2, dtype=str).fillna("")
    require(
        {"Stock Code", "Name of Securities", "Category", "ISIN"} <= set(data.columns),
        "HKEX",
    )
    require(len(data) > 5000, "HKEX list too short")
    data["code"] = data["Stock Code"].astype(int)
    result.official = {"HKG": {f"{code:04d}.HK" for code in data["code"]}}
    data = data[(data["Trading Currency"] == "HKD") & (data["RMB Counter"] == "")]
    # 2900-2999 are temporary parallel-trading counters (share consolidations, board-lot
    # changes, rights) that duplicate a company's main stock code.
    data = data[~data["code"].between(2900, 2999)]
    for _, row in data.iterrows():
        symbol, isin = f"{row.code:04d}.HK", row.ISIN.strip()
        name = row["Name of Securities"].strip()
        if row.Category in ("Equity", "Real Estate Investment Trusts"):
            country = "Hong Kong" if isin.startswith("HK") else ""
            result.listings.append(
                Listing("equities", "HKG", symbol, name, "HKD", isin, country)
            )
        elif row.Category == "Exchange Traded Products":
            result.listings.append(
                Listing("etfs", "HKG", symbol, name, "HKD", isin, mic="XHKG")
            )
    return result


def parse_nse(
    equity_csv: bytes, etf_csv: bytes, industries_csv: bytes | None = None
) -> SourceResult:
    """India: NSE main-board equities and ETFs (industries from the Nifty Total Market list)."""
    result = SourceResult()
    industries: dict[str, str] = {}
    if industries_csv:
        nifty = pd.read_csv(
            io.BytesIO(industries_csv), dtype=str, keep_default_na=False
        )
        if {"Symbol", "Industry"} <= set(nifty.columns):
            industries = {
                f"{s.strip()}.NS": i.strip()
                for s, i in zip(nifty.Symbol, nifty.Industry)
            }
    result.classifications = {"NSE": industries}
    equities = pd.read_csv(io.BytesIO(equity_csv), dtype=str, keep_default_na=False)
    equities.columns = [c.strip() for c in equities.columns]
    etfs = pd.read_csv(io.BytesIO(etf_csv), dtype=str, keep_default_na=False)
    require(
        {"SYMBOL", "NAME OF COMPANY", "SERIES", "ISIN NUMBER"} <= set(equities.columns),
        "NSE",
    )
    require({"Symbol", "SecurityName", "ISINNumber"} <= set(etfs.columns), "NSE ETF")
    require(len(equities) > 1500 and len(etfs) > 100, "NSE lists too short")
    result.official = {
        "NSE": {f"{s.strip()}.NS" for s in equities.SYMBOL}
        | {f"{s.strip()}.NS" for s in etfs.Symbol}
    }
    for _, row in equities[
        equities.SERIES.str.strip().isin(["EQ", "BE", "BZ"])
    ].iterrows():
        isin = row["ISIN NUMBER"].strip()
        result.listings.append(
            Listing(
                "equities",
                "NSE",
                f"{row.SYMBOL.strip()}.NS",
                row["NAME OF COMPANY"].strip(),
                "INR",
                isin,
                "India" if isin.startswith("IN") else "",
                classification=industries.get(f"{row.SYMBOL.strip()}.NS", ""),
            )
        )
    for _, row in etfs.iterrows():
        underlying = row.get("Underlying Asset", "").strip()
        name = underlying if "ETF" in underlying else row.SecurityName.strip()
        result.listings.append(
            Listing(
                "etfs",
                "NSE",
                f"{row.Symbol.strip()}.NS",
                name,
                "INR",
                row.ISINNumber.strip(),
                mic="XNSE",
            )
        )
    return result


def parse_jpx(xlsx: bytes) -> SourceResult:
    """Japan: TSE Prime/Standard/Growth equities and ETFs/ETNs."""
    result = SourceResult()
    data = pd.read_excel(io.BytesIO(xlsx), dtype=str).fillna("")
    require(
        {"Local Code", "Name (English)", "Section/Products"} <= set(data.columns), "JPX"
    )
    require(len(data) > 3000, "JPX list too short")
    result.official = {"JPX": {f"{c}.T" for c in data["Local Code"]}}
    sectors = data.get("33 Sector(name)", pd.Series("", index=data.index))
    sectors = sectors.where(sectors.str.strip() != "-", "")
    result.classifications = {"JPX": dict(zip(data["Local Code"] + ".T", sectors))}
    for _, row in data.iterrows():
        section, symbol = row["Section/Products"], f"{row['Local Code']}.T"
        name = row["Name (English)"].strip()
        if re.search(r"(Prime|Standard|Growth) Market", section):
            country = "Japan" if "Domestic" in section else ""
            result.listings.append(
                Listing(
                    "equities",
                    "JPX",
                    symbol,
                    name,
                    "JPY",
                    country=country,
                    classification=result.classifications["JPX"][symbol],
                )
            )
        elif section.startswith("ETFs"):
            result.listings.append(Listing("etfs", "JPX", symbol, name, "JPY"))
    return result


def parse_asx(csv: bytes, group_sector: dict[str, str]) -> SourceResult:
    """Australia: ASX companies with a GICS industry group (rows without one are skipped)."""
    result = SourceResult()
    data = pd.read_csv(io.BytesIO(csv), skiprows=2, dtype=str, keep_default_na=False)
    require(
        {"Company name", "ASX code", "GICS industry group"} <= set(data.columns), "ASX"
    )
    require(len(data) > 1500, "ASX list too short")
    result.official = {"ASX": {f"{c}.AX" for c in data["ASX code"]}}
    aliases = {
        "Consumer Discretionary Distribution & Retail": "Retailing",
        "Consumer Staples Distribution & Retail": "Food & Staples Retailing",
        "Financial Services": "Diversified Financials",
        "Equity Real Estate Investment Trusts (REITs)": "Real Estate",
        "Real Estate Management & Development": "Real Estate",
    }
    for _, row in data.iterrows():
        group = aliases.get(row["GICS industry group"], row["GICS industry group"])
        if (
            group in group_sector
        ):  # 'Not Applic' (ETPs, trusts) and 'Class Pend' are skipped
            result.listings.append(
                Listing(
                    "equities",
                    "ASX",
                    f"{row['ASX code']}.AX",
                    row["Company name"].strip(),
                    "AUD",
                    sector=group_sector[group],
                    industry_group=group,
                )
            )
    return result


def parse_tsx(tsx_json: bytes, tsxv_json: bytes) -> SourceResult:
    """Canada: TSX and TSXV equities, TSX ETFs."""
    result = SourceResult()
    for raw, file, suffix in [(tsx_json, "TOR", ".TO"), (tsxv_json, "VAN", ".V")]:
        companies = json.loads(raw)["results"]
        require(len(companies) > 1000, f"{file} directory too short")
        result.official[file] = {
            yahoo_canada(i["symbol"]) + suffix
            for c in companies
            for i in c["instruments"]
        }
        for company in companies:
            name = company["name"].strip()
            for instrument in company["instruments"]:
                symbol = instrument["symbol"]
                if re.search(r"\.(DB|NT|NO)(\.|$)", symbol):
                    continue  # debentures and notes are debt securities
                currency = "USD" if symbol.endswith(".U") else "CAD"
                listing_name = canada_name(name, symbol)
                ticker = yahoo_canada(symbol) + suffix
                if re.search(r"\bETF\b", name) and file == "TOR":
                    result.listings.append(
                        Listing("etfs", "TOR", ticker, listing_name, currency)
                    )
                elif not re.search(
                    r"\b(ETF|ETN|Fund)\b", name
                ):  # 'Fund': ETF or closed-end?
                    result.listings.append(
                        Listing("equities", file, ticker, listing_name, currency)
                    )
    return result


def jpx_download_url() -> str:
    """The JPX listed-issues file name changes over time; read it from the index page."""
    page = fetch(
        "https://www.jpx.co.jp/english/markets/statistics-equities/misc/01.html"
    ).decode()
    match = re.search(r'href="([^"]*/data_e\.xlsx?)"', page)
    require(match is not None, "JPX download link not found")
    return "https://www.jpx.co.jp" + match.group(1)


def load_sources(group_sector: dict[str, str]) -> dict[str, Callable[[], SourceResult]]:
    """Source name -> loader. Loaders download and parse lazily so one failure stays isolated."""
    tsx = "https://www.tsx.com/json/company-directory/search/{}/%5E*"
    nse = "https://archives.nseindia.com/content/equities/{}"
    return {
        "Nasdaq Trader (US ETFs)": lambda: parse_nasdaq_trader(
            fetch_nasdaq_trader("nasdaqlisted"), fetch_nasdaq_trader("otherlisted")
        ),
        "HKEX": lambda: parse_hkex(
            fetch(
                "https://www.hkex.com.hk/eng/services/trading/securities/securitieslists/ListOfSecurities.xlsx"
            )
        ),
        "NSE": lambda: parse_nse(
            fetch(nse.format("EQUITY_L.csv")),
            fetch(nse.format("eq_etfseclist.csv")),
            optional_fetch(
                "https://archives.nseindia.com/content/indices/ind_niftytotalmarket_list.csv"
            ),
        ),
        "JPX": lambda: parse_jpx(fetch(jpx_download_url())),
        "ASX": lambda: parse_asx(
            fetch("https://www.asx.com.au/asx/research/ASXListedCompanies.csv"),
            group_sector,
        ),
        "TSX/TSXV": lambda: parse_tsx(
            fetch(tsx.format("tsx")), fetch(tsx.format("tsxv"))
        ),
    }


# --------------------------------------------------------------------------- enrichment


def learn_categories(
    frame: pd.DataFrame, labels: dict[str, str]
) -> dict[str, dict[str, str]]:
    """Exchange sector label -> database categories, learned from existing rows.

    For each label, the deepest of sector / industry_group / industry is used on which
    >= MIN_AGREEMENT of >= MIN_ROWS existing rows with that label agree.
    """
    levels = ["sector", "industry_group", "industry"]
    known = frame[(frame["sector"] != "") & frame.index.isin(list(labels))]
    known = known.assign(label=[labels[s] for s in known.index])
    known = known[known.label != ""]
    mapping: dict[str, dict[str, str]] = {}
    for label, group in known.groupby("label"):
        if len(group) < MIN_ROWS:
            continue
        chosen: dict[str, str] = {}
        for depth in range(1, 4):
            prefix = group[levels[:depth]].apply(tuple, axis=1)
            counts = prefix.value_counts()
            if counts.iloc[0] / len(group) < MIN_AGREEMENT or "" in counts.index[0]:
                break
            chosen = dict(zip(levels[:depth], counts.index[0]))
        if chosen:
            mapping[label] = chosen
    return mapping


def figi_job(listing: Listing) -> tuple[dict, str] | None:
    """OpenFIGI mapping job and the ticker expected back, or None when not mappable."""
    match = re.search(SUFFIX, listing.symbol)
    if not match or match.group(0) not in FIGI_EXCHANGES:
        return None
    exchange, base = FIGI_EXCHANGES[match.group(0)], listing.symbol[: match.start()]
    if exchange == "HK":
        base = str(int(base))  # OpenFIGI uses Hong Kong codes without leading zeros
    elif exchange in ("CT", "CV"):
        if base.endswith("-UN"):
            base = base[:-3] + "-U"  # trust units
        elif "-" in base:
            return None  # preferreds, warrants and other classes are not resolvable by ticker
    if listing.isin and exchange in ("HK", "IS"):
        return {
            "idType": "ID_ISIN",
            "idValue": listing.isin,
            "exchCode": exchange,
        }, base
    return {"idType": "TICKER", "idValue": base, "exchCode": exchange}, base


def openfigi_lookup(
    jobs: list[tuple[dict, str]], api_key: str | None
) -> list[dict | None]:
    """Resolve mapping jobs in rate-limited batches; returns the matching record per job."""
    batch, pause = (100, 0.25) if api_key else (10, 2.5)
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["X-OPENFIGI-APIKEY"] = api_key
    found: list[dict | None] = []
    for start in range(0, len(jobs), batch):
        chunk = jobs[start : start + batch]
        for attempt in range(6):
            response = requests.post(
                OPENFIGI_URL,
                json=[j for j, _ in chunk],
                headers=headers,
                timeout=TIMEOUT,
            )
            if response.status_code != 429:
                break
            time.sleep(10 * (attempt + 1))  # rate limited: back off and retry
        response.raise_for_status()
        for (_, ticker), answer in zip(chunk, response.json()):
            data = answer.get("data") or []
            exact = [d for d in data if d.get("ticker") == ticker]
            found.append((exact or data or [None])[0])
        time.sleep(pause)
    return found


def openfigi_name(record: dict) -> str:
    """OpenFIGI's name when complete: its names are cut at 28 characters."""
    name = (record.get("name") or "").strip()
    tag = re.search(r"\s+-(HKD|USD|RMB|CNY)$", name)
    if tag:
        return name[: tag.start()].strip()
    return name if len(name) < 28 else ""


def enrich_with_openfigi(
    listings: list[Listing], api_key: str | None
) -> tuple[list[Listing], list[str]]:
    """Fill FIGIs (and full HKEX names); drop rows whose security type contradicts the asset class."""
    jobs = [(listing, figi_job(listing)) for listing in listings]
    jobs = [(listing, job) for listing, job in jobs if job]
    if not jobs:
        return listings, []
    try:
        records = openfigi_lookup([job for _, job in jobs], api_key)
    except Exception as error:  # blocked, rate limited, changed format: enrichment only
        print(
            f"  OpenFIGI unavailable, rows added without FIGIs: {type(error).__name__}: {error}"
        )
        return listings, []
    rejected = set()
    notes = []
    for (listing, _), record in zip(jobs, records):
        if not record:
            continue
        kind = record.get("securityType", "")
        if (listing.kind == "equities" and kind == "ETP") or (
            listing.kind == "etfs" and kind == "Common Stock"
        ):
            rejected.add(listing.symbol)
            notes.append(f"{listing.symbol} ({listing.kind} but OpenFIGI type {kind})")
            continue
        if listing.kind == "equities":
            listing.figi = record.get("figi") or ""
            listing.composite_figi = record.get("compositeFIGI") or ""
            listing.shareclass_figi = record.get("shareClassFIGI") or ""
        if listing.file == "HKG" and openfigi_name(record):
            listing.name = openfigi_name(record)
    return [x for x in listings if x.symbol not in rejected], notes


# --------------------------------------------------------------------------- database update


class Database:
    """The per-exchange equities/ETF files plus the symbols of every asset class."""

    def __init__(self, root: str) -> None:
        self.root = root
        self.frames: dict[str, pd.DataFrame] = {}
        self.added: dict[str, list[pd.Series]] = {}
        self.cache: dict[tuple[str, str], dict] = {}
        self.symbols: set[str] = set()
        for path in glob.glob(f"{root}/*/*.csv") + glob.glob(f"{root}/*.csv"):
            self.symbols |= set(
                pd.read_csv(path, usecols=[0], dtype=str, keep_default_na=False).iloc[
                    :, 0
                ]
            )
        self.columns = {
            kind: read_csv_text(
                sorted(glob.glob(f"{root}/{kind}/*.csv"))[0]
            ).columns.tolist()
            for kind in ("equities", "etfs")
        }

    def frame(self, kind: str, file: str) -> pd.DataFrame:
        path = self.path(kind, file)
        if path not in self.frames:
            columns = self.columns[kind]
            empty = pd.DataFrame(columns=columns, dtype=str).rename_axis("symbol")
            self.frames[path] = read_csv_text(path) if os.path.exists(path) else empty
            self.added[path] = []
        return self.frames[path]

    def path(self, kind: str, file: str) -> str:
        return f"{self.root}/{kind}/{file}.csv"

    def symbol_keys(self, kind: str, file: str) -> dict[str, str]:
        """Separator-free symbol -> symbol for an exchange file (cached)."""
        if (kind + "keys", file) not in self.cache:
            frame = self.frame(kind, file)
            self.cache[(kind + "keys", file)] = {symbol_key(s): s for s in frame.index}
        return self.cache[(kind + "keys", file)]

    def live_by_name(self, kind: str, file: str) -> dict[str, list[str]]:
        """Normalised name -> live symbols for an exchange file (cached)."""
        if (kind + "names", file) not in self.cache:
            frame = self.frame(kind, file)
            names: dict[str, list[str]] = {}
            for symbol, name in frame.loc[frame["delisted"] == "False", "name"].items():
                names.setdefault(normalise_name(name), []).append(symbol)
            self.cache[(kind + "names", file)] = names
        return self.cache[(kind + "names", file)]

    def defaults(self, kind: str, file: str) -> dict[str, str]:
        """mic / market of an exchange file, from its existing rows."""
        frame = self.frame(kind, file)
        mode = lambda col: (  # noqa: E731
            frame[col][frame[col] != ""].mode().iloc[0]
            if col in frame and (frame[col] != "").any()
            else ""
        )
        return {"mic": mode("mic"), "market": mode("market")}

    def group_sector(self) -> dict[str, str]:
        """GICS industry group -> sector as used in the equities files."""
        frames = [
            read_csv_text(p)[["sector", "industry_group"]]
            for p in glob.glob(f"{self.root}/equities/*.csv")
        ]
        pairs = pd.concat(frames)
        pairs = pairs[(pairs.sector != "") & (pairs.industry_group != "")]
        return (
            pairs.groupby("industry_group")
            .sector.agg(lambda s: s.mode().iloc[0])
            .to_dict()
        )

    def etf_families(self) -> Callable[[str], str]:
        """Issuer family from the opening words of an ETF name.

        The first two words are used when >= 95% of >= 5 existing ETFs starting with them
        share one family, otherwise the first word with >= 95% of >= 10 ETFs (or all of >= 3).
        Matching ignores case, so upper-case exchange names ('ISHARES CHINA') match too.
        """
        frames = [
            read_csv_text(p)[["name", "family"]]
            for p in glob.glob(f"{self.root}/etfs/*.csv")
        ]
        etfs = pd.concat(frames)
        etfs = etfs[etfs.family != ""]
        tables = []
        for words, minimum in ((2, 5), (1, 10)):
            key = lambda name, n=words: " ".join(name.lower().split()[:n])  # noqa: E731
            table = {}
            for prefix, group in etfs.groupby(etfs.name.map(key)):
                counts = group.family.value_counts()
                share = counts.iloc[0] / len(group)
                unanimous = words == 1 and len(group) >= 3 and share == 1
                if (len(group) >= minimum and share >= 0.95) or unanimous:
                    table[prefix] = counts.index[0]
            tables.append((key, table))

        def family(name: str) -> str:
            for key, table in tables:
                if key(name) in table:
                    return table[key(name)]
            return ""

        return family

    def write(self) -> None:
        for path, original in self.frames.items():
            if not self.added[path] and not original.attrs.get("changed"):
                continue
            out = original
            if self.added[path]:
                new_rows = pd.DataFrame(self.added[path])[original.columns]
                out = pd.concat([original, new_rows])
            # Equities files are kept sorted by symbol (the US-ticker step rewrites them sorted);
            # ETF files keep their order unless they were already sorted.
            if "/equities/" in path or original.index.is_monotonic_increasing:
                out = out.sort_index()
            out.index.name = "symbol"
            out.to_csv(path)


def apply_source(
    db: Database,
    name: str,
    result: SourceResult,
    family: Callable[[str], str],
    api_key: str | None = None,
    use_openfigi: bool = True,
) -> dict:
    """Add a source's new listings and delist superseded tickers. Returns a summary."""
    added, skipped_format, delist = [], [], []
    seen = set()
    for listing in result.listings:
        if listing.symbol in db.symbols or listing.symbol in seen:
            continue
        seen.add(listing.symbol)
        frame = db.frame(listing.kind, listing.file)
        existing = db.symbol_keys(listing.kind, listing.file).get(
            symbol_key(listing.symbol)
        )
        if existing and re.search(SUFFIX, listing.symbol):
            a, b = normalise_name(frame.loc[existing, "name"]), normalise_name(
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
        file: learn_categories(db.frame("equities", file), labels)
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
        if (
            listing.file not in official_keys_by_file
        ):  # per source: lists differ by source
            official_keys_by_file[listing.file] = {symbol_key(s) for s in official}
        official_keys = official_keys_by_file[listing.file]
        frame = db.frame(listing.kind, listing.file)
        key = normalise_name(listing.name)
        matches = (
            set(db.live_by_name(listing.kind, listing.file).get(key, []))
            if key
            else set()
        )
        if listing.isin:
            live = frame[frame["delisted"] == "False"]
            matches |= set(live.index[live["isin"] == listing.isin])
        for old in sorted(matches):
            if old not in official and symbol_key(old) not in official_keys:
                delist.append((listing.kind, listing.file, old, listing.symbol))

    if len(delist) > MAX_DELISTINGS_PER_SOURCE:
        print(
            f"  ! {len(delist)} ticker changes look implausible; not delisting anything for {name}"
        )
        delist = []
    for kind, file, old, new in delist:
        frame = db.frame(kind, file)
        frame.loc[old, "delisted"] = "True"
        frame.attrs["changed"] = True

    for listing in added:
        frame = db.frame(listing.kind, listing.file)
        defaults = db.defaults(listing.kind, listing.file)
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
        db.added[db.path(listing.kind, listing.file)].append(
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
) -> list[str]:
    """Update the database from every source; returns the names of skipped sources.

    A source that cannot be downloaded (blocked, rate limited, offline), no longer has the
    expected format, or fails while being applied is skipped: its partial changes are rolled
    back and the other sources continue.
    """
    db = Database(database)
    family = db.etf_families()
    if sources is None:
        sources = load_sources(db.group_sector())
    failures = []
    for name, load in sources.items():
        added_before = {path: len(rows) for path, rows in db.added.items()}
        delisted_before = {path: f["delisted"].copy() for path, f in db.frames.items()}
        symbols_before = set(db.symbols)
        try:
            result = load()
            summary = apply_source(db, name, result, family, api_key, use_openfigi)
        except Exception as error:  # one broken source must not stop the others
            for path in list(db.added):
                del db.added[path][added_before.get(path, 0) :]
            for path, column in delisted_before.items():
                db.frames[path]["delisted"] = column
            for path in [p for p in db.frames if p not in delisted_before]:
                del (
                    db.frames[path],
                    db.added[path],
                )  # first loaded by this source: reload later
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
            f"{len(summary['rejected'])} rejected on security type"
        )
        for note in summary["rejected"]:
            print(f"  not added: {note}")
        for kind, file, old, new in summary["delisted"]:
            print(f"  delisted {kind}/{file} {old} (now listed as {new})")
    if not dry_run:
        db.write()
    if failures:
        print(f"Sources skipped this run: {', '.join(failures)}")
    return failures


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
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
        )
    except Exception as error:  # never break the weekly pipeline; nothing is written
        print(f"Listings update skipped entirely ({type(error).__name__}: {error})")


if __name__ == "__main__":
    main()
