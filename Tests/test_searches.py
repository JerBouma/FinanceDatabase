from Searcher.json_picker import (select_cryptocurrencies, select_equities, select_moneymarkets, select_etfs,
                                  select_funds, select_indices, select_currencies)
from Searcher.json_options import search_products
import pytest

# Initialize data
all_cryptos = select_cryptocurrencies()
all_etfs = select_etfs()
all_equities = select_equities()
all_funds = select_funds()
all_currencies = select_currencies()
all_indices = select_indices()
all_moneymarkets = select_moneymarkets()


def test_product_search():
    cryptos = search_products(all_cryptos, 'Bitcoin')
    assert type(cryptos) is dict and len(cryptos) > 0, 'cryptos is invalid'

    etfs = search_products(all_etfs, 'technology')
    assert type(etfs) is dict and len(etfs) > 0, 'etfs is invalid'

    equities = search_products(all_equities, 'technology')
    assert type(equities) is dict and len(equities) > 0, 'equities is invalid'

    equities = search_products(all_equities, 'APPLE', search='long_name')
    assert type(equities) is dict and len(equities) > 0, 'equities (APPLE) is invalid'

    equities = search_products(all_equities, 'United States', search='country')
    assert type(equities) is dict and len(equities) > 0, 'equities (United States) is invalid'

    funds = search_products(all_funds, 'nasdaq')
    assert type(funds) is dict and len(funds) > 0, 'funds is invalid'

    currencies = search_products(all_currencies, 'EUR', search='currency')
    assert type(currencies) is dict and len(currencies) > 0, 'currencies is invalid'

    indices = search_products(all_indices, 'us', search='market')
    assert type(indices) is dict and len(indices) > 0, 'indices is invalid'

    moneymarkets = search_products(all_moneymarkets, 'us', search='market')
    assert type(moneymarkets) is dict and len(moneymarkets) > 0, 'moneymarkets is invalid'


if __name__ == '__main__':
    pytest.main([__file__])
