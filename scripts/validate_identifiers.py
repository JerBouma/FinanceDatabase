"""Report and optionally repair or clear invalid security identifiers in database/.

Run locally (and by the CI identifier gate through its test):

    python scripts/validate_identifiers.py [paths ...] [--apply] [--report-file report.csv]

Without --apply nothing is changed.
"""

__docformat__ = "google"

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.validation.validation_controller import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
