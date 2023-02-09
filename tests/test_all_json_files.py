from financedatabase.json_picker import (
    select_cryptocurrencies,
    select_equities,
    select_moneymarkets,
    select_etfs,
    select_funds,
    select_indices,
    select_currencies,
)
import pytest


def test_all_json_files():
    all_cryptos = select_cryptocurrencies()
    assert (
        type(all_cryptos) is dict and len(all_cryptos) > 0
    ), "all_cryptos Cryptos dictionary is invalid."

    all_etfs = select_etfs()
    assert (
        type(all_etfs) is dict and len(all_etfs) > 0
    ), "all_etfs dictionary is invalid."

    all_equities = select_equities()
    assert (
        type(all_equities) is dict and len(all_equities) > 0
    ), "all_equities dictionary is invalid."

    all_funds = select_funds()
    assert (
        type(all_funds) is dict and len(all_funds) > 0
    ), "all_funds dictionary is invalid."

    all_currencies = select_currencies()
    assert (
        type(all_currencies) is dict and len(all_currencies) > 0
    ), "all_currencies dictionary is invalid."

    all_indices = select_indices()
    assert (
        type(all_indices) is dict and len(all_indices) > 0
    ), "all_indices dictionary is invalid."

    all_moneymarkets = select_moneymarkets()
    assert (
        type(all_moneymarkets) is dict and len(all_moneymarkets) > 0
    ), "all_moneymarkets dictionary is invalid."


if __name__ == "__main__":
    pytest.main([__file__])
