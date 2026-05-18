"""Money Markets Test Module"""

from __future__ import annotations

import financedatabase as fd

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tests.conftest import Recorder

moneymarkets = fd.Moneymarkets(use_local_location=True)


def test_select(recorder: Recorder) -> None:
    """Verify select() output for representative money market filter combinations."""
    recorder.capture(moneymarkets.select().iloc[:5])
    recorder.capture(moneymarkets.select(currency="USD").iloc[:5])
    recorder.capture(moneymarkets.select(family="BlackRock Funds").iloc[:5])


def test_show_options(recorder: Recorder) -> None:
    """Verify show_options() returns the expected option values for money market."""
    recorder.capture(list(moneymarkets.show_options()))
    recorder.capture(list(moneymarkets.show_options(selection="currency")))
    recorder.capture(list(moneymarkets.show_options(selection="family")))
    recorder.capture(list(moneymarkets.show_options(family="BlackRock Funds")))


def test_search(recorder: Recorder) -> None:
    """Verify search() output for representative money market queries."""
    recorder.capture(moneymarkets.search(summary="Government").iloc[:5])
    recorder.capture(moneymarkets.search(index="RXX").iloc[:5])
    recorder.capture(moneymarkets.search(currency="USD").iloc[:5])
    recorder.capture(moneymarkets.search(family="BlackRock Funds").iloc[:5])
