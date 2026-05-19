"""Currencies Test Module"""

from __future__ import annotations

import financedatabase as fd

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tests.conftest import Recorder

currencies = fd.Currencies(use_local_location=True)


def test_select(recorder: Recorder) -> None:
    """Verify select() output for representative currency filter combinations."""
    smoke = currencies.select()
    assert not smoke.empty
    recorder.capture(currencies.select().iloc[:5])
    recorder.capture(currencies.select(base_currency="USD").iloc[:5])
    recorder.capture(currencies.select(quote_currency="EUR").iloc[:5])
    recorder.capture(
        currencies.select(base_currency="USD", quote_currency="CAD").iloc[:5]
    )


def test_show_options(recorder: Recorder) -> None:
    """Verify show_options() returns the expected option values for currency."""
    recorder.capture(list(currencies.show_options()))
    recorder.capture(list(currencies.show_options(selection="base_currency")))
    recorder.capture(list(currencies.show_options(selection="quote_currency")))
    recorder.capture(list(currencies.show_options(base_currency="USD")))
    recorder.capture(list(currencies.show_options(quote_currency="EUR")))
    recorder.capture(
        list(currencies.show_options(selection="base_currency", base_currency="USD"))
    )
    recorder.capture(
        list(currencies.show_options(selection="quote_currency", quote_currency="EUR"))
    )


def test_search(recorder: Recorder) -> None:
    """Verify search() output for representative currency queries."""
    recorder.capture(currencies.search(summary="dollar").iloc[:5])
    recorder.capture(currencies.search(index="USD").iloc[:5])
    recorder.capture(currencies.search(base_currency="CAD").iloc[:5])
    recorder.capture(currencies.search(quote_currency="EUR").iloc[:5])


def test_select_with_invalid_value_raises() -> None:
    """`select(<filter>=...)` raises ValueError for values not in show_options()."""
    import pytest

    for col in ["base_currency", "quote_currency"]:
        with pytest.raises(ValueError, match="not available in the database"):
            currencies.select(**{col: "__definitely_not_a_real_value__"})
