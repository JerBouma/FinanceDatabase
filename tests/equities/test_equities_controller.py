"""Equities Controller Tests"""

import logging
import re
import sys
import types
from pathlib import Path
from typing import Any

import pandas as pd
import pytest
import requests as _requests

import financedatabase as fd
from tests.helpers import check_search, check_select, check_show_options

equities = fd.Equities(use_local_location=True)


EQUITY_SELECTION_FIELDS = (
    "country",
    "sector",
    "industry_group",
    "industry",
    "currency",
    "exchange",
    "mic",
    "market",
    "market_cap",
)


@pytest.fixture
def equities_with_delisted_options(monkeypatch):
    """Provide one live and one delisted value for every selectable field."""
    values = {
        field: [f"Live {field}", f"Delisted {field}"]
        for field in EQUITY_SELECTION_FIELDS
    }
    values["delisted"] = [False, True]
    monkeypatch.setattr(equities, "data", pd.DataFrame(values))
    return equities


def test_na_symbol_survives_local_compression_round_trip() -> None:
    """The valid ticker ``NA`` must not be interpreted as a missing index."""
    assert "NA" in equities.data.index
    assert not equities.data.index.hasnans
    assert pd.isna(equities.data.loc["NA", "summary"])


def test_na_symbol_survives_remote_compression_round_trip(
    monkeypatch, tmp_path
) -> None:
    """Remote BZ2 loading uses the same literal-NA handling as local loading."""
    monkeypatch.setenv("FINANCEDATABASE_CACHE_DIR", str(tmp_path))

    class _Response:
        status_code = 200
        headers: dict = {}
        content = Path("compression/equities.bz2").read_bytes()

        @staticmethod
        def raise_for_status() -> None:
            return None

    monkeypatch.setattr(_requests, "get", lambda *args, **kwargs: _Response())
    remote_equities = fd.Equities()

    assert "NA" in remote_equities.data.index
    assert not remote_equities.data.index.hasnans
    assert pd.isna(remote_equities.data.loc["NA", "summary"])


SELECT_CASES = [
    {},
    {"country": "Canada"},
    {"sector": "Communication Services"},
    {"industry_group": "Insurance"},
    {"market_cap": "Large Cap"},
    {"exchange": "AMS"},
    {"country": "United States", "sector": "Financials"},
    {"country": "United States", "industry_group": "Media & Entertainment"},
    {"sector": "Energy", "industry_group": "Energy"},
    {
        "country": "United States",
        "sector": "Health Care",
        "industry_group": "Pharmaceuticals, Biotechnology & Life Sciences",
    },
    {
        "country": "United States",
        "sector": "Utilities",
        "industry_group": "Utilities",
        "industry": "Electric Utilities",
        "market": "NASDAQ Global Select",
    },
    {
        "country": "United States",
        "sector": "Materials",
        "industry_group": "Materials",
        "market": "Johannesburg Stock Exchange",
        "currency": "USD",
    },
    {
        "country": "Japan",
        "sector": "Energy",
        "industry_group": "Energy",
        "market": "Tokyo Stock Exchange",
        "currency": "JPY",
        "only_primary_listing": True,
    },
]


@pytest.mark.parametrize("kwargs", SELECT_CASES, ids=str)
def test_select(kwargs: dict) -> None:
    """select() matches an independent pandas filter of the same data (structure, not a snapshot)."""
    filters = [
        k
        for k in kwargs
        if k
        not in [
            "case_sensitive",
            "exclude_delisted",
            "only_primary_listing",
            "selection",
        ]
    ]
    check_select(equities, nonempty=len(filters) <= 1, **kwargs)


@pytest.mark.parametrize("field", EQUITY_SELECTION_FIELDS)
def test_select_allows_delisted_only_scalar_when_requested(
    equities_with_delisted_options, field: str
) -> None:
    """A delisted-only scalar filter is valid when delisted equities are included."""
    delisted_value = f"Delisted {field}"

    result = equities_with_delisted_options.select(
        **{field: delisted_value}, exclude_delisted=False
    )

    assert result.index.tolist() == [1]
    with pytest.raises(ValueError, match="not available in the database"):
        equities_with_delisted_options.select(**{field: delisted_value})
    with pytest.raises(ValueError, match="not available in the database"):
        equities_with_delisted_options.select(
            **{field: delisted_value}, exclude_delisted=True
        )


@pytest.mark.parametrize("field", EQUITY_SELECTION_FIELDS)
def test_select_allows_delisted_only_list_when_requested(
    equities_with_delisted_options, field: str
) -> None:
    """A delisted-only list filter is valid when delisted equities are included."""
    delisted_value = f"Delisted {field}"

    result = equities_with_delisted_options.select(
        **{field: [delisted_value]}, exclude_delisted=False
    )

    assert result.index.tolist() == [1]


