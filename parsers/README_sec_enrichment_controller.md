# SEC Enrichment Controller

`sec_enrichment_controller.py` enriches missing US security `name` and `currency` fields in FinanceDatabase CSV files using public SEC data. It can also upgrade conservative fund and money-market names that are only generic share-class labels, such as `A Shares`, `Class A`, or `Administrative Class Shares`, when SEC series/class data provides the full fund series name.

The controller is intentionally conservative. It prefers a smaller number of high-confidence updates over broad coverage, because US tickers can be reused after a security is delisted. When a row already has stronger identifiers such as `isin`, `cusip`, `figi`, `composite_figi`, or `shareclass_figi`, the controller will not auto-apply a ticker-only SEC match unless SEC-side identifiers corroborate the row.

## What It Reads

Default target files:

```bash
database/equities.csv
database/etfs.csv
database/funds.csv
database/moneymarkets.csv
```

SEC sources:

- `company_tickers_exchange.json` for operating-company ticker, name, CIK, and exchange data.
- `company_tickers_mf.json` for mutual fund ticker, CIK, series, and class identifiers.
- SEC investment company series/class CSVs for current and historical fund class names and tickers.
- SEC Form N-CEN quarterly datasets for fund and ETF ticker/name/exchange context.

## SEC User Agent

SEC requests require a descriptive `User-Agent`. The SEC asks automated clients to identify the application and provide contact information so they can reach the operator if traffic causes problems.

Use a real email or operational contact in your own runs:

```bash
export SEC_USER_AGENT="FinanceDatabase your-email@example.com"
```

You can also pass it per command:

```bash
python parsers/sec_enrichment_controller.py \
  --user-agent "FinanceDatabase your-email@example.com"
```

## Create An Environment

From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install pandas requests
```

For development and tests:

```bash
python -m pip install pytest ruff pytest-recording pytest-recorder pytest-mock
```

## Dry Run

Dry run is the default. It downloads/caches SEC data, scans the CSVs, and writes an audit report without changing database files.

```bash
SEC_USER_AGENT="FinanceDatabase your-email@example.com" \
python parsers/sec_enrichment_controller.py
```

Default report:

```bash
.cache/sec_enrichment/sec_enrichment_report.csv
```

Useful shorter dry run while testing:

```bash
SEC_USER_AGENT="FinanceDatabase your-email@example.com" \
python parsers/sec_enrichment_controller.py \
  --datasets database/etfs.csv \
  --start-year 2025 \
  --end-year 2025 \
  --no-include-ncen
```

## Apply Accepted Updates

After reviewing the report, apply only accepted high-confidence updates:

```bash
SEC_USER_AGENT="FinanceDatabase your-email@example.com" \
python parsers/sec_enrichment_controller.py --apply
```

Apply to a subset:

```bash
SEC_USER_AGENT="FinanceDatabase your-email@example.com" \
python parsers/sec_enrichment_controller.py \
  --datasets database/funds.csv database/moneymarkets.csv \
  --apply
```

Use a custom cache and report path:

```bash
SEC_USER_AGENT="FinanceDatabase your-email@example.com" \
python parsers/sec_enrichment_controller.py \
  --cache-dir .cache/sec_enrichment \
  --report .cache/sec_enrichment/funds_report.csv \
  --datasets database/funds.csv
