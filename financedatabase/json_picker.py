"""JSON Picker"""
import json
from pathlib import Path

import requests
import pandas as pd

# pylint: disable=unspecified-encoding, too-many-arguments, too-many-locals, too-many-return-statements,
# pylint: disable=too-many-return-statements,too-many-branches,too-many-statements,line-too-long

file_path = Path(__file__).parent.parent / "Database"


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
    if cryptocurrency:
        json_file = f"{base_url}/{cryptocurrency}.json"
        if use_local_location:
            with open(json_file) as json_local:
                json_data = json.load(json_local)
        else:
            try:
                request = requests.get(json_file, timeout=30)
                json_data = json.loads(request.text)
            except json.decoder.JSONDecodeError:
                print(f"Not able to find any data for {cryptocurrency}.")
                return {}
    else:
        json_file = f"{base_url}/{all_cryptocurrencies_json}.json"
        if use_local_location:
            with open(json_file) as json_local:
                json_data = json.load(json_local)
        else:
            try:
                request = requests.get(json_file, timeout=30)
                json_data = json.loads(request.text)
            except json.decoder.JSONDecodeError:
                print("Not able to find any data.")
                return {}

    return json_data


def select_currencies(
    currency=None,
    base_url="https://raw.githubusercontent.com/JerBouma/FinanceDatabase/"
    "master/Database/Currencies",
    use_local_location=False,
    all_currencies_json="_Currencies",
):
    """
    Description
    ----
    Returns all currencies when no input is given and has the option to give
    a specific set of symbols for the currency you provide.

    Input
    ----
    currency (string, default is None)
        If filled, gives all data for a specific currency.
    base_url (string, default is GitHub location)
        The possibility to enter your own location if desired.
    use_local_location (string, default False)
        The possibility to select a local location (i.e. based on Windows path)
    all_currencies_json (string, default is _Currencies)
        Alter the name of the all currencies json if desired.

    Output
    ----
    json_data (dictionary)
        Returns a dictionary with a selection or all data based on the input.
    """
    if currency:
        json_file = f"{base_url}/{currency}.json"
        if use_local_location:
            with open(json_file) as json_local:
                json_data = json.load(json_local)
        else:
            try:
                request = requests.get(json_file, timeout=30)
                json_data = json.loads(request.text)
            except json.decoder.JSONDecodeError:
                print(f"Not able to find any data for {currency}.")
                return {}
    else:
        json_file = f"{base_url}/{all_currencies_json}.json"
        if use_local_location:
            with open(json_file) as json_local:
                json_data = json.load(json_local)
        else:
            try:
                request = requests.get(json_file, timeout=30)
                json_data = json.loads(request.text)
            except json.decoder.JSONDecodeError:
                print("Not able to find any data.")
                return {}

    return json_data


def select_etfs(
    category=None,
    exclude_exchanges=True,
    base_url="https://raw.githubusercontent.com/JerBouma/FinanceDatabase/"
    "master/Database/ETFs",
    use_local_location=False,
    all_etfs_json="_ETFs",
):
    """
    Description
    ----
    Returns all ETFs when no input is given and has the option to give
    a specific set of symbols for the category you provide.

    Input
    ----
    category (string, default is None)
        If filled, gives all data for a specific category.
    exclude_exchanges (boolean, default is True):
        Whether you want to exclude exchanges from the search. If False,
        you will receive multiple times i.e. Vanguard S&P 500 from different exchanges.
    base_url (string, default is GitHub location)
        The possibility to enter your own location if desired.
    use_local_location (string, default False)
        The possibility to select a local location (i.e. based on Windows path)
    all_etfs_json (string, default is _ETFs)
        Alter the name of the all etfs json if desired.

    Output
    ----
    json_data (dictionary)
        Returns a dictionary with a selection or all data based on the input.
    """

    if category:
        if use_local_location:
            json_file = f"{base_url}/{category}.json"
            with open(json_file) as json_local:
                json_data = json.load(json_local)
        else:
            try:
                category = category.replace("%", "%25").replace(" ", "%20")
                json_file = f"{base_url}/{category}.json"
                request = requests.get(json_file, timeout=30)
                json_data = json.loads(request.text)
            except json.decoder.JSONDecodeError:
                print(f"Not able to find any data for {category}.")
                return {}
    else:
        json_file = f"{base_url}/{all_etfs_json}.json"
        if use_local_location:
            with open(json_file) as json_local:
                json_data = json.load(json_local)
        else:
            try:
                request = requests.get(json_file, timeout=30)
                json_data = json.loads(request.text)
            except json.decoder.JSONDecodeError:
                print("Not able to find any data.")
                return {}

    if exclude_exchanges:
        for etf in json_data.copy():
            if "." in etf:
                del json_data[etf]
        if len(json_data) == 0:
            print(
                "Because exclude_exchanges is set to True, all available data for this "
                f"combination ({category}) is removed. Set this parameter to False "
                "to obtain data."
            )
            return {}

    return json_data


