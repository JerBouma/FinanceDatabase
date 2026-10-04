"""Regenerate the statistics section of README.md from database/.

Run by the Update-README-Statistics job of `.github/workflows/database_update.yml` and locally:

    python scripts/update_readme_stats.py [--readme README.md] [--database database]

Everything between the two marker comments in README.md is replaced:

    <!-- STATISTICS:START ... -->
    ...generated...
    <!-- STATISTICS:END -->

Without the markers nothing is changed and the script exits cleanly, so a README edit can never
fail the weekly pipeline. The section only uses what GitHub renders in a README: badges,
Markdown tables, a collapsible <details> block and a Mermaid pie chart.
"""

from __future__ import annotations

import argparse
import datetime as dt
import glob
import re
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import quote

import pandas as pd

START = "<!-- STATISTICS:START"
END = "<!-- STATISTICS:END -->"
HEADER = (
    "<!-- STATISTICS:START (generated weekly by scripts/update_readme_stats.py "
    "from database/; edits between these markers are overwritten) -->"
)


@dataclass
class AssetStats:
    """Statistics for one asset class."""

    icon: str
    name: str
    symbols: int
    listed: int | None = None  # None when the asset class has no delisted flag
    exchanges: int | None = None
    coverage: list[str] = field(default_factory=list)


def fmt(number: int) -> str:
    return f"{number:,}"


def read(paths: list[str], columns: list[str]) -> pd.DataFrame:
    """Read only the needed columns as text (keeps memory low; 'NA' stays a ticker)."""
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


def distinct(series: pd.Series) -> int:
    return series[series.str.strip() != ""].nunique()


def collect(database: str) -> tuple[list[AssetStats], dict[str, pd.Series]]:
    """Per-asset-class statistics plus the breakdowns shown in the collapsible section."""
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
            distinct(equities["exchange"]),
            [
                f"{distinct(equities['sector'])} sectors",
                f"{distinct(equities['industry'])} industries",
                f"{distinct(equities['country'])} countries",
            ],
        ),
        AssetStats(
            "📦",
            "ETFs",
            len(etfs),
            len(live_etfs),
            distinct(etfs["exchange"]),
            [
                f"{fmt(distinct(etfs['family']))} issuers",
                f"{distinct(etfs['category'])} categories",
            ],
        ),
        AssetStats(
            "💼",
            "Funds",
            len(funds),
            None,
            distinct(funds["exchange"]),
            [
                f"{fmt(distinct(funds['family']))} fund families",
                f"{distinct(funds['category'])} categories",
            ],
        ),
        AssetStats(
            "📈",
            "Indices",
            len(indices),
            None,
            distinct(indices["exchange"]),
            [f"{distinct(indices['category'])} categories"],
        ),
        AssetStats(
            "💱",
            "Currencies",
            len(currencies),
            None,
            None,
            [f"{distinct(currency_codes)} currencies"],
        ),
        AssetStats(
            "🪙",
            "Cryptocurrencies",
            len(cryptos),
            None,
            None,
            [
                f"{distinct(cryptos['cryptocurrency'])} coins",
                f"{distinct(cryptos['currency'])} quote currencies",
            ],
        ),
        AssetStats(
            "🏦",
            "Money Markets",
            len(money),
            None,
            distinct(money["exchange"]),
            [f"{distinct(money['family'])} fund families"],
        ),
    ]

    def count(series: pd.Series) -> pd.Series:
        return series[series.str.strip() != ""].value_counts()

    breakdowns = {
        "sectors": count(live_equities["sector"]),
        "countries": count(live_equities["country"]),
        "exchanges": count(live_equities["exchange"]),
        "etf_groups": count(live_etfs["category_group"]),
    }
    return stats, breakdowns


def badge(label: str, message: str, color: str) -> str:
    """A static shields.io badge (only the image is fetched; no data leaves the repo)."""

    def escape(text: str) -> str:
        # shields.io treats '-' and '_' as separators; doubling them keeps them literal.
        return quote(text.replace("-", "--").replace("_", "__"), safe="")

    url = f"https://img.shields.io/badge/{escape(label)}-{escape(message)}-{color}"
    return f"![{label}]({url}?style=flat-square)"


