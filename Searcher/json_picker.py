import requests
import json


def select_cryptocurrencies(cryptocurrency=None):
    URL = ("https://raw.githubusercontent.com/JerBouma/FinanceDatabase/master/"
           "Database/Cryptocurrencies/")

    if cryptocurrency:
        try:
            json_file = URL + cryptocurrency + '.json'
            request = requests.get(json_file)
            json_data = json.loads(request.text)
        except json.decoder.JSONDecodeError:
            raise ValueError("Not able to find any data for {}".format(cryptocurrency))
    else:
        try:
            json_file = URL + "_Cryptocurrencies.json"
            request = requests.get(json_file)
            json_data = json.loads(request.text)
        except json.decoder.JSONDecodeError:
            raise ValueError("Not able to find any data.")

    return json_data


def select_currencies(currency=None):
    URL = ("https://raw.githubusercontent.com/JerBouma/FinanceDatabase/master/"
           "Database/Currencies/")

    if currency:
        try:
            json_file = URL + currency + '.json'
            request = requests.get(json_file)
            json_data = json.loads(request.text)
        except json.decoder.JSONDecodeError:
            raise ValueError("Not able to find any data for {}".format(currency))
    else:
        try:
            json_file = URL + "_Currencies.json"
            request = requests.get(json_file)
            json_data = json.loads(request.text)
        except json.decoder.JSONDecodeError:
            raise ValueError("Not able to find any data.")

    return json_data


def select_etfs(category=None):
    URL = ("https://raw.githubusercontent.com/JerBouma/FinanceDatabase/master/"
           "Database/ETFs/")

    if category:
        category = category.replace(' ', '%20')
        try:
            json_file = URL + category + '.json'
            request = requests.get(json_file)
            json_data = json.loads(request.text)
        except json.decoder.JSONDecodeError:
            raise ValueError("Not able to find any data for {}".format(category))
    else:
        try:
            json_file = URL + "_ETFs.json"
            request = requests.get(json_file)
            json_data = json.loads(request.text)
        except json.decoder.JSONDecodeError:
            raise ValueError("Not able to find any data.")

    return json_data


def select_equities(country=None, sector=None, industry=None):
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
            raise ValueError("Not able to find any data with the combination of Country ({}), "
                             "Sector ({}), Industry ({}).".format(country, sector, industry))
    elif sector and industry:
        sector = sector.replace(' ', '%20')
        industry = industry.replace(' ', '%20')

        try:
            json_file = URL + 'Sectors/' + sector + '/' + industry + ".json"
            request = requests.get(json_file)
            json_data = json.loads(request.text)
        except json.decoder.JSONDecodeError:
            raise ValueError("Not able to find any data with the combination of, "
                             "Sector ({}), Industry ({}).".format(sector, industry))
    elif country:
        country = country.replace(' ', '%20')

        try:
            json_file = URL + 'Countries/' + country + ".json"
            request = requests.get(json_file)
            json_data = json.loads(request.text)
        except json.decoder.JSONDecodeError:
            raise ValueError("Not able to find any data with the combination of "
                             "Country ({}).".format(country))
    elif industry or (country and industry):
        raise ValueError("Only selecting industry or country and industry results in no data.")
    else:
        try:
            json_file = URL + "Equities.json"
            request = requests.get(json_file)
            json_data = json.loads(request.text)
        except json.decoder.JSONDecodeError:
            raise ValueError("Not able to find any data.")

    return json_data


def select_funds(category=None):
    URL = ("https://raw.githubusercontent.com/JerBouma/FinanceDatabase/master/"
           "Database/Funds/")

    if category:
        category = category.replace(' ', '%20')
        try:
            json_file = URL + category + '.json'
            request = requests.get(json_file)
            json_data = json.loads(request.text)
        except json.decoder.JSONDecodeError:
            raise ValueError("Not able to find any data for {}".format(category))
    else:
        try:
            json_file = URL + "_Funds.json"
            request = requests.get(json_file)
            json_data = json.loads(request.text)
        except json.decoder.JSONDecodeError:
            raise ValueError("Not able to find any data.")

    return json_data


def select_indices(market=None):
    URL = ("https://raw.githubusercontent.com/JerBouma/FinanceDatabase/master/"
           "Database/Indices/")

    if market:
        try:
            json_file = URL + market + '.json'
            request = requests.get(json_file)
            json_data = json.loads(request.text)
        except json.decoder.JSONDecodeError:
            raise ValueError("Not able to find any data for {}".format(market))
    else:
        try:
            json_file = URL + "_Indices.json"
            request = requests.get(json_file)
            json_data = json.loads(request.text)
        except json.decoder.JSONDecodeError:
            raise ValueError("Not able to find any data.")

    return json_data


def select_other(product):
    URL = ("https://raw.githubusercontent.com/JerBouma/FinanceDatabase/master/"
           "Database/Other/")

    if product not in ['Futures', 'Moneymarkets', 'Options']:
        raise ValueError("{} is not available. Only 'Futures', 'Moneymarkets' and 'Options'.")

    try:
        json_file = URL + product + ".json"
        request = requests.get(json_file)
        json_data = json.loads(request.text)
    except json.decoder.JSONDecodeError:
        raise ValueError("Not able to find any data with type {}.".format(product))

    return json_data
