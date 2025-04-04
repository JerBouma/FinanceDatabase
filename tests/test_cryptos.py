"""Cryptos"""

import financedatabase as fd

cryptos = fd.Cryptos()

# pylint: disable=missing-function-docstring


def test_select(recorder):
    recorder.capture(cryptos.select().iloc[:5])
    recorder.capture(cryptos.select(currency="USD").iloc[:5])
    recorder.capture(cryptos.select(cryptocurrency="ETC").iloc[:5])
    recorder.capture(cryptos.select(currency="USD", cryptocurrency="ETC").iloc[:5])


def test_show_options(recorder):
    recorder.capture(list(cryptos.show_options()))
    recorder.capture(list(cryptos.show_options(selection="cryptocurrency")))
    recorder.capture(list(cryptos.show_options(selection="currency")))
    recorder.capture(list(cryptos.show_options(cryptocurrency="ETC")))
    recorder.capture(list(cryptos.show_options(currency="USD")))
    recorder.capture(
        list(cryptos.show_options(selection="cryptocurrency", cryptocurrency="ETC"))
    )
    recorder.capture(list(cryptos.show_options(selection="currency", currency="USD")))


def test_search(recorder):
    recorder.capture(cryptos.search(summary="bitcoin").iloc[:5])
    recorder.capture(cryptos.search(index="ETC").iloc[:5])
    recorder.capture(cryptos.search(cryptocurrency="AAVE").iloc[:5])
    recorder.capture(cryptos.search(currency="USD").iloc[:5])
