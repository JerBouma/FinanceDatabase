"""Equities Test Module"""

from __future__ import annotations

import sys
import types
from typing import TYPE_CHECKING, Any

import pytest
import requests as _requests

import financedatabase as fd

if TYPE_CHECKING:
    from tests.conftest import Recorder

equities = fd.Equities(use_local_location=True)


def test_select(recorder: Recorder) -> None:
    """Verify select() output for representative equity filter combinations."""
    smoke = equities.select()
    assert not smoke.empty
    assert "country" in smoke.columns
    recorder.capture(equities.select().iloc[:5])
    recorder.capture(equities.select(country="Canada").iloc[:5])
    recorder.capture(equities.select(sector="Communication Services").iloc[:5])
    recorder.capture(equities.select(industry_group="Insurance").iloc[:5])
    recorder.capture(equities.select(market_cap="Large Cap").iloc[:5])
    recorder.capture(equities.select(exchange="AMS").iloc[:5])
    recorder.capture(
        equities.select(country="United States", sector="Financials").iloc[:5]
    )
    recorder.capture(
        equities.select(
            country="United States", industry_group="Media & Entertainment"
        ).iloc[:5]
    )
    recorder.capture(equities.select(sector="Energy", industry_group="Energy").iloc[:5])
    recorder.capture(
        equities.select(
            country="United States",
            sector="Health Care",
            industry_group="Pharmaceuticals, Biotechnology & Life Sciences",
        ).iloc[:5]
    )
    recorder.capture(
        equities.select(
            country="United States",
            sector="Utilities",
            industry_group="Utilities",
            industry="Electric Utilities",
            market="NASDAQ Global Select",
        ).iloc[:5]
    )
    recorder.capture(
        equities.select(
            country="United States",
            sector="Materials",
            industry_group="Materials",
            market="Johannesburg Stock Exchange",
            currency="USD",
        ).iloc[:5]
    )
    recorder.capture(
        equities.select(
            country="Japan",
            sector="Energy",
            industry_group="Energy",
            market="Tokyo Stock Exchange",
            currency="JPY",
            only_primary_listing=True,
        ).iloc[:5]
    )


def test_show_options(recorder: Recorder) -> None:
    """Verify show_options() returns the expected option values for equity."""
    recorder.capture(list(equities.show_options()))
    recorder.capture(list(equities.show_options(selection="country")))
    recorder.capture(list(equities.show_options(selection="sector")))
    recorder.capture(list(equities.show_options(selection="industry_group")))
    recorder.capture(list(equities.show_options(selection="market_cap")))
    recorder.capture(list(equities.show_options(country="Canada")))
    recorder.capture(list(equities.show_options(sector="Communication Services")))
    recorder.capture(list(equities.show_options(industry_group="Insurance")))
    recorder.capture(list(equities.show_options(market_cap="Large Cap")))
    recorder.capture(
        list(equities.show_options(selection="country", country="United States"))
    )
    recorder.capture(
        list(equities.show_options(selection="sector", sector="Financials"))
    )
    recorder.capture(
        list(
            equities.show_options(
                selection="industry_group", industry_group="Media & Entertainment"
            )
        )
    )
    recorder.capture(
        list(equities.show_options(selection="market_cap", market_cap="Large Cap"))
    )


def test_exchange_market_one_to_one() -> None:
    """Each `exchange` code must map to exactly one `market` label.

    Drift between these two columns is a recurring data-quality issue.
    This test fails fast if any exchange code becomes
    ambiguous, preventing future PRs from re-introducing it.

    The reverse direction is not asserted: one `market` label may
    legitimately cover several exchange tiers (e.g. "OTC Bulletin
    Board" covers PNK / OQB / OID / OEM / OQX).
    """
    df = equities.select()
    pairs = df.dropna(subset=["exchange", "market"])
    by_exchange = pairs.groupby("exchange")["market"].nunique()
    ambiguous = by_exchange[by_exchange > 1]
    assert (
        ambiguous.empty
    ), f"Exchange codes mapping to multiple market labels: {ambiguous.to_dict()}"


def test_search_with_list_of_index() -> None:
    """`search(index=[...])` accepts a list of symbols and filters by membership."""
    result = equities.search(index=["AAPL", "MSFT", "GOOGL"])
    assert set(result.index) >= {"AAPL", "MSFT", "GOOGL"}


def test_search_case_sensitive() -> None:
    """`search(case_sensitive=True)` distinguishes from case-insensitive by row count."""
    case_sensitive = equities.search(summary="Apple", case_sensitive=True)
    case_insensitive = equities.search(summary="Apple")
    assert len(case_sensitive) <= len(case_insensitive)
    assert not case_sensitive.empty


def test_search_invalid_column_is_ignored(capsys) -> None:
    """An unknown filter column logs a warning and is silently dropped."""
    result = equities.search(nonexistent_column="value")
    captured = capsys.readouterr()
    assert "nonexistent_column is not a valid column" in captured.out
    assert len(result) == len(equities.select(exclude_delisted=False))


def test_to_toolkit_raises_without_financetoolkit(monkeypatch) -> None:
    """`FinanceFrame.to_toolkit()` raises ImportError if financetoolkit is absent."""

    monkeypatch.setitem(sys.modules, "financetoolkit", None)
    with pytest.raises(ImportError, match="financetoolkit"):
        equities.select().to_toolkit()


