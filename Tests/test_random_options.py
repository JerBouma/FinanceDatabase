from financedatabase.json_picker import (select_cryptocurrencies, select_equities, select_moneymarkets, select_etfs,
                                         select_funds, select_indices, select_currencies)
from financedatabase.json_options import show_options
import numpy as np
import pytest


def test_random_options():
    random_number = np.random.randint(0, 10)

    crypto_option = show_options('cryptocurrencies')[random_number]
    random_crypto = select_cryptocurrencies(crypto_option)
    assert type(random_crypto) is dict and len(random_crypto) > 0, "all_cryptos Cryptos dictionary is invalid."

    currencies_option = show_options('currencies')[random_number]
    random_currency = select_currencies(currencies_option)
    assert type(random_currency) is dict and len(random_currency) > 0, "random_currency dictionary is invalid."

    etfs_option = show_options('etfs')[random_number]
    random_etf = select_etfs(etfs_option)
    assert type(random_etf) is dict and len(random_etf) > 0, "random_etf dictionary is invalid."

    equity_option_countries = show_options('equities')['countries'][random_number]
    random_equity = select_equities(country=equity_option_countries)
    assert type(random_equity) is dict and len(random_equity) > 0, "random_equity (countries) dictionary is invalid."

    equity_option_sectors = show_options('equities')['sectors'][random_number]
    random_equity = select_equities(sector=equity_option_sectors)
    assert type(random_equity) is dict and len(random_equity) > 0, "random_equity (sectors) dictionary is invalid."

    equity_option_industries = show_options('equities')['industries'][random_number]
    random_equity = select_equities(industry=equity_option_industries, exclude_exchanges=False)
    assert type(random_equity) is dict and len(random_equity) > 0, "random_equity (industries) dictionary is invalid."

    random_equity = select_equities(country='United States', sector='Basic Materials')
    assert type(random_equity) is dict and len(random_equity) > 0, ("random_equity (country + sector) "
                                                                    "dictionary is invalid.")

    random_equity = select_equities(country='United States', industry='Waste Management')
    assert type(random_equity) is dict and len(random_equity) > 0, ("random_equity (country + industry) "
                                                                    "dictionary is invalid.")

    random_equity = select_equities(country='United States', sector='Consumer Cyclical',
                                    industry='Auto Parts')
    assert type(random_equity) is dict and len(random_equity) > 0, ("random_equity (country + sector + industry) "
                                                                    "dictionary is invalid.")

    funds_option = show_options('funds')[random_number]
    random_fund = select_funds(funds_option, exclude_exchanges=False)
    assert type(random_fund) is dict and len(random_fund) > 0, "random_fund dictionary is invalid."

    random_index = select_indices('us_market')
    assert type(random_index) is dict and len(random_index) > 0, "random_index dictionary is invalid."

    random_moneymarket = select_moneymarkets('us_market')
    assert type(random_moneymarket) is dict and len(random_moneymarket) > 0, "random_moneymarket dictionary is invalid."


if __name__ == '__main__':
    pytest.main([__file__])
