"""Enrichment Model"""

__docformat__ = "google"

import html
import json
import os
import re
import time
from typing import TYPE_CHECKING

import pandas as pd
import requests

from scripts.listings.helpers import SUFFIX, TIMEOUT, US_ETF_FILES
from scripts.listings.sources_model import Listing

if TYPE_CHECKING:
    from scripts.listings.database_model import Database

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
EXCHANGE_NAMES = {
    "NMS": "Nasdaq Global Select Market",
    "NGM": "Nasdaq Global Market",
    "NCM": "Nasdaq Capital Market",
    "NYQ": "New York Stock Exchange",
    "ASE": "NYSE American",
    "PCX": "NYSE Arca",
    "BTS": "Cboe BZX Exchange",
    "HKG": "Hong Kong Stock Exchange",
    "NSE": "National Stock Exchange of India",
    "JPX": "Tokyo Stock Exchange",
    "ASX": "Australian Securities Exchange",
    "TOR": "Toronto Stock Exchange",
    "VAN": "TSX Venture Exchange",
}


def learn_categories(
    frame: pd.DataFrame, labels: dict[str, str]
) -> dict[str, dict[str, str]]:
    """
    Exchange sector label -> database categories, learned from existing rows.

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


def create_figi_job(listing: Listing) -> tuple[dict, str] | None:
    """
    OpenFIGI mapping job and the ticker expected back, or None when not mappable.
    """
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


def lookup_openfigi(
    jobs: list[tuple[dict, str]], api_key: str | None
) -> list[dict | None]:
    """
    Resolve mapping jobs in rate-limited batches; returns the matching record per job.
    """
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
            time.sleep(10 * (attempt + 1))
        response.raise_for_status()
        for (_, ticker), answer in zip(chunk, response.json()):
            data = answer.get("data") or []
            exact = [d for d in data if d.get("ticker") == ticker]
            found.append((exact or data or [None])[0])
        time.sleep(pause)
    return found


def get_openfigi_name(record: dict) -> str:
    """
    OpenFIGI's name when complete: its names are cut at 28 characters.
    """
    name = (record.get("name") or "").strip()
    tag = re.search(r"\s+-(HKD|USD|RMB|CNY)$", name)
    if tag:
        return name[: tag.start()].strip()
    return name if len(name) < 28 else ""


def enrich_with_openfigi(
    listings: list[Listing], api_key: str | None
) -> tuple[list[Listing], list[str]]:
    """
    Fill FIGIs (and full HKEX names); re-file rows whose security type contradicts the asset class.
    """
    jobs = [(listing, create_figi_job(listing)) for listing in listings]
    jobs = [(listing, job) for listing, job in jobs if job]
    if not jobs:
        return listings, []
    try:
        records = lookup_openfigi([job for _, job in jobs], api_key)
    except Exception as error:
        print(
            f"  OpenFIGI unavailable, rows added without FIGIs: {type(error).__name__}: {error}"
        )
        return listings, []
    notes = []
    for (listing, _), record in zip(jobs, records):
        if not record:
            continue
        kind = record.get("securityType", "")
        # The exchange lists some funds without "ETF" in the name (and the reverse): file the
        # row under the asset class its security type says, not the one the name suggested.
        if listing.kind == "equities" and kind == "ETP":
            listing.kind, listing.country, listing.sector = "etfs", "", ""
            listing.industry_group = listing.industry = ""
            notes.append(f"{listing.symbol} filed as ETF (OpenFIGI type {kind})")
        elif listing.kind == "etfs" and kind == "Common Stock":
            listing.kind = "equities"
            notes.append(f"{listing.symbol} filed as equity (OpenFIGI type {kind})")
        if listing.kind == "equities":
            listing.figi = record.get("figi") or ""
            listing.composite_figi = record.get("compositeFIGI") or ""
            listing.shareclass_figi = record.get("shareClassFIGI") or ""
        if listing.file == "HKG" and get_openfigi_name(record):
            listing.name = get_openfigi_name(record)
    return listings, notes


def create_factual_summary(symbol: str, row: dict[str, str], kind: str) -> str:
    """
    A summary stating only facts already in the row; nothing is inferred or invented.
    """
    exchange = EXCHANGE_NAMES.get(row.get("exchange", ""), "")
    if not row.get("name") or not exchange:
        return ""
    ticker = re.sub(SUFFIX, "", symbol)
    what = "an exchange-traded fund" if kind == "etfs" else "a company"
    text = f"{row['name']} is {what} listed on the {exchange} under the ticker {ticker}"
    text += f" and traded in {row['currency']}." if row.get("currency") else "."
    if kind == "etfs":
        if row.get("family"):
            text += f" The fund is part of the {row['family']} range."
        if row.get("category_group") and row.get("category"):
            text += f" It is classified as {row['category_group']} ({row['category']})."
    else:
        detail = row.get("industry") or row.get("industry_group")
        if row.get("sector"):
            text += f" It is classified in the {row['sector']} sector"
            text += f" ({detail})." if detail and detail != row["sector"] else "."
        if row.get("country"):
            text += f" Its country is {row['country']}."
    return text


# The section ends at the next heading. Case-sensitive on purpose: the objective itself often
# says "(before fees and expenses)", which must not end it.
SEC_END = (
    r"(?<!before )(?<!of )(?<!\()\b(?:Fees and Expenses|Fees & Expenses|Annual Fund Operating"
    r"|Shareholder Fees|Principal Investment Strateg\w*|FEES AND EXPENSES)\b"
)


def get_objective_window(document: str) -> str:
    """
    Plain text following the 'Investment Objective' heading (up to 3,000 characters).
    """
    text = html.unescape(re.sub(r"<[^>]+>", " ", document)).replace("\u00a0", " ")
    text = re.sub(r"\s+", " ", text)
    # Prefer the capitalised section heading; fall back to any mention of the phrase.
    match = re.search(r"Investment Objectives?\b\s*[.:]?\s*", text) or re.search(
        r"Investment Objectives?\b\s*[.:]?\s*", text, re.I
    )
    return text[match.end() : match.end() + 3000] if match else ""


def extract_objective(document: str, window: str | None = None) -> str:
    """
    The 'Investment Objective' paragraph of a summary prospectus (HTML), or ''.
    """
    window = get_objective_window(document) if window is None else window
    end = re.search(SEC_END, window)
    if not end:
        return ""
    section = window[: end.start()].strip()
    sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z“\"])", section)
    keep = [x for x in sentences if not re.search(r"website|www\.", x, re.I)]
    return clean_objective(" ".join(keep))


def compose_summary(objective: str, symbol: str, row: dict[str, str], kind: str) -> str:
    """
    The official objective, followed by the factual summary when the objective is short
    ("The Fund seeks total return."); the factual summary alone when there is none."""
    factual = create_factual_summary(symbol, row, kind)
    if not objective:
        return factual
    return f"{objective} {factual}".strip() if len(objective) < 160 else objective


OBJECTIVE_TERMS = (
    r"\bseeks?\b|objective|capital appreciation|current income|total return|growth of capital"
    r"|investment results|income"
)


def clean_objective(text: str) -> str:
    """
    Tidy an extracted objective; '' when it does not read as an investment objective.

    Ends it at its last full sentence (dropping a stray heading word such as "FUND") and drops
    dated outcome-period details (e.g. a buffer ETF's cap "over the period April 1, 2026 through
    March 31, 2027"), which go stale; a target-maturity year is kept.
    """
    text = re.sub(r"“\s*Fund\s*”", "“Fund”", text)
    text = re.sub(r"\s+([,.;:)])", r"\1", text).strip()
    last = max(text.rfind(c) for c in ".!?")
    text = text[: last + 1] if last >= 0 else ""
    sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z“\"])", text)
    dated_terms = (
        r"\b(?:19|20)\d\d\b.*\b(?:cap|caps|upside|outcome period|buffer|floor|period)\b"
    )
    dated_terms_rev = (
        r"\b(?:cap|caps|upside|outcome period|buffer|floor|period)\b.*\b(?:19|20)\d\d\b"
    )
    text = " ".join(
        x
        for x in sentences
        if not re.search(f"{dated_terms}|{dated_terms_rev}", x, re.I)
    )
    text = text.strip()
    if not (20 <= len(text) <= 1200) or not re.search(OBJECTIVE_TERMS, text, re.I):
        return ""
    return text


class SecFunds:
    """
    US fund data from SEC EDGAR: investment objectives and registrant (trust) per ticker.

    Disabled (every lookup returns '') without SEC_USER_AGENT_EMAIL or when EDGAR is
    unreachable, so it can never stop a run.
    """

    def __init__(self, contact: str | None) -> None:
        """
        Load the SEC fund series index when a contact email is set (SEC requires one).
        """
        self.headers = {"User-Agent": f"FinanceDatabase {contact}"} if contact else None
        self.funds: dict[str, list] = {}
        self.last = 0.0
        if self.headers:
            try:
                data = json.loads(
                    self.get("https://www.sec.gov/files/company_tickers_mf.json")
                )
                self.funds = {row[3]: row for row in data["data"]}
            except Exception as error:
                print(
                    f"  SEC EDGAR unavailable, no SEC enrichment: {type(error).__name__}: {error}"
                )
                self.headers = None

    def get(self, url: str) -> str:
        """
        Download an SEC page, pausing between requests to respect the SEC rate limit.
        """
        wait = 0.15 - (time.time() - self.last)  # stay under SEC's 10 requests/second
        if wait > 0:
            time.sleep(wait)
        self.last = time.time()
        response = requests.get(url, headers=self.headers, timeout=TIMEOUT)
        response.raise_for_status()
        return response.text

    def get_registrant(self, symbol: str) -> str:
        """
        Get the registrant (fund family) of a fund symbol, or an empty string.
        """
        return str(self.funds[symbol][0]) if symbol in self.funds else ""

    def get_objective(self, symbol: str) -> str:
        """
        Investment objective from one of the series' latest 497K filings, or ''.

        Some recent 497K filings are supplements (e.g. a portfolio-manager change) rather
        than a summary prospectus, so up to three are tried.
        """
        if not self.headers or symbol not in self.funds:
            return ""
        try:
            series = self.funds[symbol][1]
            atom = self.get(
                "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK="
                f"{series}&type=497K&dateb=&owner=include&count=3&output=atom"
            )
            for filing in re.findall(r"<filing-href>([^<]+)</filing-href>", atom)[:3]:
                docs = re.findall(
                    r'href="(/Archives/edgar/data/[^"]+\.htm)"', self.get(filing)
                )
                objective = (
                    extract_objective(self.get("https://www.sec.gov" + docs[0]))
                    if docs
                    else ""
                )
                if objective:
                    return objective
            return ""
        except Exception as error:
            print(f"  SEC objective for {symbol} unavailable: {type(error).__name__}")
            return ""

    def get_registrant_families(self, db: "Database") -> dict[str, str]:
        """
        SEC registrant (CIK) -> family, where >= 90% of >= 5 existing US ETFs agree.
        """
        if not self.funds:
            return {}
        pairs = []
        for file in US_ETF_FILES:
            if os.path.exists(db.get_path("etfs", file)):
                frame = db.get_frame("etfs", file)
                pairs += [
                    (self.get_registrant(s), f)
                    for s, f in frame["family"].items()
                    if f and s in self.funds
                ]
        table = pd.DataFrame(pairs, columns=["cik", "family"])
        families = {}
        for cik, group in table.groupby("cik"):
            counts = group.family.value_counts()
            if len(group) >= 5 and counts.iloc[0] / len(group) >= 0.9:
                families[cik] = counts.index[0]
        return families