@pytest.mark.parametrize("field", EQUITY_SELECTION_FIELDS)
def test_select_rejects_unknown_values_when_delisted_are_requested(
    equities_with_delisted_options, field: str
) -> None:
    """Including delisted equities does not permit unknown filter values."""
    with pytest.raises(ValueError, match="not available in the database"):
        equities_with_delisted_options.select(
            **{field: "__definitely_not_a_real_value__"}, exclude_delisted=False
        )


SHOW_OPTIONS_CASES = [
    {},
    {"selection": "country"},
    {"selection": "sector"},
    {"selection": "industry_group"},
    {"selection": "market_cap"},
    {"country": "Canada"},
    {"sector": "Communication Services"},
    {"industry_group": "Insurance"},
    {"market_cap": "Large Cap"},
    {"selection": "country", "country": "United States"},
    {"selection": "sector", "sector": "Financials"},
    {"selection": "industry_group", "industry_group": "Media & Entertainment"},
    {"selection": "market_cap", "market_cap": "Large Cap"},
]


@pytest.mark.parametrize("kwargs", SHOW_OPTIONS_CASES, ids=str)
def test_show_options(kwargs: dict) -> None:
    """show_options() matches an independent pandas filter of the same data (structure, not a snapshot)."""
    filters = [
        k
        for k in kwargs
        if k
        not in [
            "case_sensitive",
            "exclude_delisted",
            "only_primary_listing",
            "selection",
        ]
    ]
    check_show_options(equities, nonempty=len(filters) <= 1, **kwargs)


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


def test_search_invalid_column_is_ignored(caplog) -> None:
    """An unknown filter column logs a warning and is otherwise ignored."""
    # The package logger doesn't propagate, so the capture handler is attached directly.
    logger = logging.getLogger("financedatabase")
    logger.addHandler(caplog.handler)
    try:
        result = equities.search(nonexistent_column="value")
    finally:
        logger.removeHandler(caplog.handler)
    assert "nonexistent_column is not a valid column" in caplog.text
    assert len(result) == len(equities.select())  # both exclude delisted by default


def test_to_toolkit_raises_without_financetoolkit(monkeypatch) -> None:
    """`FinanceFrame.to_toolkit()` raises ImportError if financetoolkit is absent."""

    monkeypatch.setitem(sys.modules, "financetoolkit", None)
    with pytest.raises(ImportError, match="financetoolkit"):
        equities.select().to_toolkit()


def test_init_raises_on_request_failure(monkeypatch) -> None:
    """`FinanceDatabase.__init__` re-raises as ValueError on network failure."""

    def raise_connection_error(*a, **kw):
        raise _requests.exceptions.ConnectionError("simulated")

    monkeypatch.setattr(_requests, "get", raise_connection_error)
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

    def raise_connection_error(*a, **kw):
        raise _requests.exceptions.ConnectionError("simulated")

    monkeypatch.setattr(_requests, "get", raise_connection_error)
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


SEARCH_CASES = [
    {"summary": "apple"},
    {"index": "AAPL"},
    {"country": "Canada"},
    {"sector": "Communication Services"},
    {"industry_group": "Insurance"},
    {"market_cap": "Large Cap"},
    {"country": "United States", "sector": "Financials"},
    {"country": "United States", "industry_group": "Media & Entertainment"},
    {"sector": "Energy", "industry_group": "Energy"},
    {"country": "United States", "sector": "Industrials", "industry_group": "Software"},
]


@pytest.mark.parametrize("kwargs", SEARCH_CASES, ids=str)
def test_search(kwargs: dict) -> None:
    """search() matches an independent pandas filter of the same data (structure, not a snapshot)."""
    filters = [
        k
        for k in kwargs
        if k
        not in [
            "case_sensitive",
            "exclude_delisted",
            "only_primary_listing",
            "selection",
        ]
    ]
    check_search(equities, nonempty=len(filters) <= 1, **kwargs)


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


def test_search_excludes_delisted_by_default() -> None:
    """search() leaves delisted symbols out unless exclude_delisted=False, like select()."""
    data = equities.data
    delisted = data.index[data["delisted"].astype(bool)][0]
    query = f"^{re.escape(delisted)}$"
    assert delisted not in equities.search(index=query).index
    assert delisted not in equities.search(index=query, exclude_delisted=True).index
    assert delisted in equities.search(index=query, exclude_delisted=False).index
    assert (
        not equities.search(name=data.loc[delisted, "name"])["delisted"]
        .astype(bool)
        .any()
    )
