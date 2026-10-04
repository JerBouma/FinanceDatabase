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

- Each source is fetched and parsed on its own. A download error, a format change or a
  suspiciously short list skips that source only; the rest of the run continues.
- Rows are only ever added; nothing is removed. A symbol is added only when it exists in no
  asset class at all (no cross-asset collisions).
- A candidate is skipped when an existing row in the same exchange file has the same symbol
  apart from separators (`HCO.P.V` vs `HCO-P.V`) and the same company name.
- Ticker changes: when a new listing matches a live existing row in the same exchange file by
  ISIN or company name, and that row's symbol is no longer on the exchange's official list,
  the old row is marked `delisted=True`. More than `MAX_DELISTINGS_PER_SOURCE` such changes
  for one source is treated as a parsing problem and no rows are delisted for that source.
- Values the source does not provide are left blank, never guessed.
"""

from __future__ import annotations

import argparse
import glob
import io
import json
import os
import re
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
    mic: str = ""


@dataclass
class SourceResult:
    """Parsed source: listings to consider adding and every symbol currently listed."""

    listings: list[Listing] = field(default_factory=list)
    official: dict[str, set[str]] = field(default_factory=dict)


# --------------------------------------------------------------------------- helpers


def fetch(url: str) -> bytes:
    """Download a URL with a browser user agent; raises on HTTP errors."""
    response = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
    response.raise_for_status()
    return response.content


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


def parse_nse(equity_csv: bytes, etf_csv: bytes) -> SourceResult:
    """India: NSE main-board equities and ETFs."""
    result = SourceResult()
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
    for _, row in data.iterrows():
        section, symbol = row["Section/Products"], f"{row['Local Code']}.T"
        name = row["Name (English)"].strip()
        if re.search(r"(Prime|Standard|Growth) Market", section):
            country = "Japan" if "Domestic" in section else ""
            result.listings.append(
                Listing("equities", "JPX", symbol, name, "JPY", country=country)
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
            fetch("https://www.nasdaqtrader.com/dynamic/SymDir/nasdaqlisted.txt"),
            fetch("https://www.nasdaqtrader.com/dynamic/SymDir/otherlisted.txt"),
        ),
        "HKEX": lambda: parse_hkex(
            fetch(
                "https://www.hkex.com.hk/eng/services/trading/securities/securitieslists/ListOfSecurities.xlsx"
            )
        ),
        "NSE": lambda: parse_nse(
            fetch(nse.format("EQUITY_L.csv")), fetch(nse.format("eq_etfseclist.csv"))
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
        """Issuer family from the first two words of an ETF name (>= 95% agreement, >= 5 rows)."""
        frames = [
            read_csv_text(p)[["name", "family"]]
            for p in glob.glob(f"{self.root}/etfs/*.csv")
        ]
        etfs = pd.concat(frames)
        etfs = etfs[etfs.family != ""]
        key = lambda name: " ".join(name.lower().split()[:2])  # noqa: E731
        families = {}
        for prefix, group in etfs.groupby(etfs.name.map(key)):
            counts = group.family.value_counts()
            if len(group) >= 5 and counts.iloc[0] / len(group) >= 0.95:
                families[prefix] = counts.index[0]
        return lambda name: families.get(key(name), "")

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
    db: Database, name: str, result: SourceResult, family: Callable[[str], str]
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

    # Ticker changes: a live row in the same file with the same ISIN or name whose symbol has
    # dropped off the exchange's official list is superseded by the new listing.
    for listing in added:
        official = result.official.get(listing.file)
        if official is None:
            continue
        if ("official", listing.file) not in db.cache:
            db.cache[("official", listing.file)] = {symbol_key(s) for s in official}
        official_keys = db.cache[("official", listing.file)]
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
                isin=listing.isin,
            )
        else:
            row.update(isin=listing.isin)
            if listing.file in US_ETF_FILES:
                row["family"] = family(listing.name)
        db.added[db.path(listing.kind, listing.file)].append(
            pd.Series(row, name=listing.symbol)
        )
        db.symbols.add(listing.symbol)

    return {"added": added, "skipped_format": skipped_format, "delisted": delist}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--database", default="database")
    parser.add_argument(
        "--dry-run", action="store_true", help="report only, write nothing"
    )
    args = parser.parse_args()

    db = Database(args.database)
    family = db.etf_families()
    failures = []
    for name, load in load_sources(db.group_sector()).items():
        try:
            result = load()
        except Exception as error:  # one broken source must not stop the others
            failures.append(name)
            print(f"{name}: skipped ({type(error).__name__}: {error})")
            continue
        summary = apply_source(db, name, result, family)
        counts = pd.Series(
            [f"{x.kind}/{x.file}" for x in summary["added"]], dtype=str
        ).value_counts()
        print(
            f"{name}: {len(summary['added'])} added {counts.to_dict()}, "
            f"{len(summary['delisted'])} superseded tickers delisted, "
            f"{len(summary['skipped_format'])} skipped as symbol-format duplicates"
        )
        for kind, file, old, new in summary["delisted"]:
            print(f"  delisted {kind}/{file} {old} (now listed as {new})")
    if not args.dry_run:
        db.write()
    if failures:
        print(f"Sources skipped this run: {', '.join(failures)}")


if __name__ == "__main__":
    main()
