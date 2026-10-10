"""Remove the rows of database/equities that are not company shares.

Run by the Add-New-Ticker job of `.github/workflows/database_update.yml` after the
listings are updated, and locally with

    python scripts/remove_non_shares.py [--dry-run] [--database database]

Equities only hold the shares of companies. Rows whose name has a maturity or expiry
date, a strike, or a coupon without any share wording, and rows with an international
(XS) ISIN are bonds, notes, warrants or certificates and are removed, whichever process
added them. See scripts/listings/helpers.py for the rule.
"""

__docformat__ = "google"

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.listings.listings_controller import remove_non_shares  # noqa: E402

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--database", default="database")
    parser.add_argument("--dry-run", action="store_true")
    arguments = parser.parse_args()
    removed = remove_non_shares(arguments.database, arguments.dry_run)
    print(f"{len(removed)} rows that are not company shares", end="")
    print(" found:" if arguments.dry_run else " removed:" if removed else ".")
    for row in removed:
        print(f"  {row}")
