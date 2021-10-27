from financedatabase.json_picker import (select_cryptocurrencies, select_equities, select_moneymarkets, select_etfs,
                                         select_funds, select_indices, select_currencies)
import pytest

LOCAL_URL = "C:/Users/jerbo/Google Drive/Programming/Python/FinanceDatabase/Database"


def test_local_urls():
    crypto = select_cryptocurrencies(base_url=rf'{LOCAL_URL}/Cryptocurrencies/',
                                     use_local_location=True)
    assert type(crypto) is dict and len(crypto) > 0, "crypto dictionary is invalid."

    etfs = select_etfs(base_url=rf'{LOCAL_URL}/ETFs/',
                       use_local_location=True, exclude_exchanges=False)
    assert type(etfs) is dict and len(etfs) > 0, "etfs dictionary is invalid."

    equity = select_equities(base_url=rf'{LOCAL_URL}/Equities/',
                             use_local_location=True, exclude_exchanges=False)
    assert type(equity) is dict and len(equity) > 0, "equity dictionary is invalid."

    funds = select_funds(base_url=rf'{LOCAL_URL}/Funds/',
                         use_local_location=True, exclude_exchanges=False)
    assert type(funds) is dict and len(funds) > 0, "funds dictionary is invalid."

    currency = select_currencies(base_url=rf'{LOCAL_URL}/Currencies/',
                                 use_local_location=True)
    assert type(currency) is dict and len(currency) > 0, "currency dictionary is invalid."

    index = select_indices(base_url=rf'{LOCAL_URL}/Indices/',
                           use_local_location=True, exclude_exchanges=False)
    assert type(index) is dict and len(index) > 0, "index dictionary is invalid."

    moneymarket = select_moneymarkets(base_url=rf'{LOCAL_URL}/Moneymarkets/',
                                      use_local_location=True, exclude_exchanges=False)
    assert type(moneymarket) is dict and len(moneymarket) > 0, "moneymarket dictionary is invalid."


if __name__ == '__main__':
    pytest.main([__file__])