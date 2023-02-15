import json

import requests

from .helpers import FinanceDatabase


class Cryptos(FinanceDatabase):
    FILE_NAME = "cryptos.csv"


def select_cryptocurrencies(
    cryptocurrency=None,
    base_url="https://raw.githubusercontent.com/JerBouma/FinanceDatabase/main/"
    "Database/Cryptocurrencies",
    use_local_location=False,
    all_cryptocurrencies_json="_Cryptocurrencies",
):
    """
    Description
    ----
    Returns all cryptocurrencies when no input is given and has the option to give
    a specific set of symbols for the cryptocurrency you provide.

    Input
    ----
    cryptocurrency (string, default is None)
        If filled, gives all data for a specific cryptocurrency.
    base_url (string, default is GitHub location)
        The possibility to enter your own location if desired.
    use_local_location (string, default False)
        The possibility to select a local location (i.e. based on Windows path)
    all_cryptocurrencies_json (string, default is _Cryptocurrencies)
        Alter the name of the all cryptocurrencies json if desired.

    Output
    ----
    json_data (dictionary)
        Returns a dictionary with a selection or all data based on the input.
    """
    specific_path = cryptocurrency if cryptocurrency else all_cryptocurrencies_json
    json_file = f"{base_url}/{specific_path}.json"
    if use_local_location:
        with open(json_file) as json_local:
            return json.load(json_local)

    try:
        request = requests.get(json_file, timeout=30)
        return json.loads(request.text)
    except json.decoder.JSONDecodeError:
        print("Not able to find any data.")
        return {}
