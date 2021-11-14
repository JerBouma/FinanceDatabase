import json
import os
from tqdm import tqdm


def fill_data_points_currencies(data_symbol, options=None):
    if options is None:
        options = {}
    try:
        options['short_name'] = data_symbol['quoteType']['shortName']
    except (TypeError, KeyError):
        options['short_name'] = None
    try:
        options['currency'] = data_symbol['price']['currency']
    except (TypeError, KeyError):
        options['currency'] = None
    try:
        options['exchange'] = data_symbol['quoteType']['exchange']
    except (TypeError, KeyError):
        options['exchange'] = None
    try:
        options['market'] = data_symbol['quoteType']['market']
    except (TypeError, KeyError):
        options['market'] = None
    return options


def make_directories_and_fill_json_currencies(data, directory_name):
    try:
        os.mkdir(directory_name)
        currency_dictionaries = {}
        symbols_dictionaries = {}
        Errors = {}
    except FileExistsError:
        return print(directory_name + " already exists. Please delete or rename the directory "
                                      "before continuing")

    print("Creating folder structure")
    for symbol in tqdm(data):
        options = fill_data_points_currencies(data[symbol])
        symbols_dictionaries[symbol] = options

        try:
            currency = data[symbol]['summaryDetail']['currency']

            if currency not in currency_dictionaries and currency is not None:
                if len(currency) > 0:
                    currency_dictionaries[currency] = {}

            currency_dictionaries[currency][symbol] = options
        except (TypeError, KeyError) as e:
            Errors[symbol + ' Category'] = "Could not be categorized due to: " + str(e)

    print('Filling folders with data..')
    for currency in tqdm(currency_dictionaries.keys()):
        currency_new = currency.replace('/', ' ')
        with open(directory_name + '/' + currency_new + '.json', 'w') as handle:
            json.dump(currency_dictionaries[currency], handle, indent=4)
    with open(directory_name + '/_' + directory_name + ".json", 'w') as handle:
        json.dump(symbols_dictionaries, handle, indent=4)

    print(f'Creating {directory_name} list..')
    currencies_list = {}
    for currency in tqdm(symbols_dictionaries):
        if '.' not in currency:
            if symbols_dictionaries[currency]['short_name'] is None:
                continue
            else:
                currencies_list[symbols_dictionaries[currency]['short_name']] = currency

    with open(directory_name + '/_' + directory_name + " List.json", 'w') as handle:
        json.dump(currencies_list, handle, indent=4)

    if Errors:
        print("A couple of tickers were not able to be categorized. Please check the output of this function.")
        return Errors
