"""Helpers Module"""

__docformat__ = "google"

import re
import urllib.request

import pandas as pd
import requests

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    )
}
TIMEOUT = 120
US_ETF_FILES = {"NMS", "NGM", "NCM", "NYQ", "ASE", "PCX", "BTS"}

SUFFIX = r"\.(?:TO|V|HK|NS|T|AX)$"
# Instruments with an expiry or maturity date go out of date quickly and are not added;
# the weekly US update uses the same rule.
DATED_NAME = re.compile(
    r"\bwarrants?\b|\s(?:WTS?|RTS)$|\brights?$|\bsubscription rights?\b"
    r"|\bcontingent value rights?\b|\brights? to (?:receive|subscribe)\b"
    r"|\b(?:notes?|debentures?|bonds?|preferred shares)\b.*\bdue\b"
    r"|\bdue\s+(?:\w+\s+)?(?:\d{1,2},?\s+)?(?:19|20)\d\d\b"
    r"|\b(?:perpetual|subordinated|senior)\s+(?:\w+\s+)?(?:notes?|debentures?|bonds?)\b"
    r"|\b(?:notes?|debentures?)\s*$|\bincome capital obligation"
    r"|\bexpir(?:es|ing|ation)\b|\b\d{1,2}/\d{1,2}/(?:19|20)?\d{2}\b",
    re.IGNORECASE,
)
# Equities only hold the shares of companies. A name with a maturity or expiry date, a
# strike, or a coupon without any share wording, or an international (XS) ISIN marks a
# bond, note, warrant or certificate instead. The weekly update skips these and
# scripts/remove_non_shares.py removes any that reach the equities files.
MONTHS = "JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC"
DATE_IN_NAME = re.compile(
    r"\b(?:0[1-9]|[12]\d|3[01])(?:0[1-9]|1[0-2])\d{2}\b"
    r"|\b\d{1,2}[/.]\d{1,2}[/.](?:19|20)?\d{2}\b"
    rf"|\b\d{{1,2}}\s?(?:{MONTHS})\s?(?:\d{{2}}|\d{{4}})?\b"
    r"|\b(?:19|20)?\d{2}\s?-\s?(?:19|20)?\d{2}$"
    r"|\bdue\b|\bexpir",
    re.IGNORECASE,
)
OPTION_NAME = re.compile(r"\b(?:CALL|PUT)\b.*\d", re.IGNORECASE)
COUPON = re.compile(r"\d+(?:[.,]\d+)?\s?%")
SHARE_WORDS = re.compile(
    r"\b(?:pref|pfd|preferred|preference|depositary|cumulative|cum|shares?|stock"
    r"|units?)\b",
    re.IGNORECASE,
)
DEBT_WORDS = re.compile(
    r"\b(?:notes?|nts?|bonds?|bds|debentures?|ncd|secs|perp|pl)\b|%pl\b",
    re.IGNORECASE,
)


def check_non_share(name: str, country: str = "", isin: str = "") -> bool:
    """
    Check whether an equities row is not a company share: a dated instrument, an
    option or warrant, coupon-bearing debt or an instrument with an international
    (XS) ISIN.

    Args:
        name (str): The instrument name.
        country (str): The issuer's country, empty when unknown.
        isin (str): The ISIN (or an ISIN used as symbol), empty when unknown.

    Returns:
        bool: True for an instrument that does not belong in equities.
    """
    if isin.upper().startswith("XS") or DATE_IN_NAME.search(name):
        return True
    if OPTION_NAME.search(name):
        return True
    coupon_debt = COUPON.search(name) and not SHARE_WORDS.search(name)
    return bool(coupon_debt and (not country or DEBT_WORDS.search(name)))


NAME_STOPWORDS = (
    r"\b(inc|incorporated|corp|corporation|ltd|limited|plc|co|company|holdings?|group|"
    r"sa|ag|nv|se|the|class [a-z]|common stock|ordinary shares|shares|stock|llc|lp)\b"
)


def fetch(url: str) -> bytes:
    """
    Download a URL with a browser user agent; raises on HTTP errors.
    """
    response = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
    response.raise_for_status()
    return response.content


def fetch_nasdaq_trader(name: str) -> bytes:
    """
    Nasdaq Trader symbol directory file over HTTPS, falling back to its official FTP copy.

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


def fetch_optional(url: str) -> bytes | None:
    """
    Download an enrichment-only file; a failure just means less enrichment.
    """
    try:
        return fetch(url)
    except Exception as error:
        print(f"  optional download failed ({url}): {type(error).__name__}: {error}")
        return None


def require(condition: bool, message: str) -> None:
    """
    Abort the current source when its data does not look like the expected format.
    """
    if not condition:
        raise ValueError(message)


def read_csv_text(path: str) -> pd.DataFrame:
    """
    Read a database CSV as text, keeping values like the ticker 'NA' intact.
    """
    return pd.read_csv(path, index_col=0, dtype=str, keep_default_na=False)


def normalize_name(name: str) -> str:
    """
    Company name reduced to its distinctive words, for duplicate detection.
    """
    name = re.sub(r"\(.*?\)", " ", name.lower())
    name = re.sub(r"[^a-z0-9 ]", " ", name)
    return re.sub(r"\s+", " ", re.sub(NAME_STOPWORDS, " ", name)).strip()


def get_symbol_key(symbol: str) -> str:
    """
    Symbol without separators, keeping the exchange suffix (HCO.P.V == HCO-P.V).
    """
    match = re.search(SUFFIX, symbol)
    suffix = match.group(0) if match else ""
    return re.sub(r"[-.^/]", "", symbol[: len(symbol) - len(suffix)]) + suffix


def convert_to_yahoo_canada(symbol: str) -> str:
    """
    TSX symbol to the database's Yahoo-style form.

    'BCE.PR.A' -> 'BCE-PA', 'TD.PF.A' -> 'TD-PFA', 'GASX.WT.A' -> 'GASX-WTA', 'AD.UN' -> 'AD-UN'.
    """
    base, _, rest = symbol.partition(".")
    if not rest:
        return base
    if rest.startswith("PR."):
        rest = "P" + rest[3:]
    return base + "-" + rest.replace(".", "")


def get_canada_name(company: str, symbol: str) -> str:
    """
    Company name for the primary instrument; other classes and series name the instrument.
    """
    if "." not in symbol or symbol.split(".", 1)[1] in ("P", "H"):
        return company
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
