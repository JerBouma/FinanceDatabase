"""Indices Test Module"""

from __future__ import annotations

import financedatabase as fd

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tests.conftest import Recorder

indices = fd.Indices(use_local_location=True)


def test_select(recorder: Recorder) -> None:
    """Verify select() output for representative index filter combinations."""
    smoke = indices.select()
    assert not smoke.empty
    assert "currency" in smoke.columns
    recorder.capture(indices.select().iloc[:5])
    recorder.capture(indices.select(currency="NOK").iloc[:5])
    recorder.capture(indices.select(category="Industrials").iloc[:5])
    recorder.capture(indices.select(category_group="Cash").iloc[:5])
    recorder.capture(indices.select(exchange="ASX").iloc[:5])
    recorder.capture(indices.select(exchange="ASX", category="REITs").iloc[:5])


def test_show_options(recorder: Recorder) -> None:
    """Verify show_options() returns the expected option values for index."""
    recorder.capture(list(indices.show_options()))
    recorder.capture(list(indices.show_options(selection="category")))
    recorder.capture(list(indices.show_options(selection="category_group")))
    recorder.capture(list(indices.show_options(selection="currency")))
    recorder.capture(list(indices.show_options(selection="exchange")))
    recorder.capture(list(indices.show_options(exchange="ASX")))
    recorder.capture(list(indices.show_options(category="REITs")))


def test_search(recorder: Recorder) -> None:
    """Verify search() output for representative index queries."""
    recorder.capture(indices.search(summary="S&P").iloc[:5])
    recorder.capture(indices.search(index="GSPC").iloc[:5])
    recorder.capture(indices.search(category="Industrials").iloc[:5])
    recorder.capture(indices.search(category_group="Energy").iloc[:5])
    recorder.capture(indices.search(exchange="SHH").iloc[:5])
    recorder.capture(indices.search(summary="S&P", category="Financials").iloc[:5])


def test_select_with_invalid_value_raises() -> None:
    """`select(<filter>=...)` raises ValueError for values not in show_options()."""
    import pytest

    for col in ["currency", "exchange", "mic"]:
        with pytest.raises(ValueError, match="not available in the database"):
            indices.select(**{col: "__definitely_not_a_real_value__"})


def test_select_mic() -> None:
    """`select(mic=...)` filters indices by their ISO 10383 MIC code."""
    assert "mic" in indices.show_options()
    mic = list(indices.show_options(selection="mic"))[0]
    result = indices.select(mic=mic)
    assert not result.empty
    assert (result["mic"] == mic).all()
