"""Funds Test Module"""

import financedatabase as fd

funds = fd.Funds()


# pylint: disable=missing-function-docstring


def test_select(recorder):
    recorder.capture(funds.select().iloc[:5])
    recorder.capture(funds.select(currency="TWD").iloc[:5])
    recorder.capture(funds.select(category="Energy").iloc[:5])
    recorder.capture(funds.select(category_group="Miscellaneous").iloc[:5])
    recorder.capture(funds.select(family="13D Activist Fund").iloc[:5])
    recorder.capture(funds.select(exchange="PAR").iloc[:5])
    recorder.capture(funds.select(exchange="FRA", category="Energy").iloc[:5])


def test_show_options(recorder):
    recorder.capture(list(funds.show_options()))
    recorder.capture(list(funds.show_options(selection="category")))
    recorder.capture(list(funds.show_options(selection="category_group")))
    recorder.capture(list(funds.show_options(selection="family")))
    recorder.capture(list(funds.show_options(selection="currency")))
    recorder.capture(list(funds.show_options(selection="exchange")))
    recorder.capture(list(funds.show_options(exchange="PAR")))
    recorder.capture(list(funds.show_options(category="Energy")))


def test_search(recorder):
    recorder.capture(funds.search(summary="Shares").iloc[:5])
    recorder.capture(funds.search(index="GSPX").iloc[:5])
    recorder.capture(funds.search(category="Utilities").iloc[:5])
    recorder.capture(funds.search(category_group="Miscellaneous").iloc[:5])
    recorder.capture(funds.search(family="ivari").iloc[:5])
    recorder.capture(funds.search(exchange="NZE").iloc[:5])
    recorder.capture(funds.search(summary="Pension", category="Energy").iloc[:5])
