"""Statistics Model"""

__docformat__ = "google"

import glob
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd


def format_number(number: int) -> str:
    """
    Format a number with thousands separators.
    """
    return f"{number:,}"


@dataclass
class AssetStats:
    """
    Statistics for one asset class.
    """

    icon: str
    name: str
    symbols: int
    listed: int | None = None  # None when the asset class has no delisted flag
    exchanges: int | None = None
    coverage: list[str] = field(default_factory=list)


def read(paths: list[str], columns: list[str]) -> pd.DataFrame:
    """
    Read only the needed columns as text (keeps memory low; 'NA' stays a ticker).
    """
    frames = []
    for path in paths:
        available = pd.read_csv(path, nrows=0).columns
        frames.append(
            pd.read_csv(
                path,
                usecols=[c for c in columns if c in available],
                dtype=str,
                keep_default_na=False,
            )
        )
    data = pd.concat(frames, ignore_index=True)
    for column in columns:
        if column not in data:
            data[column] = ""
    return data


def count_distinct(series: pd.Series) -> int:
    """
    Count the distinct non-empty values of a column.
    """
    return series[series.str.strip() != ""].nunique()


def collect(database: str) -> tuple[list[AssetStats], dict[str, pd.Series]]:
    """
    Per-asset-class statistics plus the breakdowns shown in the collapsible section.
    """
    root = Path(database)
    equities = read(
        sorted(glob.glob(f"{root}/equities/*.csv")),
        ["symbol", "sector", "industry", "country", "exchange", "delisted"],
    )
    etfs = read(
        sorted(glob.glob(f"{root}/etfs/*.csv")),
        ["symbol", "family", "category_group", "category", "exchange", "delisted"],
    )
    funds = read(
        sorted(glob.glob(f"{root}/funds/*.csv")),
        ["symbol", "family", "category_group", "category", "exchange"],
    )
    indices = read([f"{root}/indices.csv"], ["symbol", "category", "exchange"])
    currencies = read(
        [f"{root}/currencies.csv"], ["symbol", "base_currency", "quote_currency"]
    )
    cryptos = read([f"{root}/cryptos.csv"], ["symbol", "cryptocurrency", "currency"])
    money = read([f"{root}/moneymarkets.csv"], ["symbol", "family", "exchange"])

    live_equities = equities[equities["delisted"] != "True"]
    live_etfs = etfs[etfs["delisted"] != "True"]
    currency_codes = pd.concat(
        [currencies["base_currency"], currencies["quote_currency"]]
    )
    stats = [
        AssetStats(
            "🏢",
            "Equities",
            len(equities),
            len(live_equities),
            count_distinct(equities["exchange"]),
            [
                f"{count_distinct(equities['sector'])} sectors",
                f"{count_distinct(equities['industry'])} industries",
                f"{count_distinct(equities['country'])} countries",
            ],
        ),
        AssetStats(
            "📦",
            "ETFs",
            len(etfs),
            len(live_etfs),
            count_distinct(etfs["exchange"]),
            [
                f"{format_number(count_distinct(etfs['family']))} issuers",
                f"{count_distinct(etfs['category'])} categories",
            ],
        ),
        AssetStats(
            "💼",
            "Funds",
            len(funds),
            None,
            count_distinct(funds["exchange"]),
            [
                f"{format_number(count_distinct(funds['family']))} fund families",
                f"{count_distinct(funds['category'])} categories",
            ],
        ),
        AssetStats(
            "📈",
            "Indices",
            len(indices),
            None,
            count_distinct(indices["exchange"]),
            [f"{count_distinct(indices['category'])} categories"],
        ),
        AssetStats(
            "💱",
            "Currencies",
            len(currencies),
            None,
            None,
            [f"{count_distinct(currency_codes)} currencies"],
        ),
        AssetStats(
            "🪙",
            "Cryptocurrencies",
            len(cryptos),
            None,
            None,
            [
                f"{count_distinct(cryptos['cryptocurrency'])} coins",
                f"{count_distinct(cryptos['currency'])} quote currencies",
            ],
        ),
        AssetStats(
            "🏦",
            "Money Markets",
            len(money),
            None,
            count_distinct(money["exchange"]),
            [f"{count_distinct(money['family'])} fund families"],
        ),
    ]

    def count_values(series: pd.Series) -> pd.Series:
        return series[series.str.strip() != ""].value_counts()

    breakdowns = {
        "sectors": count_values(live_equities["sector"]),
        "countries": count_values(live_equities["country"]),
        "exchanges": count_values(live_equities["exchange"]),
        "etf_groups": count_values(live_etfs["category_group"]),
    }
    return stats, breakdowns
