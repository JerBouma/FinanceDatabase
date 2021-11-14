import json
import os
from tqdm import tqdm
from itertools import islice


def fill_data_points_equities(data_symbol, options=None):
    if options is None:
        options = {}
    try:
        options['short_name'] = data_symbol['quoteType']['shortName']
    except (TypeError, KeyError):
        options['short_name'] = None
    try:
        options['long_name'] = data_symbol['quoteType']['longName']
    except (TypeError, KeyError):
        options['long_name'] = None
    try:
        options['summary'] = data_symbol['summaryProfile']['longBusinessSummary']
    except (TypeError, KeyError):
        options['summary'] = None
    try:
        options['currency'] = data_symbol['price']['currency']
    except (TypeError, KeyError):
        options['currency'] = None
    try:
        options['sector'] = data_symbol['summaryProfile']['sector']
    except (TypeError, KeyError):
        options['sector'] = None
    try:
        options['industry'] = data_symbol['summaryProfile']['industry'].replace('/', ' ').replace('\u2014', ' - ')
    except (TypeError, KeyError):
        options['industry'] = None
    try:
        options['exchange'] = data_symbol['quoteType']['exchange']
    except (TypeError, KeyError):
        options['exchange'] = None
    try:
        options['market'] = data_symbol['quoteType']['market']
    except (TypeError, KeyError):
        options['market'] = None
    try:
        options['country'] = data_symbol['summaryProfile']['country']
    except (TypeError, KeyError):
        options['country'] = None
    try:
        options['state'] = data_symbol['summaryProfile']['state']
    except (TypeError, KeyError):
        options['state'] = None
    try:
        options['city'] = data_symbol['summaryProfile']['city']
    except (TypeError, KeyError):
        options['city'] = None
    try:
        options['zipcode'] = data_symbol['summaryProfile']['zip']
    except (TypeError, KeyError):
        options['zipcode'] = None
    try:
        options['website'] = data_symbol['summaryProfile']['website']
    except (TypeError, KeyError):
        options['website'] = None
    try:
        if data_symbol['price']['marketCap'] <= 2e9:
            options['market_cap'] = 'Small Cap'
        elif (data_symbol['price']['marketCap'] > 2e9) and (data_symbol['price']['marketCap'] < 10e9):
            options['market_cap'] = 'Mid Cap'
        elif data_symbol['price']['marketCap'] >= 10e9:
            options['market_cap'] = 'Large Cap'
    except (TypeError, KeyError):
        options['market_cap'] = None

    return options


