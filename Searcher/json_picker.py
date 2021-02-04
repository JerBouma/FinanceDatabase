import requests
import json


def select_cryptocurrencies(cryptocurrency=None):
    """
    Description
    ----
    Returns all cryptocurrencies when no input is given and has the option to give
    a specific set of symbols for the cryptocurrency you provide.

    Input
    ----
    cryptocurrency (string, default is None)
        If filled, gives all data for a specific cryptocurrency.

    Output
    ----
    json_data (dictionary)
        Returns a dictionary with a selection or all data based on the input.
    """
    URL = ("https://raw.githubusercontent.com/JerBouma/FinanceDatabase/master/"
           "Database/Cryptocurrencies/")

    if cryptocurrency:
        try:
            json_file = URL + cryptocurrency + '.json'
            request = requests.get(json_file)
            json_data = json.loads(request.text)
        except json.decoder.JSONDecodeError:
            raise ValueError(f"Not able to find any data for {cryptocurrency}.")
    else:
        try:
            json_file = URL + "_Cryptocurrencies.json"
            request = requests.get(json_file)
            json_data = json.loads(request.text)
        except json.decoder.JSONDecodeError:
            raise ValueError("Not able to find any data.")

    return json_data


def select_currencies(currency=None):
    """
    Description
    ----
    Returns all currencies when no input is given and has the option to give
    a specific set of symbols for the currency you provide.

    Input
    ----
    currency (string, default is None)
        If filled, gives all data for a specific currency.

    Output
    ----
    json_data (dictionary)
        Returns a dictionary with a selection or all data based on the input.
    """
    URL = ("https://raw.githubusercontent.com/JerBouma/FinanceDatabase/master/"
           "Database/Currencies/")

    if currency:
        try:
            json_file = URL + currency + '.json'
            request = requests.get(json_file)
            json_data = json.loads(request.text)
        except json.decoder.JSONDecodeError:
            raise ValueError("Not able to find any data for {currency}.")
    else:
        try:
            json_file = URL + "_Currencies.json"
            request = requests.get(json_file)
            json_data = json.loads(request.text)
        except json.decoder.JSONDecodeError:
            raise ValueError("Not able to find any data.")

    return json_data


def select_etfs(category=None):
    """
    Description
    ----
    Returns all ETFs when no input is given and has the option to give
    a specific set of symbols for the category you provide.

    Input
    ----
    category (string, default is None)
        If filled, gives all data for a specific category.

    Output
    ----
    json_data (dictionary)
        Returns a dictionary with a selection or all data based on the input.
    """
    URL = ("https://raw.githubusercontent.com/JerBouma/FinanceDatabase/master/"
           "Database/ETFs/")

    if category:
        category = category.replace(' ', '%20')
        try:
            json_file = URL + category + '.json'
            request = requests.get(json_file)
            json_data = json.loads(request.text)
        except json.decoder.JSONDecodeError:
            raise ValueError(f"Not able to find any data for {category}.")
    else:
        try:
            json_file = URL + "_ETFs.json"
            request = requests.get(json_file)
            json_data = json.loads(request.text)
        except json.decoder.JSONDecodeError:
            raise ValueError("Not able to find any data.")

    return json_data


