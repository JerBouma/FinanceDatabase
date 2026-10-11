"""Regenerate the statistics section of README.md (see scripts/README.md)."""

__docformat__ = "google"

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.readme.readme_controller import main  # noqa: E402

if __name__ == "__main__":
    main()
