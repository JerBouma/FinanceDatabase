"""ETFs Test Module"""

from __future__ import annotations

import financedatabase as fd

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tests.conftest import Recorder

etfs = fd.ETFs(use_local_location=True)


def test_select(recorder: Recorder) -> None:
    """Verify select() output for representative ETF filter combinations."""
    smoke = etfs.select()
    assert not smoke.empty
    assert "currency" in smoke.columns
    recorder.capture(etfs.select().iloc[:5])
    recorder.capture(etfs.select(category="Blend").iloc[:5])
    recorder.capture(etfs.select(category_group="Materials").iloc[:5])
    recorder.capture(etfs.select(family="ASYMshares").iloc[:5])
    recorder.capture(etfs.select(exchange="PCX").iloc[:5])
    recorder.capture(etfs.select(exchange="CPH", category="Financials").iloc[:5])


def test_show_options(recorder: Recorder) -> None:
    """Verify show_options() returns the expected option values for ETF."""
    recorder.capture(list(etfs.show_options()))
    recorder.capture(list(etfs.show_options(selection="category")))
    recorder.capture(list(etfs.show_options(selection="category_group")))
    recorder.capture(list(etfs.show_options(selection="family")))
    recorder.capture(list(etfs.show_options(selection="currency")))
    recorder.capture(list(etfs.show_options(selection="exchange")))
    recorder.capture(list(etfs.show_options(exchange="PAR")))
    recorder.capture(list(etfs.show_options(category="Energy")))


def test_search(recorder: Recorder) -> None:
    """Verify search() output for representative ETF queries."""
    recorder.capture(etfs.search(summary="Apple").iloc[:5])
    recorder.capture(etfs.search(index="VOO").iloc[:5])
    recorder.capture(etfs.search(category="Utilities").iloc[:5])
    recorder.capture(etfs.search(category_group="Materials").iloc[:5])
    recorder.capture(etfs.search(family="ASYMshares").iloc[:5])
    recorder.capture(etfs.search(exchange="PCX").iloc[:5])
    recorder.capture(
        etfs.search(summary="North America", category="Financials").iloc[:5]
    )


def test_select_with_invalid_value_raises() -> None:
    """`select(<filter>=...)` raises ValueError for values not in show_options()."""
    import pytest

    for col in ["category_group", "category", "family", "currency", "exchange"]:
        with pytest.raises(ValueError, match="not available in the database"):
            etfs.select(**{col: "__definitely_not_a_real_value__"})
