"""Sources Model"""

__docformat__ = "google"

import io
import json
import re
from collections.abc import Callable
from dataclasses import dataclass, field

import pandas as pd

from scripts.listings.helpers import (
    US_ETF_FILES,
    convert_to_yahoo_canada,
    fetch,
    fetch_nasdaq_trader,
    fetch_optional,
    get_canada_name,
    require,
)


@dataclass
class Listing:
    """
    One listed instrument as published by an exchange.
    """

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
    summary: str = ""
    figi: str = ""
    composite_figi: str = ""
    shareclass_figi: str = ""


@dataclass
class SourceResult:
    """
    Parsed source: listings to consider adding and every symbol currently listed.
    """

    listings: list[Listing] = field(default_factory=list)
    official: dict[str, set[str]] = field(default_factory=dict)
    # exchange file -> {symbol: exchange sector label} for every listed symbol, used to learn
    # how the exchange's classification translates to the database's categories.
    classifications: dict[str, dict[str, str]] = field(default_factory=dict)


def parse_nasdaq_trader(nasdaq_listed: bytes, other_listed: bytes) -> SourceResult:
    """
    US ETFs from the Nasdaq Trader symbol directory.
    """
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
    """
    Hong Kong equities, REITs and ETPs traded in HKD.
    """
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
    """
    India: NSE main-board equities and ETFs (industries from the Nifty Total Market list).
    """
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
    """
    Japan: TSE Prime/Standard/Growth equities and ETFs/ETNs.
    """
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
    """
    Australia: ASX companies with a GICS industry group (rows without one are skipped).
    """
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
        if group in group_sector:
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
    """
    Canada: TSX and TSXV equities, TSX ETFs.
    """
    result = SourceResult()
    for raw, file, suffix in [(tsx_json, "TOR", ".TO"), (tsxv_json, "VAN", ".V")]:
        companies = json.loads(raw)["results"]
        require(len(companies) > 1000, f"{file} directory too short")
        result.official[file] = {
            convert_to_yahoo_canada(i["symbol"]) + suffix
            for c in companies
            for i in c["instruments"]
        }
        for company in companies:
            name = company["name"].strip()
            for instrument in company["instruments"]:
                symbol = instrument["symbol"]
                if re.search(r"\.(DB|NT|NO)(\.|$)", symbol):
                    continue
                currency = "USD" if symbol.endswith(".U") else "CAD"
                listing_name = get_canada_name(name, symbol)
                ticker = convert_to_yahoo_canada(symbol) + suffix
                if re.search(r"\bETF\b", name) and file == "TOR":
                    result.listings.append(
                        Listing("etfs", "TOR", ticker, listing_name, currency)
                    )
                elif not re.search(r"\b(ETF|ETN|Fund)\b", name):
                    result.listings.append(
                        Listing("equities", file, ticker, listing_name, currency)
                    )
    return result


def get_jpx_download_url() -> str:
    """
    The JPX listed-issues file name changes over time; read it from the index page.
    """
    page = fetch(
        "https://www.jpx.co.jp/english/markets/statistics-equities/misc/01.html"
    ).decode()
    match = re.search(r'href="([^"]*/data_e\.xlsx?)"', page)
    require(match is not None, "JPX download link not found")
    return "https://www.jpx.co.jp" + match.group(1)


def load_sources(group_sector: dict[str, str]) -> dict[str, Callable[[], SourceResult]]:
    """
    Source name -> loader. Loaders download and parse lazily so one failure stays isolated.
    """
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
            fetch_optional(
                "https://archives.nseindia.com/content/indices/ind_niftytotalmarket_list.csv"
            ),
        ),
        "JPX": lambda: parse_jpx(fetch(get_jpx_download_url())),
        "ASX": lambda: parse_asx(
            fetch("https://www.asx.com.au/asx/research/ASXListedCompanies.csv"),
            group_sector,
        ),
        "TSX/TSXV": lambda: parse_tsx(
            fetch(tsx.format("tsx")), fetch(tsx.format("tsxv"))
        ),
    }
