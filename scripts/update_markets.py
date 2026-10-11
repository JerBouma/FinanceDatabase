"""Update cryptocurrencies, currencies and indices from public market sources.

Run weekly by `.github/workflows/database_update.yml` and locally with

    python scripts/update_markets.py [--dry-run] [--database database]

Sources (all public):

- CoinGecko: the coins by market cap and every listed coin. Coins in the top 500 get the
  quote currencies most coins trade in (USD, EUR, ...); coins CoinGecko no longer lists at
  all are removed.
- ISO 4217 (SIX, the maintenance agency): new currencies get the pairs most currencies
  have; withdrawn currencies (e.g. HRK, BGN after the euro) are removed.
- Euronext: the indices it publishes on Amsterdam, Paris, Brussels, Lisbon, Oslo and Milan.

Each update runs on its own: a failing source is skipped and logged, removals affecting an
implausible share of a file are not applied, and the script never fails the pipeline.
"""

__docformat__ = "google"

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.markets.markets_controller import main  # noqa: E402

if __name__ == "__main__":
    main()
