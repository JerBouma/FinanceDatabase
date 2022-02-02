import json
import os
from tqdm import tqdm


def fill_data_points_funds(data_symbol, exchange_rates, options=None):
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
        options['currency'] = data_symbol['price']['currency']
    except (TypeError, KeyError):
        options['currency'] = None
    try:
        options['summary'] = data_symbol['assetProfile']['longBusinessSummary']
    except (TypeError, KeyError):
        options['summary'] = None
    try:
        options['manager_name'] = data_symbol['fundProfile']['managementInfo']['managerName']
    except (TypeError, KeyError):
        options['manager_name'] = None
    try:
        options['manager_bio'] = data_symbol['fundProfile']['managementInfo']['managerBio']
    except (TypeError, KeyError):
        options['manager_bio'] = None
    try:
        options['category'] = data_symbol['fundProfile']['categoryName']
    except (TypeError, KeyError):
        options['category'] = None
    try:
        options['family'] = data_symbol['fundProfile']['family']
    except (TypeError, KeyError):
        options['family'] = None
    try:
        options['exchange'] = data_symbol['quoteType']['exchange']
    except (TypeError, KeyError):
        options['exchange'] = None
    try:
        options['market'] = data_symbol['quoteType']['market']
    except (TypeError, KeyError):
        options['market'] = None
    try:
        if options['currency'] != 'USD':
            exchange_rate = exchange_rates.loc[f"{options['currency']}USD=X"]
        else:
            exchange_rate = 1

        options['total_assets'] = data_symbol['summaryDetail']['totalAssets'] * exchange_rate
    except (TypeError, KeyError):
        options['total_assets'] = None

    return options


def make_directories_and_fill_json_funds(data, directory_name, exchange_rates):
    try:
        os.mkdir(directory_name)
        category_dictionaries = {}
        symbols_dictionaries = {}
        Errors = {}
    except FileExistsError:
        return print(directory_name + " already exists. Please delete or rename the directory "
                                      "before continuing")

    print("Creating folder structure")
    for symbol in tqdm(data):
        options = fill_data_points_funds(data[symbol], exchange_rates)
        symbols_dictionaries[symbol] = options

        try:
            category = data[symbol]['fundProfile']['categoryName']

            if category not in category_dictionaries and category is not None:
                if len(category) > 0:
                    category_dictionaries[category] = {}

            category_dictionaries[category][symbol] = options
        except (TypeError, KeyError) as e:
            Errors[symbol + ' Category'] = "Could not be categorized due to: " + str(e)

    print('Filling folders with data..')
    for category in tqdm(category_dictionaries.keys()):
        category_new = category.replace('/', ' ')
        with open(directory_name + '/' + category_new + '.json', 'w') as handle:
            json.dump(category_dictionaries[category], handle, indent=4)
    with open(directory_name + '/_' + directory_name + ".json", 'w') as handle:
        json.dump(symbols_dictionaries, handle, indent=4)

    print(f'Creating {directory_name} list..')
    funds_list = {}
    for fund in tqdm(symbols_dictionaries):
        if '.' not in fund:
            if symbols_dictionaries[fund]['short_name'] is None:
                continue
            else:
                funds_list[symbols_dictionaries[fund]['short_name']] = fund

    with open(directory_name + '/_' + directory_name + " List.json", 'w') as handle:
        json.dump(funds_list, handle, indent=4)

    if Errors:
        print("A couple of tickers were not able to be categorized. Please check the output of this function.")
        return Errors
