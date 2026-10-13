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
    fetch_euronext_etfs,
    fetch_nasdaq_trader,
    fetch_optional,
    get_canada_name,
    read_html_table,
    require,
)

# KRX boards in KIND's list: KOSPI and KOSDAQ (KONEX is not covered).
KRX_BOARDS = {"유가": ("KSC", ".KS"), "코스닥": ("KOE", ".KQ")}
# KIND gives a Korean region; foreign companies have a country there instead.
KOREAN_REGION = re.compile(r"(?:시|(?<!제)도)$")


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
    category_group: str = ""
    category: str = ""
    family: str = ""
    abbreviated: bool = False  # the exchange only publishes a short name


@dataclass
class SourceResult:
    """
    Parsed source: listings to consider adding and every symbol currently listed.
    """

    listings: list[Listing] = field(default_factory=list)
    official: dict[str, set[str]] = field(default_factory=dict)
    # exchange file -> {symbol: exchange sector label}, to learn the category mapping.
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
    # 2900-2999 are temporary parallel-trading counters duplicating a main stock code.
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
    India: NSE main-board equities and ETFs, industries from the Nifty Total Market.
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


def parse_asx(csv: bytes) -> SourceResult:
    """
    Australia: ASX companies; the third column marks trusts and funds 'Not Applic'.
    """
    result = SourceResult()
    data = pd.read_csv(io.BytesIO(csv), skiprows=2, dtype=str, keep_default_na=False)
    require(list(data.columns[:2]) == ["Company name", "ASX code"], "ASX")
    require(len(data.columns) >= 3 and len(data) > 1500, "ASX list too short")
    result.official = {"ASX": {f"{c}.AX" for c in data["ASX code"]}}
    companies = ~data.iloc[:, 2].isin(["", "Not Applic"])
    for _, row in data[companies].iterrows():
        result.listings.append(
            Listing(
                "equities",
                "ASX",
                f"{row['ASX code']}.AX",
                row["Company name"].strip(),
                "AUD",
            )
        )
    return result


def parse_krx(page: bytes) -> SourceResult:
    """
    South Korea: KOSPI and KOSDAQ companies from KRX's KIND list. The names are Korean;
    OpenFIGI gives the English ones, and rows without one are not added.
    """
    result = SourceResult()
    rows = read_html_table(page, "euc-kr")
    require(bool(rows) and rows[0][:3] == ["회사명", "시장구분", "종목코드"], "KRX")
    require(len(rows) > 2000, "KRX list too short")
    for file, _ in KRX_BOARDS.values():
        result.classifications[file] = {}
    for name, board, code, industry, *rest in rows[1:]:
        if board not in KRX_BOARDS or not re.fullmatch(r"[0-9A-Z]{6}", code):
            continue
        file, suffix = KRX_BOARDS[board]
        symbol = code + suffix
        result.classifications[file][symbol] = industry
        region = rest[-1] if rest else ""
        result.listings.append(
            Listing(
                "equities",
                file,
                symbol,
                name,
                "KRW",
                country="South Korea" if KOREAN_REGION.search(region) else "",
                classification=industry,
                abbreviated=True,
            )
        )
    return result


