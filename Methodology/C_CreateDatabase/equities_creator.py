import json
import os
from tqdm import tqdm


def fill_data_points_equities(data_symbol, options=None):
    if options is None:
        options = {}
    try:
        options['short_name'] = data_symbol['quoteType']['shortName']
    except (TypeError, KeyError):
        options['short_name'] = 'None'
    try:
        options['long_name'] = data_symbol['quoteType']['longName']
    except (TypeError, KeyError):
        options['long_name'] = 'None'
    try:
        options['summary'] = data_symbol['summaryProfile']['longBusinessSummary']
    except (TypeError, KeyError):
        options['summary'] = 'None'
    try:
        options['currency'] = data_symbol['price']['currency']
    except (TypeError, KeyError):
        options['currency'] = 'None'
    try:
        options['sector'] = data_symbol['summaryProfile']['sector']
    except (TypeError, KeyError):
        options['sector'] = 'None'
    try:
        options['industry'] = data_symbol['summaryProfile']['industry']
    except (TypeError, KeyError):
        options['industry'] = 'None'
    try:
        options['exchange'] = data_symbol['quoteType']['exchange']
    except (TypeError, KeyError):
        options['exchange'] = 'None'
    try:
        options['market'] = data_symbol['quoteType']['market']
    except (TypeError, KeyError):
        options['market'] = 'None'
    try:
        options['country'] = data_symbol['summaryProfile']['country']
    except (TypeError, KeyError):
        options['country'] = 'None'
    try:
        options['city'] = data_symbol['summaryProfile']['city']
    except (TypeError, KeyError):
        options['city'] = 'None'
    return options


def make_directories_and_fill_json_equities(data, directory_name):
    try:
        os.mkdir(directory_name)
        os.mkdir(directory_name + '/Sectors')
        os.mkdir(directory_name + '/Countries')
        sector_dictionaries = {}
        sector_industry_dictionaries = {}
        country_dictionaries = {}
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
            sector_directories = os.listdir(directory_name + '/Sectors')
            sector = data[symbol]['summaryProfile']['sector']
            industry = data[symbol]['summaryProfile']['industry']

            if sector is None:
                sector = 'Unknown Sector'
            if sector not in sector_directories and len(sector) > 0:
                os.mkdir(directory_name + '/Sectors/' + sector)
                sector_dictionaries[sector] = {}
                sector_industry_dictionaries[sector] = {}
            if industry is None:
                industry = 'Unknown Industry'
            if industry not in sector_industry_dictionaries[sector]:
                sector_industry_dictionaries[sector][industry] = {}

            sector_dictionaries[sector][symbol] = options
            sector_industry_dictionaries[sector][industry][symbol] = options
        except (TypeError, KeyError) as e:
            Errors[symbol + ' Sector'] = "Could not be filled in 'Sectors' part due to: " + str(e)

        try:
            sector = data[symbol]['summaryProfile']['sector']
            industry = data[symbol]['summaryProfile']['industry']
            country_directories = os.listdir(directory_name + '/Countries')
            country = data[symbol]['summaryProfile']['country']

            if country not in country_directories and len(country) > 0:
                os.mkdir(directory_name + '/Countries/' + country)
                country_dictionaries[country] = {}
                country_sector_dictionaries[country] = {}
                country_sector_industry_dictionaries[country] = {}
            if sector not in country_sector_industry_dictionaries[country] and len(sector) > 0:
                os.mkdir(directory_name + '/Countries/' + country + '/' + sector)
                country_sector_dictionaries[country][sector] = {}
                country_sector_industry_dictionaries[country][sector] = {}
            if industry not in country_sector_industry_dictionaries[country][sector]:
                country_sector_industry_dictionaries[country][sector][industry] = {}

            country_dictionaries[country][symbol] = options
            country_sector_dictionaries[country][sector][symbol] = options
            country_sector_industry_dictionaries[country][sector][industry][symbol] = options
        except (TypeError, KeyError) as e:
            Errors[symbol + ' Country'] = "Could not be placed in 'Country' part due to " + str(e)
            continue

    print('Filling folders with data..')
    for sector in tqdm(sector_industry_dictionaries.keys()):
        with open(directory_name + '/Sectors/' + sector + '/_' + sector + '.json', 'w') as handle:
            json.dump(sector_dictionaries[sector], handle, indent=4)
        for industry in sector_industry_dictionaries[sector].keys():
            industry_new = industry.replace('/', ' ')
            with open(directory_name + '/Sectors/' + sector + '/' + industry_new + '.json', 'w') as handle:
                json.dump(sector_industry_dictionaries[sector][industry], handle, indent=4)

    for country in tqdm(country_sector_industry_dictionaries.keys()):
        with open(directory_name + '/Countries/' + country + '/' + country + '.json', 'w') as handle:
            json.dump(country_dictionaries[country], handle, indent=4)
        for sector in country_sector_industry_dictionaries[country].keys():
            with open(directory_name + '/Countries/' + country + '/' + sector + '/_' + sector + '.json', 'w') as handle:
                json.dump(country_sector_dictionaries[country][sector], handle, indent=4)
            for industry in country_sector_industry_dictionaries[country][sector].keys():
                industry_new = industry.replace('/', ' ')
                with open(directory_name + '/Countries/' + country + '/' + sector +
                          '/' + industry_new + '.json', 'w') as handle:
                    json.dump(country_sector_industry_dictionaries[country][sector][industry], handle, indent=4)
    with open(directory_name + '/' + directory_name + ".json", 'w') as handle:
        json.dump(symbols_dictionaries, handle, indent=4)

    if Errors:
        print("A couple of tickers were not able to be categorized. Please check the output of this function.")
        return Errors
