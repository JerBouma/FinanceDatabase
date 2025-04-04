"""Currencies Test Module"""

import financedatabase as fd

moneymarkets = fd.Moneymarkets()

# pylint: disable=missing-function-docstring


def test_select(recorder):
    recorder.capture(moneymarkets.select().iloc[:5])
    recorder.capture(moneymarkets.select(currency="USD").iloc[:5])
    recorder.capture(moneymarkets.select(family="BlackRock Funds").iloc[:5])


def test_show_options(recorder):
    recorder.capture(list(moneymarkets.show_options()))
    recorder.capture(list(moneymarkets.show_options(selection="currency")))
    recorder.capture(list(moneymarkets.show_options(selection="family")))
    recorder.capture(list(moneymarkets.show_options(family="BlackRock Funds")))


def test_search(recorder):
    recorder.capture(moneymarkets.search(summary="Government").iloc[:5])
    recorder.capture(moneymarkets.search(index="RXX").iloc[:5])
    recorder.capture(moneymarkets.search(currency="USD").iloc[:5])
    recorder.capture(moneymarkets.search(family="BlackRock Funds").iloc[:5])
