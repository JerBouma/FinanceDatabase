import json

import requests


def select_cryptocurrencies(
    cryptocurrency=None,
    base_url="https://raw.githubusercontent.com/JerBouma/FinanceDatabase/master/"
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
                request = requests.get(json_file)
                json_data = json.loads(request.text)
            except json.decoder.JSONDecodeError:
                raise ValueError(f"Not able to find any data for {cryptocurrency}.")
    else:
        json_file = f"{base_url}/{all_cryptocurrencies_json}.json"
        if use_local_location:
            with open(json_file) as json_local:
                json_data = json.load(json_local)
        else:
            try:
                request = requests.get(json_file)
                json_data = json.loads(request.text)
            except json.decoder.JSONDecodeError:
                raise ValueError("Not able to find any data.")

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
                request = requests.get(json_file)
                json_data = json.loads(request.text)
            except json.decoder.JSONDecodeError:
                raise ValueError(f"Not able to find any data for {currency}.")
    else:
        json_file = f"{base_url}/{all_currencies_json}.json"
        if use_local_location:
            with open(json_file) as json_local:
                json_data = json.load(json_local)
        else:
            try:
                request = requests.get(json_file)
                json_data = json.loads(request.text)
            except json.decoder.JSONDecodeError:
                raise ValueError("Not able to find any data.")

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
                request = requests.get(json_file)
                json_data = json.loads(request.text)
            except json.decoder.JSONDecodeError:
                raise ValueError(f"Not able to find any data for {category}.")
    else:
        json_file = f"{base_url}/{all_etfs_json}.json"
        if use_local_location:
            with open(json_file) as json_local:
                json_data = json.load(json_local)
        else:
            try:
                request = requests.get(json_file)
                json_data = json.loads(request.text)
            except json.decoder.JSONDecodeError:
                raise ValueError("Not able to find any data.")

    if exclude_exchanges:
        for etf in json_data.copy():
            if "." in etf:
                del json_data[etf]
        if not len(json_data):
            raise ValueError(
                "Because exclude_exchanges is set to True, all available data for "
                f"this combination ({category}) is removed. Set this parameter to False to obtain data."
            )

    return json_data


def select_equities(
    country=None,
    sector=None,
    industry=None,
    exclude_exchanges=True,
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
    if country and sector and industry:
        if use_local_location:
            json_file = f"{base_url}/Countries/{country}/{sector}/{industry}.json"
            with open(json_file) as json_local:
                json_data = json.load(json_local)
        else:
            try:
                country = country.replace("%", "%25").replace(" ", "%20")
                sector = sector.replace("%", "%25").replace(" ", "%20")
                industry = industry.replace("%", "%25").replace(" ", "%20")
                json_file = f"{base_url}/Countries/{country}/{sector}/{industry}.json"
                request = requests.get(json_file)
                json_data = json.loads(request.text)
            except json.decoder.JSONDecodeError:
                raise ValueError(
                    f"Not able to find any data with the combination of Country ({country}), "
                    f"Sector ({sector}) and Industry ({industry})."
                )
    elif country and sector:
        if use_local_location:
            json_file = f"{base_url}/Countries/{country}/{sector}/_{sector}.json"
            with open(json_file) as json_local:
                json_data = json.load(json_local)
        else:
            try:
                country = country.replace("%", "%25").replace(" ", "%20")
                sector = sector.replace("%", "%25").replace(" ", "%20")
                json_file = f"{base_url}/Countries/{country}/{sector}/_{sector}.json"
                request = requests.get(json_file)
                json_data = json.loads(request.text)
            except json.decoder.JSONDecodeError:
                raise ValueError(
                    f"Not able to find any data with the combination of Country ({country}) "
                    f"and Sector ({sector})"
                )
    elif sector and industry:
        if use_local_location:
            json_file = f"{base_url}/Sectors/{sector}/{industry}.json"
            with open(json_file) as json_local:
                json_data = json.load(json_local)
        else:
            try:
                sector = sector.replace("%", "%25").replace(" ", "%20")
                industry = industry.replace("%", "%25").replace(" ", "%20")
                json_file = f"{base_url}/Sectors/{sector}/{industry}.json"
                request = requests.get(json_file)
                json_data = json.loads(request.text)
            except json.decoder.JSONDecodeError:
                raise ValueError(
                    "Not able to find any data with the combination of, "
                    f"Sector ({sector}) and Industry ({industry})."
                )
    elif country and industry:
        if use_local_location:
            json_file = f"{base_url}/Countries/{country}/Industries/{industry}.json"
            with open(json_file) as json_local:
                json_data = json.load(json_local)
        else:
            try:
                country = country.replace("%", "%25").replace(" ", "%20")
                industry = industry.replace("%", "%25").replace(" ", "%20")
                json_file = f"{base_url}/Countries/{country}/Industries/{industry}.json"
                request = requests.get(json_file)
                json_data = json.loads(request.text)
            except json.decoder.JSONDecodeError:
                raise ValueError(
                    "Not able to find any data with the combination of, "
                    f"Country ({country}) and Industry ({industry})."
                )
    elif country:
        if use_local_location:
            json_file = f"{base_url}/Countries/{country}/{country}.json"
            with open(json_file) as json_local:
                json_data = json.load(json_local)
        else:
            try:
                country = country.replace("%", "%25").replace(" ", "%20")
                json_file = f"{base_url}/Countries/{country}/{country}.json"
                request = requests.get(json_file)
                json_data = json.loads(request.text)
            except json.decoder.JSONDecodeError:
                raise ValueError(f"Not able to find any data for {country}.")
    elif sector:
        if use_local_location:
            json_file = f"{base_url}/Sectors/{sector}/_{sector}.json"
            with open(json_file) as json_local:
                json_data = json.load(json_local)
        else:
            try:
                sector = sector.replace("%", "%25").replace(" ", "%20")
                json_file = f"{base_url}/Sectors/{sector}/_{sector}.json"
                request = requests.get(json_file)
                json_data = json.loads(request.text)
            except json.decoder.JSONDecodeError:
                raise ValueError(f"Not able to find any data for {sector}.")
    elif industry:
        if use_local_location:
            json_file = f"{base_url}/Industries/{industry}.json"
            with open(json_file) as json_local:
                json_data = json.load(json_local)
        else:
            try:
                industry = industry.replace("%", "%25").replace(" ", "%20")
                json_file = f"{base_url}/Industries/{industry}.json"
                request = requests.get(json_file)
                json_data = json.loads(request.text)
            except json.decoder.JSONDecodeError:
                raise ValueError(f"Not able to find any data for {industry}.")
    else:
        if use_local_location:
            json_data = {}

            json_file_part_one = f"{base_url}/Equities Part 1.json"
            with open(json_file_part_one) as json_local:
                json_data_part_one = json.load(json_local)
            json_data.update(json_data_part_one)

            json_file_part_two = f"{base_url}/Equities Part 2.json"
            with open(json_file_part_two) as json_local:
                json_data_part_two = json.load(json_local)
            json_data.update(json_data_part_two)
        else:
            try:
                json_data = {}

                json_file_part_one = f"{base_url}/Equities Part 1.json"
                request = requests.get(json_file_part_one)
                json_data_segment = json.loads(request.text)
                json_data.update(json_data_segment)

                json_file_part_two = f"{base_url}/Equities Part 2.json"
                request = requests.get(json_file_part_two)
                json_data_segment = json.loads(request.text)
                json_data.update(json_data_segment)
            except json.decoder.JSONDecodeError:
                raise ValueError("Not able to find any data.")

    if exclude_exchanges:
        for company in json_data.copy():
            if "." in company:
                del json_data[company]
            if not len(json_data):
                raise ValueError(
                    "Because exclude_exchanges is set to True, all available data for "
                    f"this combination ({country}, {sector} and {industry}) is removed. "
                    f"Set this parameter to False to obtain data."
                )

    return json_data


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
                request = requests.get(json_file)
                json_data = json.loads(request.text)
            except json.decoder.JSONDecodeError:
                raise ValueError(f"Not able to find any data for {category}.")
    else:
        json_file = f"{base_url}/{all_funds_json}.json"
        if use_local_location:
            with open(json_file) as json_local:
                json_data = json.load(json_local)
        else:
            try:
                request = requests.get(json_file)
                json_data = json.loads(request.text)
            except json.decoder.JSONDecodeError:
                raise ValueError("Not able to find any data.")

    if exclude_exchanges:
        for fund in json_data.copy():
            if "." in fund:
                del json_data[fund]
            if not len(json_data):
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
                request = requests.get(json_file)
                json_data = json.loads(request.text)
            except json.decoder.JSONDecodeError:
                raise ValueError(f"Not able to find any data for {market}.")
    else:
        json_file = f"{base_url}/{all_indices_json}.json"
        if use_local_location:
            with open(json_file) as json_local:
                json_data = json.load(json_local)
        else:
            try:
                request = requests.get(json_file)
                json_data = json.loads(request.text)
            except json.decoder.JSONDecodeError:
                raise ValueError("Not able to find any data.")

    if exclude_exchanges:
        for index in json_data.copy():
            if "." in index:
                del json_data[index]
            if not len(json_data):
                raise ValueError(
                    "Because exclude_exchanges is set to True, all available data for "
                    f"this combination ({market}) is removed. Set this parameter to False to obtain data."
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
                request = requests.get(json_file)
                json_data = json.loads(request.text)
            except json.decoder.JSONDecodeError:
                raise ValueError(f"Not able to find any data for {market}.")
    else:
        json_file = f"{base_url}/{all_moneymarkets_json}.json"
        if use_local_location:
            with open(json_file) as json_local:
                json_data = json.load(json_local)
        else:
            try:
                request = requests.get(json_file)
                json_data = json.loads(request.text)
            except json.decoder.JSONDecodeError:
                raise ValueError("Not able to find any data.")

    if exclude_exchanges:
        for moneymarket in json_data.copy():
            if "." in moneymarket:
                del json_data[moneymarket]
        if not len(json_data):
            raise ValueError(
                "Because exclude_exchanges is set to True, all available data for "
                f"this combination ({market}) is removed. Set this parameter to False to obtain data."
            )

    return json_data
