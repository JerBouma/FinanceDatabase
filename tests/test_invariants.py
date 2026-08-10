"""Cross-asset invariants Test Module."""

from __future__ import annotations

import glob
import io
from pathlib import Path

import pandas as pd

import financedatabase as fd
from financedatabase.validation.update_us_equities import (
    ALLOWED_INSTRUMENT_TYPES,
    BACKFILL_SOURCES,
    EQUITY_COLUMNS,
    classify_instrument,
    load_overrides,
)


def test_equities_read_rewrite_is_byte_identical() -> None:
    """The workflow must not alter untouched equity source files."""
    files = sorted(glob.glob("database/equities/*.csv"))
    assert files, "no equities CSVs found under database/equities/"
    source = {path: Path(path).read_bytes() for path in files}

    equities = pd.concat(
        [
            pd.read_csv(
                io.BytesIO(source[path]),
                index_col=0,
                dtype=str,
                keep_default_na=False,
            )
            for path in files
        ]
    )
    equities = equities[~equities.index.duplicated(keep="first")]
    equities = equities[equities.index.notna() & (equities.index != "")]
    equities = equities.sort_index()

    assert "NA" in equities.index
    unknown_exchange = equities["exchange"].isna() | (equities["exchange"] == "")
    regenerated: dict[str, bytes] = {}
    for exchange, group in equities[~unknown_exchange].groupby("exchange"):
        regenerated[f"database/equities/{exchange}.csv"] = group.to_csv(
            lineterminator="\n"
        ).encode()
    if unknown_exchange.any():
        regenerated["database/equities/NAN.csv"] = (
            equities[unknown_exchange].to_csv(lineterminator="\n").encode()
        )

    assert set(regenerated) == set(source)
    changed = [path for path in files if regenerated[path] != source[path]]
    assert not changed, f"workflow read/rewrite changed untouched files: {changed}"


def test_equity_schema_and_instrument_types_are_consistent() -> None:
    """Every exchange uses one schema and only normalized instrument types."""
    expected = ["symbol", *EQUITY_COLUMNS]
    invalid: dict[str, list[str]] = {}
    for path in sorted(Path("database/equities").glob("*.csv")):
        frame = pd.read_csv(path, dtype=str, keep_default_na=False)
        assert list(frame.columns) == expected, f"Unexpected equity schema in {path}"
        values = sorted(
            set(frame["instrument_type"]) - {""} - set(ALLOWED_INSTRUMENT_TYPES)
        )
        if values:
            invalid[str(path)] = values
    assert not invalid, f"Invalid equity instrument types: {invalid}"


def test_targeted_us_equities_have_no_confirmed_non_equity_names() -> None:
    """The recurrent US import must not repopulate confirmed non-equities."""
    overrides = load_overrides()
    offenders: list[tuple[str, str, str]] = []
    for exchange, source_exchange in BACKFILL_SOURCES.items():
        path = Path("database/equities") / f"{exchange}.csv"
        if not path.exists():
            continue
        frame = pd.read_csv(path, dtype=str, keep_default_na=False)
        for row in frame.to_dict(orient="records"):
            symbol = row["symbol"].strip().upper()
            decision = classify_instrument(
                row["name"], overrides.get((source_exchange, symbol))
            )
            current = row["instrument_type"].strip()
            if decision.status == "rejected" or (
                current
                and (
                    decision.status != "accepted" or current != decision.instrument_type
                )
            ):
                offenders.append((exchange, symbol, decision.instrument_type))
    assert not offenders, (
        "Confirmed non-equity rows remain in targeted US equity files: "
        f"{offenders[:20]} ({len(offenders)} total)"
    )


def _load(asset: str):
    """Helper: instantiate the asset class with local data."""
    cls = {
        "equities": fd.Equities,
        "etfs": fd.ETFs,
        "funds": fd.Funds,
        "indices": fd.Indices,
        "currencies": fd.Currencies,
        "cryptos": fd.Cryptos,
        "moneymarkets": fd.Moneymarkets,
    }[asset]
    return cls(use_local_location=True).select()


def test_no_symbol_collisions_across_asset_classes() -> None:
    """A given `symbol` must belong to at most one asset class.

    A symbol that appears in both `equities.csv` and `etfs.csv` (for
    example) is almost always a data-quality bug — the row in one of
    the two files is a leftover from a prior categorisation. This
    invariant catches such drift before it lands on `main`.
    """
    indices_by_asset = {
        asset: set(_load(asset).index)
        for asset in (
            "equities",
            "etfs",
            "funds",
            "indices",
            "currencies",
            "cryptos",
            "moneymarkets",
        )
    }

    collisions: dict[tuple[str, str], set[str]] = {}
    asset_names = list(indices_by_asset.keys())
    for i, a in enumerate(asset_names):
        for b in asset_names[i + 1 :]:
            shared = indices_by_asset[a] & indices_by_asset[b]
            if shared:
                collisions[(a, b)] = shared

    assert (
        not collisions
    ), "Symbols appear in more than one asset-class file:\n" + "\n".join(
        f"  {a} <-> {b}: {sorted(syms)[:5]}{' ...' if len(syms) > 5 else ''} ({len(syms)} total)"
        for (a, b), syms in collisions.items()
    )


def test_no_isin_collisions_across_asset_classes() -> None:
    """A given `isin` must belong to at most one asset class.

    ISIN is a unique identifier for a tradable security; the same code
    appearing in both `equities.csv` and `etfs.csv` means one of the two
    rows has been mis-tagged with an ISIN that rightfully belongs to the
    other security. Only `equities.csv` and `etfs.csv` track ISIN today
    (funds/indices/currencies/cryptos/moneymarkets don't), so this check
    is restricted to that pair.
    """
    eq = _load("equities")
    etfs = _load("etfs")
    eq_isins = set(eq["isin"].dropna()) if "isin" in eq.columns else set()
    etf_isins = set(etfs["isin"].dropna()) if "isin" in etfs.columns else set()
    shared = eq_isins & etf_isins
    assert not shared, (
        "ISINs appear in both equities.csv and etfs.csv "
        f"({len(shared)} total): {sorted(shared)[:5]}"
        f"{' ...' if len(shared) > 5 else ''}"
    )


def test_delisted_is_strictly_boolean() -> None:
    """`delisted` must be a real bool column: no NaN, no stray types.

    `Equities.select()` filters with `~equities["delisted"]`, which only
    negates correctly on a bool dtype, so anything else is dirty data.
    """
    files = sorted(Path("database/equities").glob("*.csv"))
    assert files, "no equities CSVs found under database/equities/"
    delisted = pd.concat([pd.read_csv(f, index_col=0)["delisted"] for f in files])
    if delisted.dtype != bool:
        offenders = delisted[~delisted.isin([True, False])]
        raise AssertionError(
            f"'delisted' is not bool dtype (got {delisted.dtype}); "
            f"{len(offenders)} invalid/NaN value(s), e.g. "
            f"{offenders.index[:5].tolist()}"
        )
