"""Indices Test Module"""

import financedatabase as fd

indices = fd.Indices()


# pylint: disable=missing-function-docstring


def test_select(recorder):
    recorder.capture(indices.select().iloc[:5])
    recorder.capture(indices.select(currency="NOK").iloc[:5])
    recorder.capture(indices.select(category="Industrials").iloc[:5])
    recorder.capture(indices.select(category_group="Cash").iloc[:5])
    recorder.capture(indices.select(exchange="ASX").iloc[:5])
    recorder.capture(indices.select(exchange="ASX", category="REITs").iloc[:5])


def test_show_options(recorder):
    recorder.capture(list(indices.show_options()))
    recorder.capture(list(indices.show_options(selection="category")))
    recorder.capture(list(indices.show_options(selection="category_group")))
    recorder.capture(list(indices.show_options(selection="currency")))
    recorder.capture(list(indices.show_options(selection="exchange")))
    recorder.capture(list(indices.show_options(exchange="ASX")))
    recorder.capture(list(indices.show_options(category="REITs")))


def test_search(recorder):
    recorder.capture(indices.search(summary="S&P").iloc[:5])
    recorder.capture(indices.search(index="GSPC").iloc[:5])
    recorder.capture(indices.search(category="Industrials").iloc[:5])
    recorder.capture(indices.search(category_group="Energy").iloc[:5])
    recorder.capture(indices.search(exchange="SHH").iloc[:5])
    recorder.capture(indices.search(summary="S&P", category="Financials").iloc[:5])
