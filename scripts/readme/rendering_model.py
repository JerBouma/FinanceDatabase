"""Rendering Model"""

__docformat__ = "google"

from scripts.readme.statistics_model import AssetStats, format_number

START = "<!-- STATISTICS:START"
END = "<!-- STATISTICS:END -->"
HEADER = (
    "<!-- STATISTICS:START (generated weekly by scripts/update_readme_stats.py "
    "from database/; edits between these markers are overwritten) -->"
)


def render(stats: list[AssetStats]) -> str:
    """
    Render the statistics section of the README as Markdown.
    """
    total = sum(s.symbols for s in stats)

    def format_cell(value: int | None) -> str:
        return format_number(value) if value is not None else "–"

    rows = [
        "| | Asset class | Symbols | Exchanges | Coverage |",
        "| :-: | :-- | --: | --: | :-- |",
    ]
    for s in stats:
        rows.append(
            f"| {s.icon} | **{s.name}** | {format_number(s.symbols)} | "
            f"{format_cell(s.exchanges)} | {' · '.join(s.coverage)} |"
        )
    rows.append(f"| | **Total** | **{format_number(total)}** | | |")

    return "\n".join(
        [
            HEADER,
            "",
            *rows,
            "",
            END,
        ]
    )