def select_equities(
    country=None,
    sector=None,
    industry=None,
    exclude_exchanges=True,
    # TODO: remove base_url and use_local_location in a future PR
    base_url="https://raw.githubusercontent.com/JerBouma/FinanceDatabase/"
    "master/Database/Equities",
    use_local_location=False,
):
    """
    Description
    ----
    Returns all equities when no input is given and has the option to give
    a specific set of symbols for the country, sector and/or industry provided.

    The data depends on the combination of inputs. For example Country + Sector
    gives all symbols for a specific sector in a specific country.

    Input
    ----
    country (string, default is None)
        If filled, gives all data for a specific country.
    sector (string, default is None)
        If filled, gives all data for a specific sector.
    industry (string, default is None)
        If filled, gives all data for a specific industry.
    exclude_exchanges (boolean, default is True):
        Whether you want to exclude exchanges from the search. If False,
        you will receive multiple times i.e. Tesla from different exchanges.
    base_url (string, default is GitHub location)
        The possibility to enter your own location if desired.
    use_local_location (string, default False)
        The possibility to select a local location (i.e. based on Windows path)

    Output
    ----
    json_data (dictionary)
        Returns a dictionary with a selection or all data based on the input.
    """
    print("This got hit")
    the_path = file_path / "equities.zip.csv"
    df = pd.read_csv(
        the_path, compression="zip", on_bad_lines="skip", sep=";", index_col=0
    )
    if country:
        df = df[df["country"] == country]
    if sector:
        df = df[df["sector"] == sector]
    if industry:
        df = df[df["industry"] == industry]
    return df.to_json()


def select_funds(
    category=None,
    exclude_exchanges=True,
    base_url="https://raw.githubusercontent.com/JerBouma/FinanceDatabase/"
    "master/Database/Funds",
    use_local_location=False,
    all_funds_json="_Funds",
):
    """
    Description
    ----
    Returns all funds when no input is given and has the option to give
    a specific set of symbols for the category you provide.

    Input
    ----
    category (string, default is None)
        If filled, gives all data for a specific category.
    exclude_exchanges (boolean, default is True):
        Whether you want to exclude exchanges from the search. If False,
        you will receive multiple times i.e. AAEUX from different exchanges.
    base_url (string, default is GitHub location)
        The possibility to enter your own location if desired.
    use_local_location (string, default False)
        The possibility to select a local location (i.e. based on Windows path)
    all_funds_json (string, default is _Funds)
        Alter the name of the all funds json if desired.

    Output
    ----
    json_data (dictionary)
        Returns a dictionary with a selection or all data based on the input.
    """
    if category:
        if use_local_location:
            json_file = f"{base_url}/{category}.json"
            with open(json_file) as json_local:
                json_data = json.load(json_local)
        else:
            try:
                category = category.replace("%", "%25").replace(" ", "%20")
                json_file = f"{base_url}/{category}.json"
                request = requests.get(json_file, timeout=30)
                json_data = json.loads(request.text)
            except json.decoder.JSONDecodeError:
                print(f"Not able to find any data for {category}.")
                return {}
    else:
        json_file = f"{base_url}/{all_funds_json}.json"
        if use_local_location:
            with open(json_file) as json_local:
                json_data = json.load(json_local)
        else:
            try:
                request = requests.get(json_file, timeout=30)
                json_data = json.loads(request.text)
            except json.decoder.JSONDecodeError:
                print("Not able to find any data.")
                return {}

    if exclude_exchanges:
        for fund in json_data.copy():
            if "." in fund:
                del json_data[fund]
            if len(json_data) == 0:
                raise ValueError(
                    "Because exclude_exchanges is set to True, all available data for "
                    f"this combination ({category}) is removed. Set this parameter to False to "
                    f"obtain data."
                )

    return json_data


