# Scripts

Repository tooling that keeps `database/` current and checks it. None of it ships with the
`financedatabase` package. The code follows the package's layout: one folder per task, with
`helpers.py` for small shared functions, `*_model.py` files for the data logic and one
`*_controller.py` that runs it. The files directly in this folder are the entry points.

| Entry point | Runs | What it does |
|---|---|---|
| `update_us_equities.py` | weekly (Add-New-Ticker) | New NASDAQ, NYSE and NYSE American equities and market cap tiers |
| `update_listings.py` | weekly (Add-New-Ticker) | New equities and ETFs from official exchange directories |
| `update_markets.py` | weekly (Add-New-Ticker) | Cryptocurrencies, currencies and indices |
| `remove_non_shares.py` | weekly (Add-New-Ticker) | Removes equities that are not company shares |
| `check_database.py` | weekly, before the commit | Undoes an update that broke the database (`--restore`) |
| `update_compression.py` | after every update | Regenerates `compression/` from `database/` |
| `update_readme_stats.py` | after every update | Regenerates the statistics section of `README.md` |
| `check_categories.py` | after every update | Fails when an equity's categories are not in `categories.json` |
| `validate_identifiers.py` | locally and in the test suite | Reports (and with `--apply` repairs) invalid identifiers |

Every weekly script runs with `--dry-run` (where offered) and `--database database` locally,
for example `python scripts/update_listings.py --dry-run`.

## Robustness

- Downloads go through one session that retries network errors, rate limits (429) and
  server errors three times with backoff, honouring `Retry-After`.
- Every source is applied on its own; a failing source is skipped and logged, and no weekly
  script can fail the pipeline (`continue-on-error` and a time limit per step as well).
- Files are only rewritten when their content changes, through a temporary file, so an
  interrupted run never leaves a half-written CSV.
- Implausible changes are not applied: more than 20% of the US market cap tiers at once,
  more than 50 ticker changes per exchange source, removing more than 40% of the coins or
  more than 10 currencies.
- Before the commit, `check_database.py --restore` compares the update with the last commit
  and undoes it when it changed a file's columns, removed a file, added duplicate or empty
  symbols, put a symbol in two asset classes or lost more than 10% of an asset class.

## US equities (`equities/`)

The NASDAQ, NYSE and NYSE American feeds of the US-Stock-Symbols repository add new
equities and refresh the market cap tier of existing ones (Mega Cap ≥ $200B, Large ≥ $10B,
Mid ≥ $2B, Small ≥ $300M, Micro ≥ $50M, else Nano). New tickers are classified through
`us_feed_industries.csv` (Nasdaq feed industry → industry), with the industry group and
sector most common for that industry. Malformed symbols, exchange-traded products and
instruments with an expiry or maturity date (`helpers.DATED_NAME` in `listings/`) are
skipped, and a symbol is never added when another asset class has it.

`remove_non_shares.py` then removes any equities row that is not a company share (a name with
a maturity or expiry date, a strike, a warrant, a coupon without share wording, or an
international XS ISIN; `helpers.check_non_share` in `listings/`), whatever added it.

The equity categories are the database's own: `categories.json` lists every valid sector,
industry group and industry. `category_renames.csv` maps renamed categories to the current
ones, and the US update moves any row that still uses an old name. Two old industries were
split, so a rule decides (`equities/categories_model.py`): savings banks stay banks and other
mortgage lenders become Mortgage Finance; a REIT takes the REIT industry of the property type
its name and summary mention (Diversified REITs for several), and real estate companies that
are not REITs become Real Estate Development & Services.

## Exchange directories (`listings/`)

Sources (all public, official):

