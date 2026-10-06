"""Rendering Model"""

__docformat__ = "google"

import datetime as dt
from urllib.parse import quote

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


def render(stats: list[AssetStats], today: dt.date) -> str:
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
            END,
        ]
    )
