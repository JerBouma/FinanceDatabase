"""Sources Model"""

__docformat__ = "google"

import io
import time
import xml.etree.ElementTree as ET

import pandas as pd
import requests

from scripts.listings.helpers import SESSION, TIMEOUT, fetch, require

COINGECKO = "https://api.coingecko.com/api/v3"
ISO_LISTS = "https://www.six-group.com/dam/download/financial-information/data-center/iso-currrency/lists/{}.xml"
EURONEXT_INDICES = "https://live.euronext.com/en/pd_es/data/index/download?mics={}"
# Euronext market -> (suffix, exchange, MIC) as used in the indices file.
EURONEXT_MARKETS = {
    "XAMS": (".AS", "AMS"),
    "XPAR": (".PA", "PAR"),
    "XBRU": (".BR", "BRU"),
    "XLIS": (".LS", "LIS"),
    "XOSL": (".OL", "OSL"),
    "XMIL": (".MI", "MIL"),
}


def fetch_coins(pages: int = 2) -> tuple[pd.DataFrame, set[str]]:
    """
    CoinGecko's coins by market cap (250 a page) and the tickers of every listed coin.

    Args:
        pages (int): The number of market cap pages to read.

    Returns:
        tuple[pd.DataFrame, set[str]]: id, symbol, name and rank, and all listed tickers.
    """
    rows = []
    for page in range(1, pages + 1):
        response = SESSION.get(
            f"{COINGECKO}/coins/markets",
            params={
                "vs_currency": "usd",
                "order": "market_cap_desc",
                "per_page": 250,
                "page": page,
            },
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        rows += response.json()
        time.sleep(3)
    listed = SESSION.get(f"{COINGECKO}/coins/list", timeout=TIMEOUT)
    listed.raise_for_status()
    tickers = {coin["symbol"].upper() for coin in listed.json()}
    coins = pd.DataFrame(
        [
            (c["id"], c["symbol"].upper(), c["name"].strip(), i + 1)
            for i, c in enumerate(rows)
        ],
        columns=["id", "symbol", "name", "rank"],
    )
    require(len(coins) >= 200 and len(tickers) > 5000, "CoinGecko lists too short")
    return coins, tickers


def fetch_coin_website(coin_id: str) -> str:
    """
    The homepage of a coin according to CoinGecko, empty when unknown.

    Args:
        coin_id (str): The CoinGecko id.

    Returns:
        str: The homepage URL.
    """
    try:
        response = SESSION.get(
            f"{COINGECKO}/coins/{coin_id}",
            params={
                "localization": "false",
                "tickers": "false",
                "market_data": "false",
            },
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        pages = response.json().get("links", {}).get("homepage", [])
        return next((page for page in pages if page), "")
    except (requests.RequestException, ValueError):
        return ""


def fetch_iso_currencies() -> tuple[dict[str, str], set[str], dict[str, set[str]]]:
    """
    The active and withdrawn ISO 4217 currencies and the ones countries actually use.

    Returns:
        tuple: code -> name, withdrawn codes, code -> country names of usable currencies.
    """
    active: dict[str, str] = {}
    countries: dict[str, set[str]] = {}
    # The ISO lists come from SIX, the ISO 4217 maintenance agency.
    current = ET.fromstring(fetch(ISO_LISTS.format("list-one")))  # noqa: S314
    for entry in current.iter("CcyNtry"):
        code, name = entry.findtext("Ccy"), entry.findtext("CcyNm")
        is_fund = (entry.find("CcyNm").get("IsFund") or "").lower() == "true"
        if code and name and not is_fund:
            active[code] = name.strip()
            countries.setdefault(code, set()).add(
                (entry.findtext("CtryNm") or "").strip()
            )
    historic = ET.fromstring(fetch(ISO_LISTS.format("list-three")))  # noqa: S314
    history = list(historic.iter("HstrcCcyNtry"))
    withdrawn = {e.findtext("Ccy") for e in history if e.findtext("Ccy")} - set(active)
    # An X code only counts for a country that had its own currency before (XCG, Curaçao).
    had_currency = {
        (e.findtext("CtryNm") or "").strip()
        for e in history
        if not (e.findtext("Ccy") or "X").startswith("X")
    }
    usable = {
        code: names
        for code, names in countries.items()
        if not code.startswith("X") or names & had_currency
    }
    require(len(active) > 140 and len(withdrawn) > 50, "ISO 4217 lists too short")
    return active, withdrawn, usable


def fetch_euronext_indices() -> pd.DataFrame:
    """
    The indices Euronext publishes, per market.

    Returns:
        pd.DataFrame: symbol, name, currency, isin, exchange and mic.
    """
    frames = []
    for mic, (suffix, exchange) in EURONEXT_MARKETS.items():
        response = SESSION.post(
            EURONEXT_INDICES.format(mic),
            data={
                "args[fe_type]": "csv",
                "args[fe_decimal]": ".",
                "args[fe_date_format]": "d/m/Y",
                "args[fe_layout]": "ver",
            },
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        lines = response.content.decode("utf-8-sig").splitlines()
        rows = [line for i, line in enumerate(lines) if i == 0 or line.count(";") > 5]
        data = pd.read_csv(
            io.StringIO("\n".join(rows)), sep=";", dtype=str, keep_default_na=False
        )
        require({"Name", "ISIN", "Symbol", "Currency"} <= set(data.columns), "Euronext")
        data = data[~data.Symbol.str.strip().isin(["", "-"])]
        frames.append(
            pd.DataFrame(
                {
                    "symbol": data.Symbol.str.strip() + suffix,
                    "name": data.Name.str.strip(),
                    "currency": data.Currency.str.strip(),
                    "isin": data.ISIN.str.strip(),
                    "exchange": exchange,
                    "mic": mic,
                }
            )
        )
        time.sleep(1)
    indices = pd.concat(frames, ignore_index=True).drop_duplicates("symbol")
    require(len(indices) > 1000, "Euronext index list too short")
    return indices
