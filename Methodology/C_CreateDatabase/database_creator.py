import os
import json
from tqdm import tqdm
import cryptocurrencies_creator, currencies_creator, equities_creator, etfs_creator, funds_creator, futures_creator, indices_creator, moneymarkets_creator, options_creator, utilities

DATA_FOLDER = r"C:/Users/jerbo/Python/FinanceDatabase"
EXCLUDED_TYPES = ['Option', 'Futures']
naming = {
    'Cryptocurrencies': 'CRYPTOCURRENCY',
    'Currencies': 'Currency',
    'Equities': 'Equity',
    'ETFs': 'ETF',
    'Funds': 'Fund',
    'Futures': 'Futures',
    'Indices': 'Index',
    'Moneymarkets': 'MoneyMarket',
    'Options': 'Option'}

for folder in naming:
    print("--- " + folder + " ---")
    if folder in os.listdir():
        print(f"{folder} is skipped as the folder already exists")
        continue
    if naming[folder] in EXCLUDED_TYPES:
        print(f"{folder} is skipped due to being time-dependent")
        continue
    items = {}
    print("Creating a list with symbols..")
    for item in tqdm(os.listdir(f"{DATA_FOLDER}/Data/{naming[folder]}")):
        items[item.strip('.pickle')] = item
    data_set = {}
    print("Loading all pickles..")
    for data in tqdm(items):
        data_set[data] = utilities.read_pickle(f"{DATA_FOLDER}/Data/{naming[folder]}/{items[data]}")

    eval(folder.lower() + '_creator' + ".make_directories_and_fill_json_" + folder.lower())(data_set, folder)

    try:
        os.mkdir("Categories")
    except FileExistsError:
        None

    if folder == 'Cryptocurrencies':
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
    elif folder == 'Currencies':
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
    elif folder == 'Equities':
        print("Creating equities countries, sectors and industries..")
        countries = []
        sectors = []
        industries = []

        for symbol in tqdm(data_set):
            try:
                country = data_set[symbol]['summaryProfile']['country']
                sector = data_set[symbol]['summaryProfile']['sector']
                industry = data_set[symbol]['summaryProfile']['industry'].replace('/', ' ').replace('\u2014', ' - ')

                if country not in countries:
                    countries.append(country)
                if sector not in sectors:
                    sectors.append(sector)
                if industry not in industries:
                    industries.append(industry)
            except (TypeError, KeyError):
                continue
        with open("Categories/equities_countries.json", 'w') as handle:
            json.dump(sorted(countries), handle, indent=4)
        with open("Categories/equities_sectors.json", 'w') as handle:
            json.dump(sorted(sectors), handle, indent=4)
        with open("Categories/equities_industries.json", 'w') as handle:
            json.dump(sorted(industries), handle, indent=4)
    elif folder == 'ETFs':
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
    elif folder == 'Funds':
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
