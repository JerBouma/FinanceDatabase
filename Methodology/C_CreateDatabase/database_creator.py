import os
from Methodology.C_CreateDatabase import (cryptocurrencies_creator, currencies_creator, equities_creator, etfs_creator,
                                          funds_creator, futures_creator, indices_creator, moneymarkets_creator,
                                          options_creator, utilities)

pickles = {
    'Cryptocurrencies': (
        r'C:\Users\jerbo\Google Drive\Programming\Python\FinanceDatabase\Pickles\CryptoCurrencies.pickle'),
    'Currencies': r'C:\Users\jerbo\Google Drive\Programming\Python\FinanceDatabase\Pickles\Currencies.pickle',
    'Equities': r'C:\Users\jerbo\Google Drive\Programming\Python\FinanceDatabase\Pickles\Equities.pickle',
    'ETFs': r'C:\Users\jerbo\Google Drive\Programming\Python\FinanceDatabase\Pickles\ETFs.pickle',
    'Funds': r'C:\Users\jerbo\Google Drive\Programming\Python\FinanceDatabase\Pickles\Funds.pickle',
    'Futures': r'C:\Users\jerbo\Google Drive\Programming\Python\FinanceDatabase\Pickles\Futures.pickle',
    'Indices': r'C:\Users\jerbo\Google Drive\Programming\Python\FinanceDatabase\Pickles\Indices.pickle',
    'Moneymarkets': r'C:\Users\jerbo\Google Drive\Programming\Python\FinanceDatabase\Pickles\MoneyMarkets.pickle',
    'Options': r'C:\Users\jerbo\Google Drive\Programming\Python\FinanceDatabase\Pickles\Options.pickle'}

for item in pickles.keys():
    print("--- " + item + " ---")
    data_set = utilities.read_pickle(pickles[item])
    if item in ['Futures', 'Moneymarkets', 'Options']:
        if 'Other' not in os.listdir():
            os.mkdir('Other')
        eval(item.lower() + '_creator' + ".make_directories_and_fill_json_" + item.lower())(data_set, "Other")
    else:
        eval(item.lower() + '_creator' + ".make_directories_and_fill_json_" + item.lower())(data_set, item)
