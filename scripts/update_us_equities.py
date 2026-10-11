"""Add new US equities and refresh market cap tiers (see scripts/README.md)."""

__docformat__ = "google"

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.equities.equities_controller import run_us_equities_update  # noqa: E402

if __name__ == "__main__":
    run_us_equities_update()
