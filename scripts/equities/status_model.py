"""Status Model"""

__docformat__ = "google"

import io
import re

import pandas as pd

from scripts.listings.helpers import check_non_share

# US exchange files the Nasdaq Trader directory covers (not OTC).
US_FILES = ["NYQ", "NMS", "NGM", "NCM", "ASE"]
# At most this share of the live US rows is delisted in one run; more means a bad feed.
MAX_DELISTED_SHARE = 0.03
# A directory shorter than this is incomplete.
MINIMUM_DIRECTORY = 8000
# An exchange is a home market when at least this share of its listings is one country.
HOME_VENUE_SHARE = 0.5
# German exchanges share one ticker per security; Xetra and Frankfurt are the reference.
GERMAN_REFERENCE = ["GER", "FRA"]
GERMAN_REGIONAL = ["BER", "DUS", "MUN", "HAM", "HAN", "STU"]


def convert_symbol(symbol: str) -> str:
    """
    One key for every spelling of a US symbol: BRK.B and BRK-B, ABR$D, ABR^D and
    ABR-PD, X.U and X-UN, X.WS and X-WT.

    Args:
        symbol (str): The symbol in directory or database style.

    Returns:
        str: The key.
    """
    key = re.sub(r"[.\-^$](?:P(?=[A-Z]$))?", "|", symbol.upper())
    key = re.sub(r"\|UN$", "|U", key)
    key = re.sub(r"\|W[ST]$", "|W", key)
    return key.replace("|", "")


def read_directory(nasdaq: bytes, other: bytes) -> dict[str, str]:
    """
    The listed US securities of the Nasdaq Trader directory, without test issues.

    Args:
        nasdaq (bytes): nasdaqlisted.txt.
        other (bytes): otherlisted.txt.

    Returns:
        dict[str, str]: Symbol key -> security name.
    """
    listed = {}
    for raw, column in ((other, "ACT Symbol"), (nasdaq, "Symbol")):
        frame = pd.read_csv(io.BytesIO(raw), sep="|", dtype=str, keep_default_na=False)
        frame = frame[(frame.get("Test Issue", "N") == "N") & (frame[column] != "")]
        for symbol, name in zip(frame[column], frame["Security Name"], strict=True):
            listed[convert_symbol(symbol)] = name
    return listed


def get_name_start(name: str) -> str:
    """
    The first two words of a name in lower case without punctuation or 'the'
    ('The Brink's Company' -> 'brinks company').

    Args:
        name (str): The name.

    Returns:
        str: The words, empty for an empty name.
    """
    words = re.sub(r"[^a-z0-9 ]", "", name.lower()).split()
    return " ".join([word for word in words if word != "the"][:2])


def get_status_changes(
    frame: pd.DataFrame, listed: dict[str, str]
) -> tuple[list[str], list[str]]:
    """
    The rows of a US exchange file the directory no longer lists, and the delisted
    shares it lists again under the same company name.

    Args:
        frame (pd.DataFrame): The exchange file.
        listed (dict[str, str]): See read_directory.

    Returns:
        tuple[list[str], list[str]]: The symbols to delist and to relist.
    """
    keys = frame.index.map(convert_symbol)
    in_directory = keys.isin(list(listed))
    live = frame["delisted"] != "True"
    delist = list(frame.index[live & ~in_directory])
    relist = [
        symbol
        for symbol, key in zip(
            frame.index[~live & in_directory], keys[~live & in_directory], strict=True
        )
        if get_name_start(frame.loc[symbol, "name"]) == get_name_start(listed[key])
        and not check_non_share(listed[key])
    ]
    return delist, relist


def find_stale_lines(equities: pd.DataFrame) -> list[str]:
    """
    The live lines of a share whose listings in its home market are all delisted.

    Args:
        equities (pd.DataFrame): Every equities file with exchange, country, isin and
            delisted.

    Returns:
        list[str]: The symbols to delist.
    """
    known = equities[equities["country"] != ""]
    shares = known.groupby("exchange")["country"].value_counts(normalize=True)
    venues = shares[shares >= HOME_VENUE_SHARE].reset_index()
    home_country = dict(zip(venues["exchange"], venues["country"], strict=True))
    with_isin = equities[equities["isin"].str.len() == 12]
    home = with_isin["exchange"].map(home_country) == with_isin["country"]
    dead = with_isin["delisted"] == "True"
    status = (
        pd.DataFrame(
            {
                "isin": with_isin["isin"],
                "dead_home": home & dead,
                "live_home": home & ~dead,
            }
        )
        .groupby("isin")[["dead_home", "live_home"]]
        .any()
    )
    stale = status.index[status["dead_home"] & ~status["live_home"]]
    return list(with_isin.index[with_isin["isin"].isin(stale) & ~dead])


def find_stale_german_lines(equities: pd.DataFrame) -> list[str]:
    """
    The live regional German lines whose ticker is delisted on Xetra and Frankfurt.

    Args:
        equities (pd.DataFrame): Every equities file with exchange and delisted.

    Returns:
        list[str]: The symbols to delist.
    """
    base = equities.index.str.split(".").str[0]
    reference = equities["exchange"].isin(GERMAN_REFERENCE)
    dead = (equities["delisted"] == "True")[reference].groupby(base[reference]).all()
    regional = equities["exchange"].isin(GERMAN_REGIONAL) & (
        equities["delisted"] != "True"
    )
    return list(equities.index[regional & base.map(dead).fillna(False).astype(bool)])
