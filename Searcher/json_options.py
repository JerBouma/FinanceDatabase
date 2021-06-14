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
    equities_selection (string)
        Gives a sub selection fo the possibilities for equities which can be
        countries, sectors or industries.
    Output
    ----
    json_data (dictionary)
        Returns a dictionary with a selection based on the input.
    """
    URL = ("https://raw.githubusercontent.com/JerBouma/FinanceDatabase/master/"
           "Database/Categories/")

    if product.lower() not in ['cryptocurrencies', 'currencies', 'equities', 'etfs', 'funds']:
        raise ValueError(f"{product.lower()} is not an available options. Please choose either 'cryptocurrencies', "
                         f"'currencies', 'equities', 'etfs' or 'funds'.")
    if equities_selection is not None:
        if equities_selection.lower() not in ['countries', 'sectors', 'industries']:
            raise ValueError(f"{equities_selection.lower()} is not an available sub selection. Please choose either "
                             "'countries', 'sectors' or 'industries'.")
        if equities_selection.lower() in ['countries', 'sectors', 'industries'] and product.lower() != 'equities':
            print("equities_selection is only used for the product 'equities' thus changing product to 'equities'.")
            product = 'equities'

    try:
        if product.lower() == 'equities' and equities_selection is None:
            json_data = {}
            for option in ['countries', 'sectors', 'industries']:
                json_file = f"{URL}{product.lower()}_{option}.json"
                request = requests.get(json_file)
                json_data[option] = json.loads(request.text)
            return json_data
        if equities_selection:
            json_file = f"{URL}{product.lower()}_{equities_selection}.json"
        else:
            json_file = f"{URL}{product.lower()}_options.json"
        request = requests.get(json_file)
        json_data = json.loads(request.text)
    except json.decoder.JSONDecodeError:
        raise ValueError(f"Not able to find the options for {product.lower()}.")

    return json_data


def search_products(database, query, search='summary', case_sensitive=False, new_database=None):
    """
    Description
    ----
    Search in the provided dictionary for a specific query. By default
    it searches in the 'summary' key which can be found in equities, etfs and funds.

    Input
    ----
    database (dictionary)
        A dictionary that has data from the Database.
    query (string)
        The search term that is used to search in the dictionary.
    search (string):
        The key of the dictionary you wish to search in. The default
        is set to 'summary'.
    case_sensitive (boolean):
        A variable that determines whether the query needs to be case
        sensitive or not. Default is False.
    new_database (dictionary, default is None)
        If filled, is used to add data to based on the query.

    Output
    ----
    json_data (dictionary)
        Returns a dictionary with a selection based on the input.
    """
    if new_database is None:
        new_database = {}

    try:
        all_keys = list(database[list(database.keys())[0]].keys())
    except IndexError:
        raise ValueError("The database is empty. Please fill the database with one of the 'select' functions.")
    if search not in all_keys:
        raise ValueError(f"The value {search} is not an option for the 'search' variable. "
                         f"Please select one of the following:\n{all_keys}")

    for symbol in database:
        try:
            string = database[symbol][search]
            if not case_sensitive:
                query = query.lower()
                string = database[symbol][search].lower()
            if query in string:
                new_database[symbol] = database[symbol]
        except (TypeError, KeyError, AttributeError):
            continue

    return new_database