def make_directories_and_fill_json_equities(data, directory_name):
    try:
        os.mkdir(directory_name)
        os.mkdir(directory_name + '/Sectors')
        os.mkdir(directory_name + '/Countries')
        os.mkdir(directory_name + '/Industries')
        industry_dictionaries = {}
        sector_dictionaries = {}
        sector_industry_dictionaries = {}
        country_dictionaries = {}
        country_industry_dictionaries = {}
        country_sector_dictionaries = {}
        country_sector_industry_dictionaries = {}
        symbols_dictionaries = {}
        Errors = {}
    except FileExistsError:
        return print(directory_name + " already exists. Please delete or rename the directory "
                                      "before continuing")

    print("Creating folder structure")
    for symbol in tqdm(data):
        options = fill_data_points_equities(data[symbol])
        symbols_dictionaries[symbol] = options

        try:
            industry = data[symbol]['summaryProfile']['industry'].replace('/', ' ').replace('\u2014', ' - ')

            if industry not in industry_dictionaries and industry is not None:
                if len(industry) > 0:
                    industry_dictionaries[industry] = {}

            industry_dictionaries[industry][symbol] = options
        except (TypeError, KeyError) as e:
            Errors[symbol + ' Industry'] = "Could not be filled in 'Industry' part due to: " + str(e)

        try:
            sector_directories = os.listdir(directory_name + '/Sectors')
            sector = data[symbol]['summaryProfile']['sector']
            industry = data[symbol]['summaryProfile']['industry'].replace('/', ' ').replace('\u2014', ' - ')

            if sector not in sector_directories and sector is not None:
                if len(sector) > 0:
                    os.mkdir(directory_name + '/Sectors/' + sector)
                    sector_dictionaries[sector] = {}
                    sector_industry_dictionaries[sector] = {}
            if industry not in sector_industry_dictionaries[sector]:
                sector_industry_dictionaries[sector][industry] = {}

            sector_dictionaries[sector][symbol] = options
            sector_industry_dictionaries[sector][industry][symbol] = options
        except (TypeError, KeyError) as e:
            Errors[symbol + ' Sector'] = "Could not be filled in 'Sectors' part due to: " + str(e)

        try:
            sector = data[symbol]['summaryProfile']['sector']
            industry = data[symbol]['summaryProfile']['industry'].replace('/', ' ').replace('\u2014', ' - ')
            country_directories = os.listdir(directory_name + '/Countries')
            country = data[symbol]['summaryProfile']['country']

            if country not in country_directories and country is not None:
                if len(country) > 0:
                    os.mkdir(directory_name + '/Countries/' + country)
                    os.mkdir(directory_name + '/Countries/' + country + '/Industries')
                    country_dictionaries[country] = {}
                    country_industry_dictionaries[country] = {}
                    country_sector_dictionaries[country] = {}
                    country_sector_industry_dictionaries[country] = {}
            if sector not in country_sector_industry_dictionaries[country] and sector is not None:
                if len(sector) > 0:
                    os.mkdir(directory_name + '/Countries/' + country + '/' + sector)
                    country_sector_dictionaries[country][sector] = {}
                    country_sector_industry_dictionaries[country][sector] = {}
            if industry not in country_sector_industry_dictionaries[country][sector]:
                if len(industry) > 0:
                    country_industry_dictionaries[country][industry] = {}
                    country_sector_industry_dictionaries[country][sector][industry] = {}

            country_dictionaries[country][symbol] = options
            country_industry_dictionaries[country][industry][symbol] = options
            country_sector_dictionaries[country][sector][symbol] = options
            country_sector_industry_dictionaries[country][sector][industry][symbol] = options
        except (TypeError, KeyError) as e:
            Errors[symbol + ' Country'] = "Could not be placed in 'Country' part due to " + str(e)
            continue

    print('Filling folders with data..')
    for industry in tqdm(industry_dictionaries.keys()):
        with open(directory_name + '/Industries/' + industry + '.json', 'w') as handle:
            json.dump(industry_dictionaries[industry], handle, indent=4)

    for sector in tqdm(sector_industry_dictionaries.keys()):
        with open(directory_name + '/Sectors/' + sector + '/_' + sector + '.json', 'w') as handle:
            json.dump(sector_dictionaries[sector], handle, indent=4)
        for industry in sector_industry_dictionaries[sector].keys():
            with open(directory_name + '/Sectors/' + sector + '/' + industry + '.json', 'w') as handle:
                json.dump(sector_industry_dictionaries[sector][industry], handle, indent=4)

    for country in tqdm(country_sector_industry_dictionaries.keys()):
        with open(directory_name + '/Countries/' + country + '/' + country + '.json', 'w') as handle:
            json.dump(country_dictionaries[country], handle, indent=4)
        for sector in country_sector_industry_dictionaries[country].keys():
            with open(directory_name + '/Countries/' + country + '/' + sector + '/_' + sector + '.json', 'w') as handle:
                json.dump(country_sector_dictionaries[country][sector], handle, indent=4)
            for industry in country_sector_industry_dictionaries[country][sector].keys():
                with open(directory_name + '/Countries/' + country + '/' + sector +
                          '/' + industry + '.json', 'w') as handle:
                    json.dump(country_sector_industry_dictionaries[country][sector][industry], handle, indent=4)
        for industry in country_industry_dictionaries[country].keys():
            with open(directory_name + '/Countries/' + country + '/Industries/' + industry + '.json',
                      'w') as handle:
                json.dump(country_industry_dictionaries[country][industry], handle, indent=4)

    complete_dictionary = iter(symbols_dictionaries.items())
    symbols_dictionary_part_one = dict(islice(complete_dictionary, len(symbols_dictionaries) // 2))
    symbols_dictionary_part_two = dict(complete_dictionary)

    with open(directory_name + '/' + directory_name + " Part 1.json", 'w') as handle:
        json.dump(symbols_dictionary_part_one, handle, indent=4)
    with open(directory_name + '/' + directory_name + " Part 2.json", 'w') as handle:
        json.dump(symbols_dictionary_part_two, handle, indent=4)

    print(f'Creating {directory_name} list..')
    equities_list = {}
    for equity in tqdm(symbols_dictionaries):
        if '.' not in equity:
            if symbols_dictionaries[equity]['short_name'] is None:
                continue
            else:
                equities_list[symbols_dictionaries[equity]['short_name']] = equity

    with open(directory_name + '/' + directory_name + " List.json", 'w') as handle:
        json.dump(equities_list, handle, indent=4)

    if Errors:
        print("A couple of tickers were not able to be categorized. Please check the output of this function.")
        return Errors
