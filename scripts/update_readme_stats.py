"""Regenerate the statistics section of README.md from database/.

Run by the Update-README-Statistics job of `.github/workflows/database_update.yml` and locally:

    python scripts/update_readme_stats.py [--readme README.md] [--database database]

Everything between the two marker comments in README.md is replaced:

    <!-- STATISTICS:START ... -->
    ...generated...
    <!-- STATISTICS:END -->

Without the markers nothing is changed and the script exits cleanly, so a README edit can never
fail the weekly pipeline. The section only uses what GitHub renders in a README: badges and a
Markdown table.
"""

__docformat__ = "google"

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.readme.readme_controller import main  # noqa: E402

if __name__ == "__main__":
    main()
