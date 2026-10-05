"""Add newly listed equities and ETFs from official exchange symbol directories.

Run weekly by `.github/workflows/database_update.yml` (Add-New-Ticker job) and locally with

    python scripts/update_listings.py [--dry-run] [--database database]

Sources (all public, official):

- Nasdaq Trader symbol directory: US-listed ETFs (US equities are added by the workflow's
  own NASDAQ/NYSE/AMEX step).
- HKEX List of Securities: Hong Kong equities, REITs and ETPs (HKD counters).
- NSE equity and ETF lists: India.
- JPX list of TSE-listed issues: Japan equities and ETFs.
- ASX listed companies: Australia equities with their GICS industry group.
- TSX / TSXV company directory: Canada equities and ETFs.

Safety rules, so an automated run never adds junk or duplicates:

- Each source is fetched, parsed and applied on its own. A blocked download (bot check, rate
  limit, HTTP error, timeout), a format change, a suspiciously short list or an unexpected
  error skips that source only: its partial changes are rolled back and the other sources
  continue. Enrichment failures (OpenFIGI, optional lists) only mean fewer filled fields.
  An error outside the sources writes nothing and still exits cleanly, so this script can
  never fail the weekly pipeline (the workflow step is also `continue-on-error`).
- Rows are only ever added; nothing is removed. A symbol is added only when it exists in no
  asset class at all (no cross-asset collisions).
- A candidate is skipped when an existing row in the same exchange file has the same symbol
  apart from separators (`HCO.P.V` vs `HCO-P.V`) and the same company name.
- Ticker changes: when a new listing matches a live existing row in the same exchange file by
  ISIN or company name, and that row's symbol is no longer on the exchange's official list,
  the old row is marked `delisted=True`. More than `MAX_DELISTINGS_PER_SOURCE` such changes
  for one source is treated as a parsing problem and no rows are delisted for that source.
- Values the source does not provide are left blank, never guessed.

Enrichment of new rows (each step is optional: if it fails, rows are still added):

- OpenFIGI (open FIGI standard, https://www.openfigi.com): FIGI, composite FIGI and share-class
  FIGI for new equities, and the full instrument name for HKEX rows (HKEX only publishes
  abbreviations) when OpenFIGI's name is complete (its names are cut at 28 characters). A row
  whose OpenFIGI security type contradicts its asset class (an ETP among equities, a common
  stock among ETFs) is filed under the asset class of its security type. Set OPENFIGI_API_KEY
  for higher rate limits.
- Sector / industry group / industry from the exchange's own classification (JPX 33 sectors,
  NSE Nifty Total Market industries), translated through the existing rows of the same file:
  a level is filled only when >= 90% of >= 10 existing rows with that classification agree.
- ETF family (issuer) from the first words of the name, when >= 95% of existing ETFs with the
  same opening words belong to one family.
- US ETFs (needs SEC_USER_AGENT_EMAIL, SEC's required contact for automated access): the
  summary is the investment objective quoted from the fund's latest summary prospectus
  (form 497K) on SEC EDGAR, and a missing family is taken from the fund's SEC registrant
  (trust) when >= 90% of >= 5 existing ETFs of that registrant share one family.
- Every other new row gets a factual summary built only from its known fields (name, exchange,
  ticker, currency, issuer, categories, sector, country), so nothing is invented.
"""

__docformat__ = "google"

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.listings.listings_controller import main  # noqa: E402

if __name__ == "__main__":
    main()
