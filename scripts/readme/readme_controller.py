"""README Module"""

__docformat__ = "google"

import argparse
import datetime as dt
import re
from pathlib import Path

from scripts.readme.rendering_model import END, START, render
from scripts.readme.statistics_model import collect, format_number


def update(readme: Path, database: str, today: dt.date | None = None) -> bool:
    """
    Rewrite the marked section; returns False (and changes nothing) without markers.
    """
    text = readme.read_text(encoding="utf-8")
    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), re.S)
    if not pattern.search(text):
        print(f"No statistics markers found in {readme}; nothing changed.")
        return False
    stats = collect(database)
    section = render(stats, today or dt.date.today())
    readme.write_text(pattern.sub(lambda _: section, text, count=1), encoding="utf-8")
    print(
        f"{readme} statistics refreshed ({format_number(sum(s.symbols for s in stats))} symbols)."
    )
    return True


def main() -> None:
    """
    Regenerate the README statistics from the command line; a failure is reported, never raised.
    """
    parser = argparse.ArgumentParser(
        description="Regenerate the statistics section of README.md from database/."
    )
    parser.add_argument("--readme", default="README.md")
    parser.add_argument("--database", default="database")
    args = parser.parse_args()
    try:
        update(Path(args.readme), args.database)
    except Exception as error:  # never fail the weekly pipeline over the README
        print(f"README statistics not refreshed ({type(error).__name__}: {error})")