def test_init_raises_on_request_failure(monkeypatch) -> None:
    """`FinanceDatabase.__init__` re-raises as ValueError on network failure."""

    def _fail(*a, **kw):
        raise _requests.exceptions.ConnectionError("simulated")

    monkeypatch.setattr(_requests, "get", _fail)
    with pytest.raises(ValueError, match="Failed to load data"):
        fd.Equities()


def test_module_show_options_raises_on_invalid_selection() -> None:
    """The module-level `show_options(selection=...)` rejects unknown asset classes."""

    with pytest.raises(ValueError, match="not valid"):
        fd.show_options(selection="not_a_real_asset_class")
    with pytest.raises(ValueError, match="not set"):
        fd.show_options(selection=None)


def test_module_show_options_raises_on_request_failure(monkeypatch) -> None:
    """The module-level `show_options` re-raises as ValueError on network failure."""

    def _fail(*a, **kw):
        raise _requests.exceptions.ConnectionError("simulated")

    monkeypatch.setattr(_requests, "get", _fail)
    with pytest.raises(ValueError, match="Failed to load data"):
        fd.show_options(selection="equities")


def test_module_show_options_local_location() -> None:
    """The module-level `show_options(use_local_location=True)` reads from local files."""
    options = fd.show_options(selection="equities", use_local_location=True)
    assert isinstance(options, dict)
    assert "country" in options


def test_search_case_sensitive_with_list() -> None:
    """`search(case_sensitive=True, <col>=[...])` exercises the list+case-sensitive branch."""
    result = equities.search(country=["Japan", "Canada"], case_sensitive=True)
    assert set(result["country"].unique()) <= {"Japan", "Canada"}


def test_to_toolkit_success_path(monkeypatch) -> None:
    """`FinanceFrame.to_toolkit()` constructs a Toolkit when the dep is available."""

    captured_kwargs: dict = {}

    class _FakeToolkit:
        def __init__(self, **kwargs):
            captured_kwargs.update(kwargs)

    fake_module = types.ModuleType("financetoolkit")
    fake_module.Toolkit = _FakeToolkit  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "financetoolkit", fake_module)

    result = equities.select(country="Japan").to_toolkit(api_key="x")
    assert isinstance(result, _FakeToolkit)
    assert captured_kwargs["api_key"] == "x"
    assert captured_kwargs["tickers"]


def test_search(recorder: Recorder) -> None:
    """Verify search() output for representative equity queries."""
    recorder.capture(equities.search(summary="apple").iloc[:5])
    recorder.capture(equities.search(index="AAPL").iloc[:5])
    recorder.capture(equities.search(country="Canada").iloc[:5])
    recorder.capture(equities.search(sector="Communication Services").iloc[:5])
    recorder.capture(equities.search(industry_group="Insurance").iloc[:5])
    recorder.capture(equities.search(market_cap="Large Cap").iloc[:5])
    recorder.capture(
        equities.search(country="United States", sector="Financials").iloc[:5]
    )
    recorder.capture(
        equities.search(
            country="United States", industry_group="Media & Entertainment"
        ).iloc[:5]
    )
    recorder.capture(equities.search(sector="Energy", industry_group="Energy").iloc[:5])
    recorder.capture(
        equities.search(
            country="United States", sector="Industrials", industry_group="Software"
        ).iloc[:5]
    )


def test_select_with_invalid_value_raises() -> None:
    """`select(<filter>=...)` raises ValueError for values not in show_options()."""
    for col in [
        "country",
        "sector",
        "industry_group",
        "industry",
        "exchange",
        "mic",
    ]:
        kwargs: dict[str, Any] = {col: "__definitely_not_a_real_value__"}
        with pytest.raises(ValueError, match="not available in the database"):
            equities.select(**kwargs)


def test_select_mic() -> None:
    """`select(mic=...)` filters equities by their ISO 10383 MIC code."""
    result = equities.select(mic="XNAS")
    assert not result.empty
    assert (result["mic"] == "XNAS").all()


def test_mic_in_show_options() -> None:
    """`mic` is a selectable option exposing real MIC values."""
    assert "mic" in equities.show_options()
    mics = list(equities.show_options(selection="mic"))
    assert {"XNAS", "XLON", "XPAR"} <= set(mics)


def test_exchange_mic_one_to_one() -> None:
    """Each `exchange` code must map to exactly one `mic`.

    Mirrors `test_exchange_market_one_to_one`: a single exchange code resolving
    to multiple MICs signals drift in the exchange-to-MIC mapping.
    """
    df = equities.select()
    pairs = df.dropna(subset=["exchange", "mic"])
    by_exchange = pairs.groupby("exchange")["mic"].nunique()
    ambiguous = by_exchange[by_exchange > 1]
    assert (
        ambiguous.empty
    ), f"Exchange codes mapping to multiple MICs: {ambiguous.to_dict()}"


def test_mic_filled_when_exchange_mapped() -> None:
    """Every row whose `exchange` has a known MIC must carry that `mic`.

    Complements `test_exchange_mic_one_to_one`: that guards an exchange
    mapping to several MICs, this guards rows left blank for an exchange
    whose MIC is otherwise known — the gap that let workflow-added tickers
    ship without a `mic`.
    """
    df = equities.select()
    mapped = df.dropna(subset=["exchange", "mic"]).drop_duplicates("exchange")
    known = set(mapped["exchange"])
    missing = df[df["exchange"].isin(known) & df["mic"].isna()]
    assert missing.empty, (
        "Rows with a known exchange but missing mic: "
        f"{sorted(missing['exchange'].unique())} ({len(missing)} rows)"
    )
