"""Helpers Module"""

__docformat__ = "google"

import os
import re
import urllib.request

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    )
}
TIMEOUT = 120


def create_session() -> requests.Session:
    """
    A session that retries network errors, rate limits and server errors with backoff.

    Returns:
        requests.Session: The session, with the browser user agent.
    """
    retry = Retry(
        total=3,
        backoff_factor=5,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset({"GET", "POST"}),
        respect_retry_after_header=True,
        raise_on_status=False,
    )
    session = requests.Session()
    session.headers.update(HEADERS)
    for prefix in ("http://", "https://"):
        session.mount(prefix, HTTPAdapter(max_retries=retry))
    return session


SESSION = create_session()
US_ETF_FILES = {"NMS", "NGM", "NCM", "NYQ", "ASE", "PCX", "BTS"}

SUFFIX = r"\.(?:TO|V|HK|NS|T|AX)$"
# Instruments with an expiry or maturity date go out of date quickly and are not added.
DATED_NAME = re.compile(
    r"\bwarrants?\b|\s(?:WTS?|RTS)$|\brights?$|\bsubscription rights?\b"
    r"|\bcontingent value rights?\b|(?<!the )\brights? to (?:receive|subscribe)\b"
    r"|\b(?:notes?|debentures?|bonds?|preferred shares)\b.*\bdue\b"
    r"|\bdue\s+(?:\w+\s+)?(?:\d{1,2},?\s+)?(?:19|20)\d\d\b"
    r"|\b(?:perpetual|subordinated|senior)\s+(?:\w+\s+)?(?:notes?|debentures?|bonds?)\b"
    r"|\b(?:notes?|debentures?)\s*$|\bincome capital obligation|\bzones$|\bexchangeable notes?\b"
    r"|\bexpir(?:es|ing|ation)\b|\b\d{1,2}/\d{1,2}/(?:19|20)?\d{2}\b",
    re.IGNORECASE,
)
# Equities only hold company shares; these patterns mark bonds, warrants and certificates.
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
WARRANT_NAME = re.compile(
    r"\b(?:warrants?|waran)\b|\bwts(?:\s\S{1,4})?$|\bWT EXP\b", re.IGNORECASE
)
# Subscription warrants named by series ('TO3'), and names ending in 'Wts'.
SUBSCRIPTION_NAME = re.compile(r"\bTO\d+\b|wts$", re.IGNORECASE)
# Nordic knock-out, stop-loss and mini certificates ('KO 1(39', 'SO 2(196') and Vienna
# open-end turbo certificates ('EB OE TL.Z./AIXTRON').
CERTIFICATE_NAME = re.compile(r"\b(?:KO|SO|MINI)\s?\d+\s?\(|\bT[LS]\.\s?Z\./")
# German bond short names: coupon period ('Chevron 14/17', 'ENGIE 13/UND.FLR'), floaters,
# MTNs, 'ANL.V.' (Anleihe) and Australian capital-indexed bonds ('Australia 2025 CI').
BOND_SHORT_NAME = re.compile(
    r"(?<=[A-Za-z .(])\d{2}/(?:\d{4}|\d{2}|UND\.?)(?!\d)|\bFLR\b|\bMTN\s?\d|\bANL\.\s?V\."
    r"|\b(?:19|20)\d{2} CI$",
    re.IGNORECASE,
)
# Debentures, rights issues, leveraged products and indices listed as equities.
OTHER_NON_SHARE = re.compile(
    r"\bred(?:eemable)? NCDs?\b|\bexch(?:ange)? traded bond\b|\brights issue\b|\bleveraged product\b|"
    r"\b(?:price|total) return index\b",
    re.IGNORECASE,
)
# Commercial paper, as Caracas lists it ('P. C. DE NETUNO, EMISION 2020-I').
COMMERCIAL_PAPER = re.compile(
    r"^P\.\s?C\.\s+[A-Z0-9]|\b(?i:papel(?:es)? comercial(?:es)?|commercial paper)\b"
)
COUPON = re.compile(r"\d+(?:[.,]\d+)?\s?%")
EXCHANGEABLE_NOTE = re.compile(r"\bzones$|\bexchangeable notes?\b", re.IGNORECASE)
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
    Check whether an equities row is not a company share (debt, warrant, certificate).

    Args:
        name (str): The instrument name.
        country (str): The issuer's country, empty when unknown.
        isin (str): The ISIN (or an ISIN used as symbol), empty when unknown.

    Returns:
        bool: True for an instrument that does not belong in equities.
    """
    if isin.upper().startswith("XS") or DATE_IN_NAME.search(name):
        return True
    if OPTION_NAME.search(name) or WARRANT_NAME.search(name):
        return True
    if any(
        p.search(name)
        for p in (
            SUBSCRIPTION_NAME,
            CERTIFICATE_NAME,
            OTHER_NON_SHARE,
            BOND_SHORT_NAME,
            COMMERCIAL_PAPER,
        )
    ):
        return True
    if EXCHANGEABLE_NOTE.search(name):
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
    response = SESSION.get(url, timeout=TIMEOUT)
    response.raise_for_status()
    return response.content


def fetch_nasdaq_trader(name: str) -> bytes:
    """
    Nasdaq Trader symbol directory file over HTTPS, falling back to its official FTP copy.
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


def fetch_euronext_etfs() -> bytes:
    """
    Euronext's ETF list as CSV, the download behind its ETF directory page.
    """
    response = SESSION.post(
        "https://live.euronext.com/en/pd_es/data/track/download"
        "?mics=XAMS%2CXPAR%2CXBRU%2CXLIS%2CXOSL",
        data={
            "args[fe_type]": "csv",
            "args[fe_decimal]": ".",
            "args[fe_date_format]": "d/m/Y",
            "args[fe_layout]": "ver",
        },
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    return response.content


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


def write_csv(frame: pd.DataFrame, path: str) -> bool:
    """
    Write a CSV only when its content changes, through a temporary file so an interrupted
    run never leaves a half-written file.

    Args:
        frame (pd.DataFrame): The rows, indexed by symbol.
        path (str): The CSV file.

    Returns:
        bool: Whether the file changed.
    """
    content = frame.to_csv(lineterminator="\n")
    if os.path.exists(path):
        with open(path, encoding="utf-8", newline="") as handle:
            if handle.read() == content:
                return False
    temporary = f"{path}.tmp"
    with open(temporary, "w", encoding="utf-8", newline="") as handle:
        handle.write(content)
    os.replace(temporary, path)
    return True


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
    TSX symbol to the database's Yahoo-style form ('BCE.PR.A' -> 'BCE-PA').
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
