"""Equities Model"""

__docformat__ = "google"

import glob

import numpy as np
import pandas as pd

from scripts.listings.helpers import DATED_NAME, check_non_share

FEED_URL = "https://raw.githubusercontent.com/rreichel3/US-Stock-Symbols/main/{0}/{0}_full_tickers.json"

# Feed -> (exchange file, market); NYSE is NYQ (XNYS), only NYSE American is ASE (XASE).
FEEDS = {
    "nasdaq": ("NMS", "NASDAQ Global Select"),
    "nyse": ("NYQ", "New York Stock Exchange"),
    "amex": ("ASE", "NYSE American"),
}

# Market cap tiers by their lower bound in USD.
MARKET_CAP_THRESHOLDS = {
    "Mega Cap": 200_000_000_000,
    "Large Cap": 10_000_000_000,
    "Mid Cap": 2_000_000_000,
    "Small Cap": 300_000_000,
    "Micro Cap": 50_000_000,
    "Nano Cap": 0,
}

# A run that would change more than this share of the US tiers is treated as a feed glitch.
MAX_TIER_CHANGE_SHARE = 0.2

# A plain ticker with the class separators of the feeds (BRK/A, ABR^D, BF.B).
VALID_SYMBOL = r"^[A-Z0-9]+(?:[./^-][A-Z0-9]+)*$"

# Exchange-traded products belong in database/etfs, not equities.
ETP_NAME = r"\b(?:ETF|ETFs|ETN|ETNs|Exchange[- ]Traded)\b"


def calculate_market_cap(value: float | None) -> str | float:
    """
    The market cap tier of a market capitalisation in USD.

    Args:
        value (float | None): The market capitalisation.

    Returns:
        str | float: The tier, NaN when the value is missing or zero.
    """
    if pd.isna(value) or not value:
        return np.nan
    for label, threshold in MARKET_CAP_THRESHOLDS.items():
        if float(value) >= threshold:
            return label
    return np.nan


def lookup_industry_group(industry: str, equities: pd.DataFrame) -> str | float:
    """
    The most common industry group of an industry in the equities.

    Args:
        industry (str): The GICS industry.
        equities (pd.DataFrame): The equities.

    Returns:
        str | float: The industry group, NaN when unknown.
    """
    if pd.isna(industry):
        return np.nan
    subset = equities[equities["industry"] == industry]
    return subset["industry_group"].mode()[0] if not subset.empty else np.nan


def lookup_sector(
    industry: str, industry_group: str, equities: pd.DataFrame
) -> str | float:
    """
    The most common sector of an industry and industry group in the equities.

    Args:
        industry (str): The GICS industry.
        industry_group (str): The GICS industry group.
        equities (pd.DataFrame): The equities.

    Returns:
        str | float: The sector, NaN when unknown.
    """
    if pd.isna(industry) or pd.isna(industry_group):
        return np.nan
    subset = equities[
        (equities["industry_group"] == industry_group)
        & (equities["industry"] == industry)
    ]
    return subset["sector"].mode()[0] if not subset.empty else np.nan


def build_new_ticker(
    row: pd.Series,
    fd_industries: dict,
    equities: pd.DataFrame,
    market_cap: str | float,
    exchange_to_mic: dict,
) -> dict:
    """
    A new equities row from a feed row.

    Args:
        row (pd.Series): The feed row.
        fd_industries (dict): Feed industry label -> GICS industry.
        equities (pd.DataFrame): The equities.
        market_cap (str | float): The market cap tier.
        exchange_to_mic (dict): Exchange -> MIC.

    Returns:
        dict: The equities fields.
    """
    industry = fd_industries.get(row["industry"], np.nan)
    industry_group = lookup_industry_group(industry, equities)
    sector = lookup_sector(industry, industry_group, equities)
    return {
        "name": row["name"],
        "summary": np.nan,
        "currency": "USD",
        "industry": industry,
        "industry_group": industry_group,
        "sector": sector,
        "exchange": row["exchange"],
        "mic": exchange_to_mic.get(row["exchange"], np.nan),
        "market": row["market"],
        "country": row["country"],
        "state": np.nan,
        "city": np.nan,
        "zipcode": np.nan,
        "website": np.nan,
        "market_cap": market_cap,
        "isin": np.nan,
        "cusip": np.nan,
        "figi": np.nan,
        "composite_figi": np.nan,
        "shareclass_figi": np.nan,
        "delisted": False,
    }


