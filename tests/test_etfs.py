"""ETFs Test Module"""

import financedatabase as fd

etfs = fd.ETFs()


# pylint: disable=missing-function-docstring


def test_select(recorder):
    recorder.capture(etfs.select().iloc[:5])
    recorder.capture(etfs.select(category="Blend").iloc[:5])
    recorder.capture(etfs.select(category_group="Materials").iloc[:5])
    recorder.capture(etfs.select(family="ASYMshsare").iloc[:5])
    recorder.capture(etfs.select(exchange="PCX").iloc[:5])
    recorder.capture(etfs.select(exchange="CPH", category="Financials").iloc[:5])


def test_show_options(recorder):
    recorder.capture(list(etfs.show_options()))
    recorder.capture(list(etfs.show_options(selection="category")))
    recorder.capture(list(etfs.show_options(selection="category_group")))
    recorder.capture(list(etfs.show_options(selection="family")))
    recorder.capture(list(etfs.show_options(selection="currency")))
    recorder.capture(list(etfs.show_options(selection="exchange")))
    recorder.capture(list(etfs.show_options(exchange="PAR")))
    recorder.capture(list(etfs.show_options(category="Energy")))


def test_search(recorder):
    recorder.capture(etfs.search(summary="Apple").iloc[:5])
    recorder.capture(etfs.search(index="VOO").iloc[:5])
    recorder.capture(etfs.search(category="Utilities").iloc[:5])
    recorder.capture(etfs.search(category_group="Materials").iloc[:5])
    recorder.capture(etfs.search(family="ASYMshsare").iloc[:5])
    recorder.capture(etfs.search(exchange="PCX").iloc[:5])
    recorder.capture(
        etfs.search(summary="North America", category="Financials").iloc[:5]
    )