def parse_set(page: bytes) -> SourceResult:
    """
    Thailand: SET and mai companies; property and infrastructure funds are skipped.
    """
    result = SourceResult()
    rows = read_html_table(page)
    header = next(
        (i for i, row in enumerate(rows) if row[:2] == ["Symbol", "Company"]), -1
    )
    require(header >= 0 and len(rows) - header > 500, "SET list too short")
    data = [row for row in rows[header + 1 :] if len(row) >= 5 and row[0]]
    # NVDR lines (-R) belong to their company and stay listed with it.
    result.official = {"SET": {f"{r[0]}{tag}.BK" for r in data for tag in ("", "-R")}}
    result.classifications = {"SET": {f"{r[0]}.BK": r[4] for r in data}}
    for symbol, name, _, _, sector, *_ in data:
        if re.search(r"\bFUND\b", name, re.I):
            continue
        result.listings.append(
            Listing(
                "equities",
                "SET",
                f"{symbol}.BK",
                name,
                "THB",
                classification=sector,
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


EURONEXT_FILES = {
    "Euronext Amsterdam": ("AMS", ".AS", "XAMS"),
    "Euronext Paris": ("PAR", ".PA", "XPAR"),
    "Euronext Brussels": ("BRU", ".BR", "XBRU"),
    "Euronext Lisbon": ("LIS", ".LS", "XLIS"),
    "Oslo Børs": ("OSL", ".OL", "XOSL"),
}


def parse_euronext(csv: bytes) -> SourceResult:
    """
    ETFs on Euronext Amsterdam, Paris, Brussels, Lisbon and Oslo.
    """
    lines = csv.decode("utf-8-sig").splitlines()
    rows = [line for i, line in enumerate(lines) if i == 0 or line.count(";") > 5]
    data = pd.read_csv(
        io.StringIO("\n".join(rows)), sep=";", dtype=str, keep_default_na=False
    )
    require(
        {"Name", "ISIN", "Symbol", "Market", "Currency"} <= set(data.columns),
        "Euronext",
    )
    require(len(data) > 500, "Euronext ETF list too short")
    result = SourceResult()
    for _, row in data.iterrows():
        market = row.Market.split(",")[0].strip()
        if market not in EURONEXT_FILES or not row.Symbol.strip():
            continue
        file, suffix, mic = EURONEXT_FILES[market]
        symbol = row.Symbol.strip() + suffix
        result.official.setdefault(file, set()).add(symbol)
        result.listings.append(
            Listing(
                "etfs",
                file,
                symbol,
                row.Name.strip(),
                row.Currency.strip(),
                row.ISIN.strip(),
                mic=mic,
                abbreviated=True,
            )
        )
    return result


def parse_xetra(csv: bytes) -> SourceResult:
    """
    ETFs and ETCs on Xetra.
    """
    data = pd.read_csv(
        io.BytesIO(csv), sep=";", skiprows=2, dtype=str, keep_default_na=False
    )
    columns = {"Instrument", "ISIN", "Mnemonic", "Instrument Type", "Currency"}
    require(columns <= set(data.columns), "Xetra")
    require(len(data) > 3000, "Xetra instrument list too short")
    result = SourceResult(official={"GER": {f"{m}.DE" for m in data.Mnemonic if m}})
    funds = data[
        data["Instrument Type"].isin(["ETF", "ETC"])
        & (data["Instrument Status"] == "Active")
        & (data.Mnemonic != "")
    ]
    for _, row in funds.iterrows():
        result.listings.append(
            Listing(
                "etfs",
                "GER",
                f"{row.Mnemonic.strip()}.DE",
                row.Instrument.strip(),
                row.Currency.strip(),
                row.ISIN.strip(),
                mic="XETR",
                abbreviated=True,
            )
        )
    return result


def parse_six(csv: bytes) -> SourceResult:
    """
    ETFs on SIX Swiss Exchange.
    """
    data = pd.read_csv(
        io.BytesIO(csv), sep=";", dtype=str, keep_default_na=False, encoding="latin-1"
    )
    columns = {"ShortName", "ValorSymbol", "ISIN", "TradingBaseCurrency", "ProductLine"}
    require(columns <= set(data.columns), "SIX")
    require(len(data) > 1000, "SIX fund list too short")
    result = SourceResult(official={"EBS": {f"{s}.SW" for s in data.ValorSymbol if s}})
    for _, row in data[
        (data.ProductLine == "ET") & (data.ValorSymbol != "")
    ].iterrows():
        result.listings.append(
            Listing(
                "etfs",
                "EBS",
                f"{row.ValorSymbol.strip()}.SW",
                row.ShortName.strip(),
                row.TradingBaseCurrency.strip(),
                row.ISIN.strip(),
                mic="XSWX",
                abbreviated=True,
            )
        )
    return result


def get_xetra_download_url() -> str:
    """
    The Xetra instrument file moves now and then; read its link from the overview page.
    """
    page = fetch(
        "https://www.cashmarket.deutsche-boerse.com/cash-en/trading/Tradable-Instruments-Xetra"
    ).decode()
    match = re.search(r'href="([^"]*t7-xetr-allTradableInstruments\.csv)"', page)
    require(match is not None, "Xetra download link not found")
    return match.group(1)


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


def load_sources() -> dict[str, Callable[[], SourceResult]]:
    """
    Source name -> lazy loader, so one failure stays isolated.
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
            fetch("https://www.asx.com.au/asx/research/ASXListedCompanies.csv")
        ),
        "KRX": lambda: parse_krx(
            fetch(
                "https://kind.krx.co.kr/corpgeneral/corpList.do?method=download"
                "&searchType=13"
            )
        ),
        "SET": lambda: parse_set(
            fetch(
                "https://www.set.or.th/dat/eod/listedcompany/static/"
                "listedCompanies_en_US.xls"
            )
        ),
        "TSX/TSXV": lambda: parse_tsx(
            fetch(tsx.format("tsx")), fetch(tsx.format("tsxv"))
        ),
        "Xetra": lambda: parse_xetra(fetch(get_xetra_download_url())),
        "Euronext": lambda: parse_euronext(fetch_euronext_etfs()),
        "SIX": lambda: parse_six(
            fetch(
                "https://www.six-group.com/fqs/ref.csv?select=ShortName,ValorSymbol,ISIN,"
                "TradingBaseCurrency,ProductLine&where=PortalSegment=FU&orderby=ShortName"
                "&page=1&pagesize=99999"
            )
        ),
    }