def select_indices(
    market=None,
    exclude_exchanges=True,
    base_url="https://raw.githubusercontent.com/JerBouma/FinanceDatabase/"
    "master/Database/Indices",
    use_local_location=False,
    all_indices_json="_Indices",
):
    """
    Description
    ----
    Returns all indices when no input is given and has the option to give
    a specific set of symbols for the market you provide.

    Input
    ----
    market (string, default is None)
        If filled, gives all data for a specific market.
    exclude_exchanges (boolean, default is True):
        Whether you want to exclude exchanges from the search. If False,
        you will receive multiple times i.e. ^GSPC from different exchanges.
    base_url (string, default is GitHub location)
        The possibility to enter your own location if desired.
    use_local_location (string, default False)
        The possibility to select a local location (i.e. based on Windows path)
    all_indices_json (string, default is _Indices)
        Alter the name of the all indices json if desired.

    Output
    ----
    json_data (dictionary)
        Returns a dictionary with a selection or all data based on the input.
    """
    if market:
        json_file = f"{base_url}/{market}.json"
        if use_local_location:
            with open(json_file) as json_local:
                json_data = json.load(json_local)
        else:
            try:
                request = requests.get(json_file, timeout=30)
                json_data = json.loads(request.text)
            except json.decoder.JSONDecodeError:
                print(f"Not able to find any data for {market}.")
                return {}
    else:
        json_file = f"{base_url}/{all_indices_json}.json"
        if use_local_location:
            with open(json_file) as json_local:
                json_data = json.load(json_local)
        else:
            try:
                request = requests.get(json_file, timeout=30)
                json_data = json.loads(request.text)
            except json.decoder.JSONDecodeError:
                print("Not able to find any data.")
                return {}

    if exclude_exchanges:
        for index in json_data.copy():
            if "." in index:
                del json_data[index]
            if len(json_data) == 0:
                raise ValueError(
                    "Because exclude_exchanges is set to True, all available data for this "
                    f"combination ({market}) is removed. Set this parameter to False "
                    "to obtain data."
                )

    return json_data


def select_moneymarkets(
    market=None,
    exclude_exchanges=True,
    base_url="https://raw.githubusercontent.com/JerBouma/FinanceDatabase/"
    "master/Database/Moneymarkets",
    use_local_location=False,
    all_moneymarkets_json="_Moneymarkets",
):
    """
    Description
    ----
    Returns all moneymarkets when no input is given and has the option to give
    a specific set of symbols for the market you provide.

    Input
    ----
    market (string, default is None)
        If filled, gives all data for a specific market.
    exclude_exchanges (boolean, default is True):
        Whether you want to exclude exchanges from the search. If False,
        you will receive multiple times i.e. SOND from different exchanges.
    base_url (string, default is GitHub location)
        The possibility to enter your own location if desired.
    use_local_location (string, default False)
        The possibility to select a local location (i.e. based on Windows path)
    all_moneymarkets_json (string, default is _Moneymarkets)
        Alter the name of the all moneymarkets json if desired.

    Output
    ----
    json_data (dictionary)
        Returns a dictionary with a selection or all data based on the input.
    """
    if market:
        json_file = f"{base_url}/{market}.json"
        if use_local_location:
            with open(json_file) as json_local:
                json_data = json.load(json_local)
        else:
            try:
                request = requests.get(json_file, timeout=30)
                json_data = json.loads(request.text)
            except json.decoder.JSONDecodeError:
                print(f"Not able to find any data for {market}.")
                return {}
    else:
        json_file = f"{base_url}/{all_moneymarkets_json}.json"
        if use_local_location:
            with open(json_file) as json_local:
                json_data = json.load(json_local)
        else:
            try:
                request = requests.get(json_file, timeout=30)
                json_data = json.loads(request.text)
            except json.decoder.JSONDecodeError:
                print("Not able to find any data.")
                return {}

    if exclude_exchanges:
        for moneymarket in json_data.copy():
            if "." in moneymarket:
                del json_data[moneymarket]
        if len(json_data) == 0:
            print(
                "Because exclude_exchanges is set to True, all available data for this "
                f"combination ({market}) is removed. Set this parameter to False "
                "to obtain data."
            )
            return {}

    return json_data
