from financedatabase.json_options import show_options
import pytest


def test_different_options():
    cryptocurrencies = show_options('cryptocurrencies')
    assert type(cryptocurrencies) is list and len(cryptocurrencies) > 0, 'cryptocurrencies is incorrect'

    currencies = show_options('currencies')
    assert type(currencies) is list and len(currencies) > 0, 'currencies is incorrect'

    equities = show_options('equities')
    assert type(equities) is dict and len(equities) > 0, 'equities is incorrect'

    equities = show_options('equities', equities_selection='countries')
    assert type(equities) is list and len(equities) > 0, 'equities countries is incorrect'

    equities = show_options('equities', equities_selection='sectors')
    assert type(equities) is list and len(equities) > 0, 'equities sectors is incorrect'

    equities = show_options('equities', equities_selection='industries')
    assert type(equities) is list and len(equities) > 0, 'equities industries is incorrect'

    etfs = show_options('etfs')
    assert type(etfs) is list and len(etfs) > 0, 'etfs is incorrect'

    funds = show_options('funds')
    assert type(funds) is list and len(funds) > 0, 'funds is incorrect'


if __name__ == '__main__':
    pytest.main([__file__])
