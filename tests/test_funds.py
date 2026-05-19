"""Funds Test Module"""

from __future__ import annotations

import financedatabase as fd

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tests.conftest import Recorder

funds = fd.Funds(use_local_location=True)


def test_select(recorder: Recorder) -> None:
    """Verify select() output for representative fund filter combinations."""
    recorder.capture(funds.select().iloc[:5])
    recorder.capture(funds.select(currency="TWD").iloc[:5])
    recorder.capture(funds.select(category="Energy").iloc[:5])
    recorder.capture(funds.select(category_group="Miscellaneous").iloc[:5])
    recorder.capture(funds.select(family="13D Activist Fund").iloc[:5])
    recorder.capture(funds.select(exchange="PAR").iloc[:5])
    recorder.capture(funds.select(exchange="FRA", category="Energy").iloc[:5])


def test_show_options(recorder: Recorder) -> None:
    """Verify show_options() returns the expected option values for fund."""
    recorder.capture(list(funds.show_options()))
    recorder.capture(list(funds.show_options(selection="category")))
    recorder.capture(list(funds.show_options(selection="category_group")))
    recorder.capture(list(funds.show_options(selection="family")))
    recorder.capture(list(funds.show_options(selection="currency")))
    recorder.capture(list(funds.show_options(selection="exchange")))
    recorder.capture(list(funds.show_options(exchange="PAR")))
    recorder.capture(list(funds.show_options(category="Energy")))


def test_search(recorder: Recorder) -> None:
    """Verify search() output for representative fund queries."""
    recorder.capture(funds.search(summary="Shares").iloc[:5])
    recorder.capture(funds.search(index="GSPX").iloc[:5])
    recorder.capture(funds.search(category="Utilities").iloc[:5])
    recorder.capture(funds.search(category_group="Miscellaneous").iloc[:5])
    recorder.capture(funds.search(family="ivari").iloc[:5])
    recorder.capture(funds.search(exchange="NZE").iloc[:5])
    recorder.capture(funds.search(summary="Pension", category="Energy").iloc[:5])
