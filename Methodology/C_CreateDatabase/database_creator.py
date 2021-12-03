import os
import json
from tqdm import tqdm
import financedatabase as fd
import cryptocurrencies_creator, currencies_creator, equities_creator, etfs_creator, funds_creator, futures_creator, indices_creator, moneymarkets_creator, options_creator, utilities

DATA_FOLDER = r"C:\Users\jerbo\Python Offline\FinanceDatabase"
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
    for item in tqdm(os.listdir(f"{DATA_FOLDER}/Data/{naming[folder]}"), desc="Creating a list with symbols"):
        items[item.strip('.pickle')] = item
    data_set = {}
    for data in tqdm(items, desc="Loading all pickles"):
        data_set[data] = utilities.read_pickle(f"{DATA_FOLDER}/Data/{naming[folder]}/{items[data]}")

    eval(f"{folder.lower()}_creator.make_directories_and_fill_json_{folder.lower()}")(data_set, folder)

    try:
        os.mkdir("Categories")
    except FileExistsError:
        pass

    if folder == 'Cryptocurrencies':
        cryptocurrencies = []
        for symbol in tqdm(data_set, desc="Creating cryptocurrencies options"):
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
        currencies = []
        for symbol in tqdm(data_set, desc="Creating currencies options"):
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
        countries = []
        sectors = []
        industries = []

        for symbol in tqdm(data_set, desc="Creating equities countries, sectors and industries options"):
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

        industries_countries = {}
        for sector in tqdm(sectors, desc="Creating specific options for each sector"):
            if not sector or len(sector) == 0:
                continue

            sector_data = fd.select_equities(
                sector=sector, exclude_exchanges=False,
                base_url=r"Equities//",
                use_local_location=True)

            sector_industries_countries = {'Countries': [], 'Industries': []}
            for company in sector_data:
                industry = sector_data[company]['industry']
                country = sector_data[company]['country']

                if industry not in sector_industries_countries['Industries']:
                    sector_industries_countries['Industries'].append(industry)
                if country not in sector_industries_countries['Countries']:
                    sector_industries_countries['Countries'].append(country)
                if industry not in industries_countries:
                    industries_countries[industry] = {'Sector': sector, 'Countries': []}
                if country not in industries_countries[industry]['Countries']:
                    industries_countries[industry]['Countries'].append(country)

            for industry in industries_countries:
                industries_countries[industry]['Countries'] = sorted(industries_countries[industry]['Countries'])

            sector_industries_countries['Industries'] = sorted(sector_industries_countries['Industries'])
            sector_industries_countries['Countries'] = sorted(sector_industries_countries['Countries'])

            with open(f"Equities/Sectors/{sector}/_{sector} Countries and Industries.json", 'w') as handle:
                json.dump(sector_industries_countries, handle, indent=4)

        with open(f"Equities/Industries/_Industries Countries.json", 'w') as handle:
            json.dump(industries_countries, handle, indent=4)

        for country in tqdm(countries, desc="Creating specific options for each country"):
            country_data = fd.select_equities(
                country=country, exclude_exchanges=False,
                base_url=r"Equities//",
                use_local_location=True)

            country_sectors = []
            country_industries = []
            country_sector_industries = {}
            for company in country_data:
                sector = country_data[company]['sector']
                industry = country_data[company]['industry']

                if sector not in country_sectors:
                    country_sectors.append(sector)
                    country_sector_industries[sector] = []
                if industry not in country_industries:
                    country_industries.append(industry)
                if industry not in country_sector_industries[sector]:
                    country_sector_industries[sector].append(industry)

            for sector in country_sectors:
                with open(f"Equities/Countries/{country}/{sector}/_{sector} Industries.json", 'w') as handle:
                    json.dump(sorted(country_sector_industries[sector]), handle, indent=4)

            with open(f"Equities/Countries/{country}/{country} Sectors.json", 'w') as handle:
                json.dump(sorted(country_sectors), handle, indent=4)
            with open(f"Equities/Countries/{country}/{country} Industries.json", 'w') as handle:
                json.dump(sorted(country_industries), handle, indent=4)

    elif folder == 'ETFs':
        etfs = []
        for symbol in tqdm(data_set, desc="Creating etfs options"):
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
        funds = []
        for symbol in tqdm(data_set, desc="Creating funds options"):
            try:
                if data_set[symbol]['fundProfile']['categoryName'] not in funds:
                    funds.append(data_set[symbol]['fundProfile']['categoryName'])
            except (TypeError, KeyError):
                continue
        if None in funds:
            funds.remove(None)
        with open("Categories/funds_options.json", 'w') as handle:
            json.dump(sorted(funds), handle, indent=4)
