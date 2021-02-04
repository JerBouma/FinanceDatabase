import os
import json
from tqdm import tqdm
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

    try:
        os.mkdir("Categories")
    except FileExistsError:
        None

    if item == 'Cryptocurrencies':
        print("Creating cryptocurrencies options..")
        cryptocurrencies = []
        for symbol in tqdm(data_set):
            try:
                if data_set[symbol]['summaryDetail']['fromCurrency'] not in cryptocurrencies:
                    cryptocurrencies.append(data_set[symbol]['summaryDetail']['fromCurrency'])
            except (TypeError, KeyError):
                continue
        if None in cryptocurrencies:
            cryptocurrencies.remove(None)
        with open("Categories/cryptocurrencies_options.json", 'w') as handle:
            json.dump(sorted(cryptocurrencies), handle, indent=4)
    elif item == 'Currencies':
        print("Creating currencies options..")
        currencies = []
        for symbol in tqdm(data_set):
            try:
                if data_set[symbol]['price']['currency'] not in currencies:
                    currencies.append(data_set[symbol]['price']['currency'])
            except (TypeError, KeyError):
                continue
        if None in currencies:
            currencies.remove(None)
        with open("Categories/currencies_options.json", 'w') as handle:
            json.dump(sorted(currencies), handle, indent=4)
    elif item == 'Equities':
        print("Creating equities countries, sectors and industries..")
        countries = []
        sectors = []
        industries = []

        for symbol in tqdm(data_set):
            try:
                country = data_set[symbol]['summaryProfile']['country']
                sector = data_set[symbol]['summaryProfile']['sector']
                industry = data_set[symbol]['summaryProfile']['industry']

                if country not in countries:
                    countries.append(country)
                if sector not in sectors:
                    sectors.append(sector)
                if industry not in industries:
                    industries.append(industry)
            except (TypeError, KeyError):
                None
        with open("Categories/equities_countries.json", 'w') as handle:
            json.dump(sorted(countries), handle, indent=4)
        with open("Categories/equities_sectors.json", 'w') as handle:
            json.dump(sorted(sectors), handle, indent=4)
        with open("Categories/equities_industries.json", 'w') as handle:
            json.dump(sorted(industries), handle, indent=4)
    elif item == 'ETFs':
        print("Creating etfs categories..")
        etfs = []
        for symbol in tqdm(data_set):
            try:
                if data_set[symbol]['fundProfile']['categoryName'] not in etfs:
                    etfs.append(data_set[symbol]['fundProfile']['categoryName'])
            except (TypeError, KeyError):
                continue
        if None in etfs:
            etfs.remove(None)
        with open("Categories/etfs_options.json", 'w') as handle:
            json.dump(sorted(etfs), handle, indent=4)
    elif item == 'Funds':
        print("Creating funds options..")
        funds = []
        for symbol in tqdm(data_set):
            try:
                if data_set[symbol]['fundProfile']['categoryName'] not in funds:
                    funds.append(data_set[symbol]['fundProfile']['categoryName'])
            except (TypeError, KeyError):
                continue
        if None in funds:
            funds.remove(None)
        with open("Categories/funds_options.json", 'w') as handle:
            json.dump(sorted(funds), handle, indent=4)
