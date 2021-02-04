import requests
import json


def show_options(product, equities_selection=None):
    """
    Description
    ----
    Returns all options that exist in the database that you
    can use to filter the database.

    Input
    ----
    product (string)
        Gives all data for a specific product which can be
        cryptocurrencies, currencies, equities, etfs or funds.

    Output
    ----
    json_data (dictionary)
        Returns a dictionary with a selection based on the input.
    """
    URL = ("https://raw.githubusercontent.com/JerBouma/FinanceDatabase/master/"
           "Database/Categories/")

    if product.lower() not in ['cryptocurrencies', 'currencies', 'equities', 'etfs', 'funds']:
        raise ValueError((product.lower() + " is not an available options. Please choose either 'cryptocurrencies', "
                                            "'currencies', 'equities', 'etfs' or 'funds'."))
    if equities_selection.lower() not in ['countries', 'sectors', 'industries']:
        raise ValueError((equities_selection.lower() + " is not an available sub selection. Please choose either "
                                                       "'countries', 'sectors' or 'industries'."))
    if equities_selection.lower() in ['countries', 'sectors', 'industries'] and product.lower() != 'equities':
        print("equities_selection is only used for the product 'equities' thus changing product to 'equities'.")
        product = 'equities'

    try:
        if equities_selection:
            json_file = URL + product.lower() + '_' + equities_selection + '.json'
        else:
            json_file = URL + product.lower() + '_options.json'
        request = requests.get(json_file)
        json_data = json.loads(request.text)
    except json.decoder.JSONDecodeError:
        raise ValueError("Not able to find the options for " + product.lower())

    return json_data


def search_products(database, query, new_database=None):
    """
    Description
    ----
    Search in the provided dictionary for a specific query. It
    specifically searches in the 'summary' key which can be found in
    equities, etfs and funds.

    Input
    ----
    database (dictionary)
        A dictionary that has data from the Database.
    query (string)
        The search term that is used to search in the dictionary.
    new_database (dictionary, default is None)
        If filled, is used to add data to based on the query.

    Output
    ----
    json_data (dictionary)
        Returns a dictionary with a selection based on the input.
    """
    if new_database is None:
        new_database = {}

    for symbol in database:
        try:
            if query in database[symbol]['summary']:
                new_database[symbol] = database[symbol]
        except (TypeError, KeyError):
            continue

    return new_database