def count_table(column: str, unit: str, counts: pd.Series, top: int) -> str:
    """A compact two-column table (name, count) of the largest groups, the rest as 'Other'."""
    lines = [f"| {column} | {unit} |", "| :-- | --: |"]
    for name, value in counts.head(top).items():
        lines.append(f"| {name} | {fmt(int(value))} |")
    if len(counts) > top:
        rest = fmt(int(counts.iloc[top:].sum()))
        lines.append(f"| *Other ({len(counts) - top})* | {rest} |")
    return "\n".join(lines)


def render(
    stats: list[AssetStats], breakdowns: dict[str, pd.Series], today: dt.date
) -> str:
    total = sum(s.symbols for s in stats)
    equities = stats[0]
    countries = int(equities.coverage[2].split()[0])
    badges = " ".join(
        [
            badge("symbols", fmt(total), "0A66C2"),
            badge("equities", fmt(equities.symbols), "2EA44F"),
            badge("ETFs", fmt(stats[1].symbols), "8250DF"),
            badge("countries", str(countries), "BF8700"),
            badge("updated", today.isoformat(), "57606A"),
        ]
    )

    def cell(value: int | None) -> str:
        return fmt(value) if value is not None else "–"

    rows = [
        "| | Asset class | Symbols | Actively listed | Exchanges | Coverage |",
        "| :-: | :-- | --: | --: | --: | :-- |",
    ]
    for s in stats:
        rows.append(
            f"| {s.icon} | **{s.name}** | {fmt(s.symbols)} | {cell(s.listed)} | "
            f"{cell(s.exchanges)} | {' · '.join(s.coverage)} |"
        )
    rows.append(f"| | **Total** | **{fmt(total)}** | | | |")

    pie = ["```mermaid", "pie showData", "    title Symbols per asset class"]
    pie += [
        f'    "{s.name}" : {s.symbols}' for s in sorted(stats, key=lambda s: -s.symbols)
    ]
    pie.append("```")

    sectors = count_table("Sector", "Equities", breakdowns["sectors"], 11)
    countries_table = count_table("Country", "Equities", breakdowns["countries"], 10)
    exchange_table = count_table("Exchange", "Equities", breakdowns["exchanges"], 10)
    etf_table = count_table("ETF category", "ETFs", breakdowns["etf_groups"], 10)

    return "\n".join(
        [
            HEADER,
            "",
            '<div align="center">',
            "",
            badges,
            "",
            "</div>",
            "",
            *rows,
            "",
            "<details>",
            "<summary><b>📊 More statistics</b>: composition, sectors, countries, exchanges and ETF categories</summary>",
            "",
            *pie,
            "",
            "<table>",
            "<tr>",
            '<td valign="top">',
            "",
            sectors,
            "",
            "</td>",
            '<td valign="top">',
            "",
            countries_table,
            "",
            "</td>",
            "</tr>",
            "<tr>",
            '<td valign="top">',
            "",
            exchange_table,
            "",
            "</td>",
            '<td valign="top">',
            "",
            etf_table,
            "",
            "</td>",
            "</tr>",
            "</table>",
            "",
            "*Actively listed excludes symbols flagged as delisted. Sector, country and exchange "
            "counts cover actively listed equities; exchange codes match the files in "
            "[`database/equities`](database/equities).*",
            "",
            "</details>",
            "",
            END,
        ]
    )


def update(readme: Path, database: str, today: dt.date | None = None) -> bool:
    """Rewrite the marked section; returns False (and changes nothing) without markers."""
    text = readme.read_text(encoding="utf-8")
    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), re.S)
    if not pattern.search(text):
        print(f"No statistics markers found in {readme}; nothing changed.")
        return False
    stats, breakdowns = collect(database)
    section = render(stats, breakdowns, today or dt.date.today())
    readme.write_text(pattern.sub(lambda _: section, text, count=1), encoding="utf-8")
    print(
        f"{readme} statistics refreshed ({fmt(sum(s.symbols for s in stats))} symbols)."
    )
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--readme", default="README.md")
    parser.add_argument("--database", default="database")
    args = parser.parse_args()
    try:
        update(Path(args.readme), args.database)
    except Exception as error:  # never fail the weekly pipeline over the README
        print(f"README statistics not refreshed ({type(error).__name__}: {error})")


if __name__ == "__main__":
    main()
