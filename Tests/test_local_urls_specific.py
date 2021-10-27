from financedatabase.json_picker import (select_cryptocurrencies, select_equities, select_moneymarkets, select_etfs,
                                         select_funds, select_indices, select_currencies)
import pytest

LOCAL_URL = "C:/Users/jerbo/Google Drive/Programming/Python/FinanceDatabase/Database"


def test_local_urls_specific():
    crypto = select_cryptocurrencies(cryptocurrency='BTC2',
                                     base_url=rf'{LOCAL_URL}/Cryptocurrencies/',
                                     use_local_location=True)
    assert type(crypto) is dict and len(crypto) > 0, "crypto BTC dictionary is invalid."

    etfs = select_etfs(category='China Region',
                       base_url=rf'{LOCAL_URL}/ETFs/',
                       use_local_location=True, exclude_exchanges=False)
    assert type(etfs) is dict and len(etfs) > 0, "etfs China Region dictionary is invalid."

    equity = select_equities(country='Canada',
                             base_url=rf'{LOCAL_URL}/Equities/',
                             use_local_location=True, exclude_exchanges=False)
    assert type(equity) is dict and len(equity) > 0, "equity Canada dictionary is invalid."

    equity = select_equities(sector='Energy',
                             base_url=rf'{LOCAL_URL}/Equities/',
                             use_local_location=True, exclude_exchanges=False)
    assert type(equity) is dict and len(equity) > 0, "equity Energy dictionary is invalid."

    equity = select_equities(industry='Biotechnology',
                             base_url=rf'{LOCAL_URL}/Equities/',
                             use_local_location=True, exclude_exchanges=False)
    assert type(equity) is dict and len(equity) > 0, "equity Biotechnology dictionary is invalid."

    equity = select_equities(country='United States', sector='Financial',
                             base_url=rf'{LOCAL_URL}/Equities/',
                             use_local_location=True, exclude_exchanges=False)
    assert type(equity) is dict and len(equity) > 0, "equity United States + Financial dictionary is invalid."

    equity = select_equities(country='Slovakia', industry='Resorts & Casinos',
                             base_url=rf'{LOCAL_URL}/Equities/',
                             use_local_location=True, exclude_exchanges=False)
    assert type(equity) is dict and len(equity) > 0, "equity Slovakia + Resorts & Casinos dictionary is invalid."

    with pytest.raises(ValueError):
        equity = select_equities(country='Slovakia', industry='Resorts & Casinos',
                                 base_url=rf'{LOCAL_URL}/Equities/',
                                 use_local_location=True, exclude_exchanges=True)

    equity = select_equities(country='Panama', sector='Industrials', industry='Airlines',
                             base_url=rf'{LOCAL_URL}/Equities/',
                             use_local_location=True, exclude_exchanges=False)
    assert type(equity) is dict and len(equity) > 0, "equity Panama + Industrials + Airlines is invalid."

    funds = select_funds(category='Alt - Currency',
                         base_url=rf'{LOCAL_URL}/Funds/',
                         use_local_location=True, exclude_exchanges=False)
    assert type(funds) is dict and len(funds) > 0, "funds Alt - Currency dictionary is invalid."

    currency = select_currencies(currency='EUR',
                                 base_url=rf'{LOCAL_URL}/Currencies/',
                                 use_local_location=True)
    assert type(currency) is dict and len(currency) > 0, "currency EUR dictionary is invalid."

    index = select_indices(market='cn_market',
                           base_url=rf'{LOCAL_URL}/Indices/',
                           use_local_location=True, exclude_exchanges=False)
    assert type(index) is dict and len(index) > 0, "index cn_market dictionary is invalid."

    moneymarket = select_moneymarkets(market='us_market',
                                      base_url=rf'{LOCAL_URL}/Moneymarkets/',
                                      use_local_location=True, exclude_exchanges=False)
    assert type(moneymarket) is dict and len(moneymarket) > 0, "moneymarket us_market dictionary is invalid."


if __name__ == '__main__':
    pytest.main([__file__])