def load_feed(name: str) -> pd.DataFrame | None:
    """
    Load one exchange feed without junk rows; None when it is unreachable or malformed.

    Args:
        name (str): The feed name (nasdaq, nyse, amex).

    Returns:
        pd.DataFrame | None: The feed by symbol, with exchange and market.
    """
    try:
        feed = pd.read_json(FEED_URL.format(name), dtype=False)
    except Exception as error:  # noqa: BLE001
        print(f"{name}: feed skipped ({type(error).__name__}: {error})")
        return None
    if len(feed) < 100 or not {"symbol", "name"} <= set(feed.columns):
        print(f"{name}: feed skipped, it looks broken ({len(feed)} rows)")
        return None
    # The feeds write share classes as BRK/A, the database as BRK-A.
    feed["symbol"] = (
        feed["symbol"].astype(str).str.strip().str.replace("/", "-", regex=False)
    )
    feed["name"] = feed["name"].astype(str).str.strip()
    invalid = ~feed["symbol"].str.match(VALID_SYMBOL)
    etp = feed["name"].str.contains(ETP_NAME, case=False, regex=True)
    dated = feed["name"].str.contains(DATED_NAME.pattern, case=False, regex=True)
    if invalid.any():
        print(
            f"{name}: skipping malformed symbols {feed.loc[invalid, 'symbol'].tolist()}"
        )
    if etp.any():
        print(
            f"{name}: skipping exchange-traded products "
            f"{feed.loc[etp & ~invalid, 'symbol'].tolist()}"
        )
    if dated.any():
        print(
            f"{name}: skipping warrants, rights and dated notes "
            f"{feed.loc[dated & ~invalid & ~etp, 'symbol'].tolist()}"
        )
    feed = feed[~invalid & ~etp & ~dated & (feed["name"] != "")]
    feed = feed.drop_duplicates("symbol").set_index("symbol")
    feed["exchange"], feed["market"] = FEEDS[name]
    return feed


def read_equities(database: str) -> pd.DataFrame:
    """
    The equities as text, so untouched rows are written back byte for byte.

    Args:
        database (str): The database folder.

    Returns:
        pd.DataFrame: The equities by symbol.
    """
    return pd.concat(
        [
            pd.read_csv(path, index_col=0, dtype=str, keep_default_na=False)
            for path in sorted(glob.glob(f"{database}/equities/*.csv"))
        ]
    )


def get_other_symbols(database: str) -> set[str]:
    """
    The symbols of the other asset classes; a symbol belongs to one class only.

    Args:
        database (str): The database folder.

    Returns:
        set[str]: The symbols.
    """
    symbols: set[str] = set()
    paths = glob.glob(f"{database}/etfs/*.csv") + glob.glob(f"{database}/funds/*.csv")
    paths += [
        f"{database}/{asset}.csv"
        for asset in ("indices", "currencies", "cryptos", "moneymarkets")
    ]
    for path in paths:
        symbols |= set(
            pd.read_csv(path, usecols=[0], dtype=str, keep_default_na=False).iloc[:, 0]
        )
    return symbols


def find_non_shares(frame: pd.DataFrame) -> pd.Series:
    """
    Mark the rows of an equities file that are not company shares.

    Args:
        frame (pd.DataFrame): An equities file.

    Returns:
        pd.Series: True for each row that is not a company share.
    """
    isin_symbol = frame.index.to_series().where(
        frame.index.str.match(r"^[A-Z]{2}\d{6,}"), ""
    )
    isin = frame["isin"].where(frame["isin"] != "", isin_symbol)
    return pd.Series(
        [
            check_non_share(name, country, code)
            for name, country, code in zip(
                frame["name"], frame["country"], isin, strict=True
            )
        ],
        index=frame.index,
    )
