"""Fail when an equity's categories are not valid GICS (see scripts/README.md)."""

__docformat__ = "google"

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.validation.validation_controller import run_gics_check  # noqa: E402

if __name__ == "__main__":
    run_gics_check()