```

## Report Columns

The report is a CSV with these columns:

- `dataset`: source FinanceDatabase CSV path.
- `symbol`: normalized symbol used for SEC matching.
- `status`: `accepted` or `review`.
- `proposed_name`: name that would be filled, if missing.
- `proposed_currency`: currency that would be filled, usually `USD`.
- `source`: SEC source that produced the candidate.
- `source_identifiers`: SEC identifiers available for the candidate, such as series/class IDs.
- `confidence`: confidence label, such as `high` or `high_identifier_match`.
- `reason`: why the row was accepted or routed for review.

Rows with `status=review` are never applied automatically.

## Matching Rules

The controller only considers rows that appear US-like:

- `country` is `United States`;
- or `exchange` is a known US exchange code;
- or the symbol has no foreign suffix such as `.L`, `.PA`, `.TO`, or `.KS`.

Accepted updates require:

- exact normalized ticker match;
- suitable SEC source for the dataset type;
- no conflicting SEC names for that ticker;
- no row identifier conflict.

Ticker reuse protection:

- If a row has `isin`, `cusip`, `figi`, `composite_figi`, or `shareclass_figi`, and the SEC candidate does not provide a matching identifier, the row is marked `review`.
- If SEC returns multiple different names for the same ticker, the row is marked `review` with `reason=ambiguous_sec_names`.
- Existing non-empty `currency` values are never overwritten.
- Existing non-empty `name` values are overwritten only when the current fund or money-market name is a generic class label and SEC series/class data provides a fuller name. These rows use `reason=incomplete_name_sec_series_class_match`.

Incomplete name examples:

```csv
CADXX,ADMINISTRATIVE CLASS SHARES,USD,,,NAS
HCAXX,A Shares,USD,,,NAS
HCMXX,Class A,USD,,,NAS
```

When SEC has both a `Series Name` and `Class Name`, the proposed name is composed as:

```text
Series Name - Class Name
```

If the SEC `Series Name` is generic, such as `Money Market Fund`, `Municipal Money Market Fund`, `Government Portfolio`, `Institutional Money Market Series`, `Money Market Portfolio`, `Primary Fund`, or `Prime Portfolio`, the controller prefixes the SEC `Entity Name`:

```text
Entity Name - Series Name - Class Name
```

For example:

```text
Commerce Capital Government Money Market Fund - Administrative Class Shares
Eagle Cash Trust - Money Market Fund - Class A
Neuberger Berman Institutional Liquidity Funds - Prime Portfolio - Premier
Prudential Institutional Liquidity Portfolio Inc - Institutional Money Market Series - Class I
Reserve Funds /Ny/ - Primary Fund - Liquidity Class V
```

Currency handling:

- SEC source files generally do not provide trading currency directly.
- The controller fills missing `currency` as `USD` only when a US SEC listing/context is confirmed.
- This is an inference from SEC-confirmed US context, not a literal SEC currency field.
- For operating companies, US context comes from SEC exchange data such as Nasdaq, NYSE, NYSE Arca, NYSE American, Cboe BZX, or OTC. For SEC investment-company series/class records, US context comes from the fund being present in SEC registered investment-company data and from the FinanceDatabase row passing the US-like row filter.
- If you only want SEC names and no inferred currency fills, review or remove `proposed_currency` values from the report before applying, or run the controller without `--apply` and patch names manually.

## Common Commands

Run a full dry run:

```bash
SEC_USER_AGENT="FinanceDatabase your-email@example.com" \
python parsers/sec_enrichment_controller.py
```

Run full dry run without N-CEN datasets:

```bash
SEC_USER_AGENT="FinanceDatabase your-email@example.com" \
python parsers/sec_enrichment_controller.py --no-include-ncen
```

Run only current and recent series/class data:

```bash
SEC_USER_AGENT="FinanceDatabase your-email@example.com" \
python parsers/sec_enrichment_controller.py \
  --start-year 2023 \
  --end-year 2025
```

Apply after review:

```bash
SEC_USER_AGENT="FinanceDatabase your-email@example.com" \
python parsers/sec_enrichment_controller.py --apply
```

Run tests for this controller:

```bash
pytest tests/test_sec_enrichment_controller.py -q
```

Run lint for this controller:

```bash
ruff check parsers/sec_enrichment_controller.py tests/test_sec_enrichment_controller.py
```

## Reviewing Results

Recommended workflow:

1. Run a dry run.
2. Inspect `accepted` rows in the report.
3. Inspect all `review` rows, especially rows with existing `isin`, `cusip`, or FIGI fields.
4. Run `--apply` only after the accepted rows look correct.
5. Review the git diff for the target CSVs.
6. Run CSV parsing/tests before committing.

Useful report filters:

```bash
python - <<'PY'
import pandas as pd

report = pd.read_csv(".cache/sec_enrichment/sec_enrichment_report.csv")
print(report["status"].value_counts(dropna=False))
print(report["reason"].value_counts(dropna=False))
print(report[report["status"] == "review"].head(25))
PY
```

## Limitations

- SEC-only data is precise but incomplete for some delisted operating companies.
- Historical fund coverage is stronger than historical operating-company ticker coverage because SEC series/class files include historical investment company classes.
- Some SEC sources provide fund series/class identifiers but not CUSIP or ISIN.
- Ticker-only matches for rows with existing identifiers are deliberately routed to manual review.
- Non-US securities are intentionally skipped.
