"""Cross-asset invariants Test Module."""

from __future__ import annotations

import financedatabase as fd


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
