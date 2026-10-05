"""Rendering Model"""

__docformat__ = "google"

import datetime as dt
from urllib.parse import quote

import pandas as pd

from scripts.readme.statistics_model import AssetStats, format_number

START = "<!-- STATISTICS:START"
END = "<!-- STATISTICS:END -->"
HEADER = (
    "<!-- STATISTICS:START (generated weekly by scripts/update_readme_stats.py "
    "from database/; edits between these markers are overwritten) -->"
)


def create_badge(label: str, message: str, color: str) -> str:
    """
    A static shields.io badge (only the image is fetched; no data leaves the repo).
    """

    def escape_text(text: str) -> str:
        # shields.io treats '-' and '_' as separators; doubling them keeps them literal.
        return quote(text.replace("-", "--").replace("_", "__"), safe="")

    url = f"https://img.shields.io/badge/{escape_text(label)}-{escape_text(message)}-{color}"
    return f"![{label}]({url}?style=flat-square)"


def create_count_table(column: str, unit: str, counts: pd.Series, top: int) -> str:
    """
    A compact two-column table (name, count) of the largest groups, the rest as 'Other'.
    """
    lines = [f"| {column} | {unit} |", "| :-- | --: |"]
    for name, value in counts.head(top).items():
        lines.append(f"| {name} | {format_number(int(value))} |")
    if len(counts) > top:
        rest = format_number(int(counts.iloc[top:].sum()))
        lines.append(f"| *Other ({len(counts) - top})* | {rest} |")
    return "\n".join(lines)


def render(
    stats: list[AssetStats], breakdowns: dict[str, pd.Series], today: dt.date
) -> str:
    """
    Render the statistics section of the README as Markdown.
    """
    total = sum(s.symbols for s in stats)
    equities = stats[0]
    countries = int(equities.coverage[2].split()[0])
    badges = " ".join(
        [
            create_badge("symbols", format_number(total), "0A66C2"),
            create_badge("equities", format_number(equities.symbols), "2EA44F"),
            create_badge("ETFs", format_number(stats[1].symbols), "8250DF"),
            create_badge("countries", str(countries), "BF8700"),
            create_badge("updated", today.isoformat(), "57606A"),
        ]
    )

    def format_cell(value: int | None) -> str:
        return format_number(value) if value is not None else "–"

    rows = [
        "| | Asset class | Symbols | Actively listed | Exchanges | Coverage |",
        "| :-: | :-- | --: | --: | --: | :-- |",
    ]
    for s in stats:
        rows.append(
            f"| {s.icon} | **{s.name}** | {format_number(s.symbols)} | {format_cell(s.listed)} | "
            f"{format_cell(s.exchanges)} | {' · '.join(s.coverage)} |"
        )
    rows.append(f"| | **Total** | **{format_number(total)}** | | | |")

    pie = ["```mermaid", "pie showData", "    title Symbols per asset class"]
    pie += [
        f'    "{s.name}" : {s.symbols}' for s in sorted(stats, key=lambda s: -s.symbols)
    ]
    pie.append("```")

    sectors = create_count_table("Sector", "Equities", breakdowns["sectors"], 11)
    countries_table = create_count_table(
        "Country", "Equities", breakdowns["countries"], 10
    )
    exchange_table = create_count_table(
        "Exchange", "Equities", breakdowns["exchanges"], 10
    )
    etf_table = create_count_table("ETF category", "ETFs", breakdowns["etf_groups"], 10)

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