def select_equities(country=None, sector=None, industry=None):
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

    Output
    ----
    json_data (dictionary)
        Returns a dictionary with a selection or all data based on the input.
    """
    URL = ("https://raw.githubusercontent.com/JerBouma/FinanceDatabase/master/"
           "Database/Equities/")

    if country and sector and industry:
        country = country.replace(' ', '%20')
        sector = sector.replace(' ', '%20')
        industry = industry.replace(' ', '%20')

        try:
            json_file = URL + 'Countries/' + country + '/' + sector + '/' + industry + ".json"
            request = requests.get(json_file)
            json_data = json.loads(request.text)
        except json.decoder.JSONDecodeError:
            raise ValueError(f"Not able to find any data with the combination of Country ({country}), "
                             f"Sector ({sector}) and Industry ({industry}).")
    elif country and sector:
        country = country.replace(' ', '%20')
        sector = sector.replace(' ', '%20')

        try:
            json_file = URL + 'Countries/' + country + '/' + sector + '/_' + sector + ".json"
            request = requests.get(json_file)
            json_data = json.loads(request.text)
        except json.decoder.JSONDecodeError:
            raise ValueError(f"Not able to find any data with the combination of Country ({country}) "
                             f"and Sector ({sector})")
    elif sector and industry:
        sector = sector.replace(' ', '%20')
        industry = industry.replace(' ', '%20')

        try:
            json_file = URL + 'Sectors/' + sector + '/' + industry + ".json"
            request = requests.get(json_file)
            json_data = json.loads(request.text)
        except json.decoder.JSONDecodeError:
            raise ValueError("Not able to find any data with the combination of, "
                             f"Sector ({sector}) and Industry ({industry}).")
    elif country and industry:
        country = sector.replace(' ', '%20')
        industry = industry.replace(' ', '%20')

        try:
            json_file = URL + 'Countries/' + country + '/Industries/' + industry + ".json"
            request = requests.get(json_file)
            json_data = json.loads(request.text)
        except json.decoder.JSONDecodeError:
            raise ValueError("Not able to find any data with the combination of, "
                             f"Country ({country}) and Industry ({industry}).")
    elif country:
        country = country.replace(' ', '%20')

        try:
            json_file = URL + 'Countries/' + country + '/' + country + ".json"
            request = requests.get(json_file)
            json_data = json.loads(request.text)
        except json.decoder.JSONDecodeError:
            raise ValueError(f"Not able to find any data for {country}.")
    elif sector:
        sector = sector.replace(' ', '%20')

        try:
            json_file = URL + 'Sectors/' + sector + '/_' + sector + ".json"
            request = requests.get(json_file)
            json_data = json.loads(request.text)
        except json.decoder.JSONDecodeError:
            raise ValueError(f"Not able to find any data for {sector}.")
    elif industry:
        industry = industry.replace(' ', '%20')

        try:
            json_file = URL + 'Industries/' + industry + ".json"
            request = requests.get(json_file)
            json_data = json.loads(request.text)
        except json.decoder.JSONDecodeError:
            raise ValueError(f"Not able to find any data for {industry}.")
    else:
        try:
            json_file = URL + "Equities.json"
            request = requests.get(json_file)
            json_data = json.loads(request.text)
        except json.decoder.JSONDecodeError:
            raise ValueError("Not able to find any data.")

    return json_data


def select_funds(category=None):
    """
    Description
    ----
    Returns all funds when no input is given and has the option to give
    a specific set of symbols for the category you provide.

    Input
    ----
    category (string, default is None)
        If filled, gives all data for a specific category.

    Output
    ----
    json_data (dictionary)
        Returns a dictionary with a selection or all data based on the input.
    """
    URL = ("https://raw.githubusercontent.com/JerBouma/FinanceDatabase/master/"
           "Database/Funds/")

    if category:
        category = category.replace(' ', '%20')
        try:
            json_file = URL + category + '.json'
            request = requests.get(json_file)
            json_data = json.loads(request.text)
        except json.decoder.JSONDecodeError:
            raise ValueError(f"Not able to find any data for {category}.")
    else:
        try:
            json_file = URL + "_Funds.json"
            request = requests.get(json_file)
            json_data = json.loads(request.text)
        except json.decoder.JSONDecodeError:
            raise ValueError("Not able to find any data.")

    return json_data


def select_indices(market=None):
    """
    Description
    ----
    Returns all indices when no input is given and has the option to give
    a specific set of symbols for the market you provide.

    Input
    ----
    market (string, default is None)
        If filled, gives all data for a specific market.

    Output
    ----
    json_data (dictionary)
        Returns a dictionary with a selection or all data based on the input.
    """
    URL = ("https://raw.githubusercontent.com/JerBouma/FinanceDatabase/master/"
           "Database/Indices/")

    if market:
        try:
            json_file = URL + market + '.json'
            request = requests.get(json_file)
            json_data = json.loads(request.text)
        except json.decoder.JSONDecodeError:
            raise ValueError(f"Not able to find any data for {market}.")
    else:
        try:
            json_file = URL + "_Indices.json"
            request = requests.get(json_file)
            json_data = json.loads(request.text)
        except json.decoder.JSONDecodeError:
            raise ValueError("Not able to find any data.")

    return json_data


def select_other(product):
    """
    Description
    ----
    Returns all Futures, Moneymarkets or Options based on the
    value you give to the input parameter.

    Input
    ----
    product (string)
        Gives all data for a specific product.

    Output
    ----
    json_data (dictionary)
        Returns a dictionary with a selection or all data based on the input.
    """
    URL = ("https://raw.githubusercontent.com/JerBouma/FinanceDatabase/master/"
           "Database/Other/")

    if product not in ['Futures', 'Moneymarkets', 'Options']:
        raise ValueError(f"{product} is not available. Only 'Futures', 'Moneymarkets' and 'Options'.")

    try:
        json_file = URL + product + ".json"
        request = requests.get(json_file)
        json_data = json.loads(request.text)
    except json.decoder.JSONDecodeError:
        raise ValueError(f"Not able to find any data with type {product}.")

    return json_data
