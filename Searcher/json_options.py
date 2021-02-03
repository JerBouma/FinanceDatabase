import requests
import json


def show_options(product):
    URL = ("https://raw.githubusercontent.com/JerBouma/FinanceDatabase/master/"
           "Database/Categories/")

    if product.lower() not in ['cryptocurrencies', 'currencies', 'equities', 'etfs', 'funds']:
        raise ValueError((product.lower() + " is not an available options. Please choose either 'cryptocurrencies', "
                                            "'currencies', 'equities', 'etfs' or 'funds'"))
    try:
        json_file = URL + product.lower() + '_options.json'
        request = requests.get(json_file)
        json_data = json.loads(request.text)
    except json.decoder.JSONDecodeError:
        raise ValueError("Not able to find the options for " + product.lower())

    return json_data


def search_products(database, query, new_database=None):
    if new_database is None:
        new_database = {}

    for symbol in database:
        try:
            if query in database[symbol]['summary']:
                new_database[symbol] = database[symbol]
        except (TypeError, KeyError):
            continue

    return new_database
