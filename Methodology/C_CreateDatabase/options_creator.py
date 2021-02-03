import json
import os
from tqdm import tqdm


def fill_data_points_options(data_symbol, options=None):
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
        options['underlying'] = data_symbol['price']['underlyingSymbol']
    except (TypeError, KeyError):
        options['underlying'] = None
    try:
        options['market'] = data_symbol['quoteType']['market']
    except (TypeError, KeyError):
        options['market'] = None
    try:
        options['exchange'] = data_symbol['quoteType']['exchange']
    except (TypeError, KeyError):
        options['exchange'] = None
    return options


def make_directories_and_fill_json_options(data, directory_name):
    try:
        symbols_dictionaries = {}
        Errors = {}
    except FileExistsError:
        return print(directory_name + " already exists. Please delete or rename the directory "
                                      "before continuing")

    print("Creating folder structure")
    for symbol in tqdm(data):
        options = fill_data_points_options(data[symbol])
        symbols_dictionaries[symbol] = options

    print('Filling folder with data..')
    with open(directory_name + '/' + 'Options.json', 'w') as handle:
        json.dump(symbols_dictionaries, handle, indent=4)

    if Errors:
        print("A couple of tickers were not able to be categorized. Please check the output of this function.")
        return Errors