- Nasdaq Trader symbol directory: US-listed ETFs.
- HKEX List of Securities: Hong Kong equities, REITs and ETPs (HKD counters).
- NSE equity and ETF lists: India.
- JPX list of TSE-listed issues: Japan equities and ETFs.
- ASX listed companies: Australia equities (rows marked 'Not Applic', trusts and funds, are skipped).
- TSX / TSXV company directory: Canada equities and ETFs.
- Deutsche Börse Xetra all-tradable-instruments file: ETFs and ETCs on Xetra.
- Euronext ETF list: ETFs on Euronext Amsterdam, Paris, Brussels, Lisbon and Oslo.
- SIX Swiss Exchange reference data: ETFs on SIX.

Safety rules, so an automated run never adds junk or duplicates:

- Each source is fetched, parsed and applied on its own. A blocked download, a format change,
  a suspiciously short list or an unexpected error skips that source only: its partial
  changes are rolled back and the other sources continue. The script never fails the pipeline.
- Rows are only added, never removed. A symbol is added only when no asset class has it.
- A candidate is skipped when the same exchange file has the same symbol apart from separators
  (`HCO.P.V` vs `HCO-P.V`) and the same company name.
- Ticker changes: when a new listing matches a live row of the same file by ISIN or name, and
  that row's symbol is no longer on the exchange's list, the old row is marked delisted. More
  than 50 such changes for one source is treated as a parsing problem and nothing is delisted.
- Values a source does not provide are left blank, never guessed.

Enrichment of new rows (each step is optional; if it fails, rows are still added):

- OpenFIGI: FIGIs for new equities, and full names for HKEX rows (HKEX publishes
  abbreviations). A row whose security type contradicts its asset class is re-filed. Set
  `OPENFIGI_API_KEY` for higher rate limits.
- Sector, industry group and industry from the exchange's own classification (JPX sectors,
  NSE industries), when ≥ 90% of ≥ 10 existing rows with that classification agree.
- ETF family from the first words of the name, when ≥ 95% of existing ETFs with those words
  share one family.
- US ETFs (needs `SEC_USER_AGENT_EMAIL`): the investment objective from the fund's summary
  prospectus on SEC EDGAR, and a missing family from the fund's SEC registrant.
- European ETFs: a line of a fund already in the database takes that fund's name, categories
  and family (by ISIN); a new fund takes its full name from its Börse Frankfurt or Euronext
  page, at most 300 lookups per source and run.
- ETF categories (every run, blanks only): a fund's other listings (same ISIN) give its
  category; otherwise the most decisive word or word pair of the name does, when ≥ 85% of
  ≥ 20 ETFs carrying it share the value ('treasury' → Fixed Income / Treasury Bonds). Words
  mostly used by one issuer ('Deka', 'iShares') decide nothing, and a category is only
  given with its own group. On held-out ETFs this is right about 94% of the time.
- Every other new row gets a factual summary built only from its known fields.

## Cryptocurrencies, currencies and indices (`markets/`)

- CoinGecko: coins in the top 500 by market cap get the quote currencies ≥ 90% of coins trade
  in; a coin whose ticker CoinGecko no longer lists at all is removed. A ticker belongs to one
  coin, and tokenized funds are left out.
- ISO 4217 (lists one and three from SIX, the maintenance agency): a new currency gets the
  pairs ≥ 80% of currencies have; withdrawn currencies are removed. Units of account (XSU,
  XUA) are not added.
- Euronext: the indices it publishes on Amsterdam, Paris, Brussels, Lisbon, Oslo and Milan.

Each update runs on its own, removals affecting an implausible share of a file are not
applied, and the script never fails the pipeline.

## Compression, README and checks

- `compression/`: each asset class gets a bz2 CSV and a gzip categories CSV in the layout every
  earlier package version reads, plus Parquet files with the final types
  (`--only datasets|categories`).
- `readme/`: everything between the `STATISTICS:START` and `STATISTICS:END` markers of
  `README.md` is regenerated; without the markers nothing changes.
- `validation/`: the identifier audit (ISIN, CUSIP, FIGI check digits and consistency) and the
  categories check against `categories.json`.
