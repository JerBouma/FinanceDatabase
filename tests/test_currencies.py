"""Currencies Test Module"""

import financedatabase as fd

currencies = fd.Currencies()

# pylint: disable=missing-function-docstring


def test_select(recorder):
    recorder.capture(currencies.select().iloc[:5])
    recorder.capture(currencies.select(base_currency="USD").iloc[:5])
    recorder.capture(currencies.select(quote_currency="EUR").iloc[:5])
    recorder.capture(
        currencies.select(base_currency="USD", quote_currency="CAD").iloc[:5]
    )


def test_show_options(recorder):
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


def test_search(recorder):
    recorder.capture(currencies.search(summary="dollar").iloc[:5])
    recorder.capture(currencies.search(index="USD").iloc[:5])
    recorder.capture(currencies.search(base_currency="CAD").iloc[:5])
    recorder.capture(currencies.search(quote_currency="EUR").iloc[:5])
