"""Remove equities that are not company shares (see scripts/README.md)."""

__docformat__ = "google"

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.equities.equities_controller import run_non_share_removal  # noqa: E402

if __name__ == "__main__":
    run_non_share_removal()
