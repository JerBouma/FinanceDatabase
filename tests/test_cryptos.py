"""Cryptocurrencies Test Module"""

from __future__ import annotations

import financedatabase as fd

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tests.conftest import Recorder

cryptos = fd.Cryptos(use_local_location=True)


def test_select(recorder: Recorder) -> None:
    """Verify select() output for representative cryptocurrency filter combinations."""
    recorder.capture(cryptos.select().iloc[:5])
    recorder.capture(cryptos.select(currency="USD").iloc[:5])
    recorder.capture(cryptos.select(cryptocurrency="ETC").iloc[:5])
    recorder.capture(cryptos.select(currency="USD", cryptocurrency="ETC").iloc[:5])


def test_show_options(recorder: Recorder) -> None:
    """Verify show_options() returns the expected option values for cryptocurrency."""
    recorder.capture(list(cryptos.show_options()))
    recorder.capture(list(cryptos.show_options(selection="cryptocurrency")))
    recorder.capture(list(cryptos.show_options(selection="currency")))
    recorder.capture(list(cryptos.show_options(cryptocurrency="ETC")))
    recorder.capture(list(cryptos.show_options(currency="USD")))
    recorder.capture(
        list(cryptos.show_options(selection="cryptocurrency", cryptocurrency="ETC"))
    )
    recorder.capture(list(cryptos.show_options(selection="currency", currency="USD")))


def test_search(recorder: Recorder) -> None:
    """Verify search() output for representative cryptocurrency queries."""
    recorder.capture(cryptos.search(summary="bitcoin").iloc[:5])
    recorder.capture(cryptos.search(index="ETC").iloc[:5])
    recorder.capture(cryptos.search(cryptocurrency="AAVE").iloc[:5])
    recorder.capture(cryptos.search(currency="USD").iloc[:5])
