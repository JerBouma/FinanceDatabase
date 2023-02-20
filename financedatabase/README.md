# Table of Contents

1. [Installation](#installation)
2. [Basic Usage](#basic-usage)
    1. [Quick Start](#quick-start)
    2. [Understanding the available options](#understanding-the-available-options) (`fd.select_options`)
    3. [Collecting information from the database](#collecting-information-from-the-database)
        1. [Equities](#equities) (`fd.select_equities`)
        2. [ETFs](#etfs) (`fd.select_etfs`)
        3. [Funds](#funds) (`fd.select_funds`)
        4. [Indices](#indices) (`fd.select_indices`)
        5. [Currencies](#currencies) (`fd.select_currencies`)
        6. [Cryptocurrencies](#cryptocurrencies) (`fd.select_cryptocurrencies`)
        7. [Money Markets](#moneymarkets) (`fd.select_moneymarkets`)
    4. [Searching the database extensively](#searching-the-database-extensively)
    5. [Storing the database at a different location](#storing-the-database-at-a-different-location)
4. [Contribution](#contribution)

# Installation
The package `financedatabase` allows you to select specific json files as well as search through collected data with a specific query.

You can install the package with the following steps:
1. `pip install financedatabase`
    - Alternatively, download the 'Searcher' directory.
2. (within Python) `import financedatabase as fd`

#  Basic Usage
This section explains in detail how the database can be queried with the related `financedatabase` package, also see the Jupyter Notebook in which you can run the examples also demonstrated here. You can find this document [here](https://github.com/JerBouma/FinanceDatabase/blob/main/financedatabase/examples.ipynb).

## Quickstart
Same methods apply to all other asset classes as well. Columns may vary.

```python
import financedatabase as fd

# Initialize the Equities database
equities = fd.Equities()

# Obtain all countries from the database
equities_countries = equities.options('country')

# Obtain all sectors from the database
equities_sectors = equities.options('sector')

# Obtain all industries from a country from the database
equities_germany_industries = equities.options('industry', country='Germany')

# Obtain a selection from the database
equities_united_states = equities.select(country="United States")

# Obtain a detailed selection from the database
equities_usa_consumer_electronics = equities.select(country="United States", industry="Consumer Electronics")

# Search specific fields from the database
equities_uk_biotech = equities.search(country='United Kingdom', summary='biotech', exchange='LSE')
```

Scroll down below for a more elaborate explanation and detailed examples.

## Understanding the available options
Understanding which sectors exist in a country can be interesting. Not only to understand the focus of the country but 
also to understand which area holds the most data. This is a demonstration of the ```show_options``` function. 
A function crucial to querying data from the Database.

Let's start by acquiring the unique countries, sectors and industries of all equities in the database:

````python
import financedatabase as fd

# Obtain all countries from the database
equities_countries = fd.show_options('equities', 'countries')

# Obtain all sectors from the database
equities_sectors = fd.show_options('equities', 'sectors')

# Obtain all industries from the database
equities_industries = fd.show_options('equities', 'industries')

# Obtain all countries + sectors + industries from the database
equities_all_categories = fd.show_options('equities')
````

For countries, you will find the following list if you print `equities_countries`:

`Afghanistan, Anguilla, Argentina, Australia, Austria, Azerbaijan, Bahamas, Bangladesh, Barbados, Belgium, Belize, Bermuda, Botswana, Brazil, British Virgin Islands, Cambodia, Canada, Cayman Islands, Chile, China, Colombia, Costa Rica, Cyprus, Czech Republic, Denmark, Dominican Republic, Egypt, Estonia, Falkland Islands, Finland, France, French Guiana, Gabon, Georgia, Germany, Ghana, Gibraltar, Greece, Greenland, Guernsey, Hong Kong, Hungary, Iceland, India, Indonesia, Ireland, Isle of Man, Israel, Italy, Ivory Coast, Japan, Jersey, Jordan, Kazakhstan, Kyrgyzstan, Latvia, Liechtenstein, Lithuania, Luxembourg, Macau, Macedonia, Malaysia, Malta, Mauritius, Mexico, Monaco, Mongolia, Montenegro, Morocco, Mozambique, Myanmar, Namibia, Netherlands, Netherlands Antilles, New Zealand, Nigeria, Norway, Panama, Papua New Guinea, Peru, Philippines, Poland, Portugal, Qatar, Reunion, Romania, Russia, Saudi Arabia, Senegal, Singapore, Slovakia, Slovenia, South Africa, South Korea, Spain, Suriname, Sweden, Switzerland, Taiwan, Tanzania, Thailand, Turkey, Ukraine, United Arab Emirates, United Kingdom, United States, Uruguay, Vietnam, Zambia`

For sectors, you will find the following list if you print `equities_sectors`:

`Basic Materials, Communication Services, Conglomerates, Consumer Cyclical, Consumer Defensive, Consumer Goods, Energy, Financial, Financial Services, Healthcare, Industrial Goods, Industrials, Real Estate, Services, Technology, Utilities`

For industries, you will find the following list if you print `equities_industries`:

`Advertising Agencies, Aerospace & Defense, Aerospace Defense - Major Diversified, Aerospace Defense Products & Services, Agricultural Chemicals, Agricultural Inputs, Air Delivery & Freight Services, Airlines, Airports & Air Services, Aluminum, Apparel Manufacturing, Apparel Retail, Apparel Stores, Asset Management, Auto & Truck Dealerships, Auto Dealerships, Auto Manufacturers, Auto Manufacturers - Major, Auto Parts, Banks - Diversified, Banks - Regional, Beverages - Brewers, Beverages - Non-Alcoholic, Beverages - Soft Drinks, Beverages - Wineries & Distilleries, Beverages - Wineries & Distillers, Biotechnology, Broadcasting, Broadcasting - TV, Building Materials, Building Products & Equipment, Business Equipment, ...`

When you wish to get country, sector or industry specific lists, you can use the related `country`, `sector` and `industry` tags as also find in the help window with `help(fd.show_options)`:

```text
show_options(product, equities_selection=None, country=None, sector=None, industry=None)
    Description
    ----
    Returns all options that exist in the database that you can use to filter the database. In case you
    use country and/or secto
    
    Input
    ----
    product (string)
        Gives all data for a specific product which can be
        cryptocurrencies, currencies, equities, etfs or funds.
    equities_selection (string)
        Gives a sub selection for the possibilities for equities which can be countries, sectors or industries.
    country (string)
        By entering a country here, you are able to obtain all Sectors and Industries within this country. You can
        add in Sector to specify on the Industry level.
    sector (string)
        By entering a sector here, you are able to obtain all industries within this sector. You can
        add in country to specify within a country.
    industry (boolean)
        By setting industry to True, you are able to obtain the sector the industry resides in as well as all
        countries who have companies in this industry.
    
    Output
    ----
    json_data (dictionary)
        Returns a dictionary with a selection based on the input.
```

For example, if I wish to know all available industries within the sector "Basic Materials" in the country United States I can use

```python
 fd.show_options(product="equities", country="United States", sector="Basic Materials")
 ```

 Which returns:

`Agricultural Inputs, Aluminum, Building Materials, Chemicals, Coking Coal, Copper, Gold, Independent Oil & Gas, Industrial Metals & Minerals, Lumber & Wood Production, Nonmetallic Mineral Mining, Oil & Gas Drilling & Exploration, Oil & Gas Equipment & Services, Other Industrial Metals & Mining, Other Precious Metals & Mining, Paper & Paper Products, Silver, Specialty Chemicals, Steel`

This also extends further if you are looking into a different category. For example, find all available currencies by using 

```python
fd.show_options('currencies')
```

Which returns:

`AED, AFN, ALL, AMD, ANG, AOA, ARS, AUD, AWG, AZN, BAM, BBD, BDT, BGN, BHD, BIF, BMD, BND, BOB, BRL, BRX, BSD, BTN, BWP, BYN, BZD, CAD, CAX, CDF, CHF, CLF, CLP, CNH, CNY, COP, CRC, CUC, CUP, CVE, CZK, CZX, DJF, DKK, DKX, DOP, DZD, EGP, ERN, ETB, EUR, FJD, FKP, GBP, GEL, GHS, GIP, GMD, GNF, GTQ, GYD, HKD, HNL, HRK, HRX, HTG, HUF, HUX, IDR, ILS, INR, IQD, IRR, ISK, ISX, JMD, JOD, JPY, KES, KGS, KHR, KMF, KPW, KRW, KWD, KYD, KZT, LAK, LBP, LKR, LRD, LSL, LYD, MAD, MDL, MGA, MKD, MMK, MNT, MOP, MRU, MUR, MVR, MWK, MXN, MXV, MXX, MYR, MYX, MZN, NAD, NGN, NIO, NOK, NPR, NZD, OMR, PAB, PEN, PGK, PHP, PKR, PLN, PLX, PYG, QAR, RON, RSD, RUB, RUX, RWF, SAR, SBD, SCR, SDG, SEK, SGD, SHP, SLL, SOS, SRD, STN, SVC, SYP, SZL, THB, THX, TJS, TMT, TND, TOP, TRY, TTD, TWD, TZS, UAH, UGX, USD, UYU, UZS, VES, VND, VUV, WST, XAF, XCD, XCU, XDR, XOF, XPF, YER, ZAC, ZAR, ZMW`

But also when it comes to `etfs` with 

```python
fd.show_options('etfs')
```

 Which returns:

`Allocation--15% to 30% Equity, Allocation--30% to 50% Equity, Allocation--50% to 70% Equity, Allocation--70% to 85% Equity, Allocation--85%+ Equity, Bank Loan, Bear Market, China Region, Commodities Broad Basket, Communications, Consumer Cyclical, Consumer Defensive, Convertibles, Corporate Bond, Diversified Emerging Mkts, Diversified Pacific/Asia, Emerging Markets Bond, Emerging-Markets Local-Currency Bond, Energy Limited Partnership, Equity Energy, Equity Precious Metals, Europe Stock, Financial, Foreign Large Blend, Foreign Large Growth, Foreign Large Value, ...`

## Collecting information from the database

Each of the asset classes in the database have a specific class as follows:

- [Equities](#equities) (`fd.Equities()`)
- [ETFs](#etfs) (`fd.ETFs()`)
- [Funds](#funds) (`fd.Funds()`)
- [Indices](#indices) (`fd.Indices()`)
- [Currencies](#currencies) (`fd.Currencies()`)
- [Cryptocurrencies](#cryptocurrencies) (`fd.Cryptos()`)
- [Money Markets](#moneymarkets) (`fd.Moneymarkets()`)

### Equities

If you wish to collect data from all equities you can use the following:

```python
import financedatabase as fd

equities = fd.Equities()

equities.select()
```

Which returns the following DataFrame:

| symbol   | short_name                 | long_name                  | currency   | sector          | industry                         | exchange   | market    | country       | state   | city        | zipcode    | website                         | market_cap   |
|:---------|:---------------------------|:---------------------------|:-----------|:----------------|:---------------------------------|:-----------|:----------|:--------------|:--------|:------------|:-----------|:--------------------------------|:-------------|
| A        | Agilent Technologies, Inc. | Agilent Technologies, Inc. | USD        | Healthcare      | Diagnostics & Research           | NYQ        | us_market | United States | CA      | Santa Clara | 95051      | http://www.agilent.com          | Large Cap    |
| AA       | Alcoa Corporation          | Alcoa Corporation          | USD        | Basic Materials | Aluminum                         | NYQ        | us_market | United States | PA      | Pittsburgh  | 15212-5858 | http://www.alcoa.com            | Mid Cap      |
| AAALF    | AAREAL BANK AG             | Aareal Bank AG             | USD        | nan             | nan                              | PNK        | us_market | Germany       | nan     | Wiesbaden   | 65189      | http://www.aareal-bank.com      | Small Cap    |
| AAALY    | AAREAL BANK AG             | Aareal Bank AG             | USD        | nan             | nan                              | PNK        | us_market | nan           | nan     | nan         | nan        | nan                             | nan          |
| AABB     | ASIA BROADBAND INC         | Asia Broadband, Inc.       | USD        | Basic Materials | Other Industrial Metals & Mining | PNK        | us_market | United States | NV      | Las Vegas   | 89135      | http://www.asiabroadbandinc.com | Micro Cap    |

This returns approximately 20.000 different equities. Note that by default, only the American exchanges are selected. These are symbols like `TSLA` (Tesla) and `MSFT` (Microsoft) that tend to be recognized by a majority of data providers and therefore is the default. To disable this, you can set the `exclude_exchanges` argument to `False` which then results in approximately 155.000 different symbols. 

Note that the summary column is taken out on purpose to keep it organized for markdown. The summary is however very handy when it comes to querying specific words as found with the following description given for Microsoft. All of this information is available when you query the database.

```
Microsoft Corporation develops, licenses, and supports software, services, devices, and solutions worldwide. Its Productivity and Business Processes segment offers Office, Exchange, SharePoint, Microsoft Teams, Office 365 Security and Compliance, and Skype for Business, as well as related Client Access Licenses (CAL); Skype, Outlook.com, OneDrive, and LinkedIn; and Dynamics 365, a set of cloud-based and on-premises business solutions for small and medium businesses, large organizations, and divisions of enterprises. Its Intelligent Cloud segment licenses SQL and Windows Servers, Visual Studio, System Center, and related CALs; GitHub that provides a collaboration platform and code hosting service for developers; and Azure, a cloud platform. It also offers support services and Microsoft consulting services to assist customers in developing, deploying, and managing Microsoft server and desktop solutions; and training and certification to developers and IT professionals on various Microsoft products. Its More Personal Computing segment provides Windows original equipment manufacturer (OEM) licensing and other non-volume licensing of the Windows operating system; Windows Commercial, such as volume licensing of the Windows operating system, Windows cloud services, and other Windows commercial offerings; patent licensing; Windows Internet of Things; and MSN advertising. It also offers Surface, PC accessories, PCs, tablets, gaming and entertainment consoles, and other devices; Gaming, including Xbox hardware, and Xbox content and services; video games and third-party video game royalties; and Search, including Bing and Microsoft advertising. It sells its products through OEMs, distributors, and resellers; and directly through digital marketplaces, online stores, and retail stores. It has a strategic collaboration with DXC Technology and Dynatrace, Inc.; and a partnership with WPP plc. The company was founded in 1975 and is headquartered in Redmond, Washington.
```

Find a more elaborate explanation with `help(equities.select)`:

```text
Help on method select in module financedatabase.equities:

select(country: str = '', sector: str = '', industry: str = '', exclude_exchanges: bool = True, capitalize: bool = True) -> pandas.core.frame.DataFrame method of financedatabase.equities.Equities instance
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
        you will receive multiple times the product from different exchanges.
    capitalize (boolean, default is True):
        Whether country, sector and industry needs to be capitalized. By default
        the values always are capitalized as that is also how it is represented
        in the csv files.
    base_url (string, default is GitHub location)
        The possibility to enter your own location if desired.
    use_local_location (string, default False)
        The possibility to select a local location (i.e. based on Windows path)
    
    Output
    ----
    equities_df (pd.DataFrame)
        Returns a dictionary with a selection or all data based on the input.
```

As an example, in [Understanding the available options](#understanding-the-available-options) we've used `equities.options(selection='industry', country="United States", sector="Basic Materials")` which allowed us to look at a specific industry in the United States. So with this information in hand, I can now query the industry `Aluminum` as follows:

```python
import financedatabase as fd

equities = fd.Equities()

aluminium_companies_usa = equities.select(country="United States", sector="Basic Materials", industry="Aluminum")
```

This gives you a DataFrame with the following information:

| symbol   | short_name                  | long_name                            | currency   | sector          | industry   | exchange   | market    | country       | state   | city           | zipcode    | website                       | market_cap   |
|:---------|:----------------------------|:-------------------------------------|:-----------|:----------------|:-----------|:-----------|:----------|:--------------|:--------|:---------------|:-----------|:------------------------------|:-------------|
| AA       | Alcoa Corporation           | Alcoa Corporation                    | USD        | Basic Materials | Aluminum   | NYQ        | us_market | United States | PA      | Pittsburgh     | 15212-5858 | http://www.alcoa.com          | Mid Cap      |
| CENX     | Century Aluminum Company    | Century Aluminum Company             | USD        | Basic Materials | Aluminum   | NMS        | us_market | United States | IL      | Chicago        | 60606      | http://centuryaluminum.com    | Small Cap    |
| KALU     | Kaiser Aluminum Corporation | Kaiser Aluminum Corporation          | USD        | Basic Materials | Aluminum   | NMS        | us_market | United States | CA      | Foothill Ranch | 92610-2831 | http://www.kaiseraluminum.com | Mid Cap      |
| NORNQ    | NORANDA ALUM HLDG CORP      | Noranda Aluminum Holding Corporation | USD        | Basic Materials | Aluminum   | PNK        | us_market | United States | TN      | Franklin       | 37067      | nan                           | Nano Cap     |
| ORMTQ    | ORMET CORP                  | Ormet Corporation                    | USD        | Basic Materials | Aluminum   | PNK        | us_market | United States | OH      | Hannibal       | 43931      | nan                           | Nano Cap     |

As you can imagine, looking at such a specific selection only yields a few results but picking the entire sector `Basic Materials` would have returned 403 different companies (which excludes exchanges other than the United States).

### ETFs

If you wish to collect data from all etfs you can use the following:

```python
import financedatabase as fd

etfs = fd.ETFs()

etfs.select()
```

Which returns the following DataFrame:

| symbol   | short_name                      | long_name                                  | currency   | category                  | family                   | exchange   | market    |   total_assets |
|:---------|:--------------------------------|:-------------------------------------------|:-----------|:--------------------------|:-------------------------|:-----------|:----------|---------------:|
| AAA      | Listed Funds Trust AAF First Pr | AAF First Priority CLO Bond ETF            | USD        | nan                       | Alternative Access Funds | PCX        | us_market |    1.00196e+07 |
| AAAU     | Goldman Sachs Physical Gold ETF | Goldman Sachs Physical Gold ETF            | USD        | nan                       | Exchange Traded Concepts | PCX        | us_market |    3.31796e+08 |
| AADR     | AdvisorShares Dorsey Wright     | AdvisorShares Dorsey Wright ADR ETF        | USD        | nan                       | nan                      | NMS        | us_market |  nan           |
| AAXJ     | iShares MSCI All Country Asia e | iShares MSCI All Country Asia ex Japan ETF | USD        | Pacific/Asia ex-Japan Stk | iShares                  | NMS        | us_market |    6.5889e+09  |
| ABCS     | Guggenheim ABC High Dividend ET | nan                                        | nan        | nan                       | nan                      | PCX        | us_market |  nan           |


This returns approximately 2.500 different ETFs. Note that by default, only the American exchanges are selected. These are symbols like `SPY` (SPDR S&P 500 ETF Trust) and `VTI` (Vanguard Total Stock Market Index Fund ETF) that tend to be recognized by a majority of data providers and therefore is the default. To disable this, you can set the `exclude_exchanges` argument to `False` which then results in approximately 35.000 different symbols. 

Note that the summary column is taken out on purpose to keep it organized for markdown. The summary is however very handy when it comes to querying specific words as found with the following description given for VTI. All of this information is available when you query the database.

```
The investment seeks to track the performance of the CRSP US Total Market Index that measures the investment return of the overall stock market. The fund employs an indexing investment approach designed to track the performance of the index, which represents approximately 100% of the investable U.S. stock market and includes large-, mid-, small-, and micro-cap stocks regularly traded on the New York Stock Exchange and Nasdaq. It invests by sampling the index, meaning that it holds a broadly diversified collection of securities that, in the aggregate, approximates the full index in terms of key characteristics.
```

Find a more elaborate explanation with `help(etfs.select)`:

```text
Help on method select in module financedatabase.etfs:

select(category: str = '', family: str = '', exclude_exchanges: bool = True, capitalize: bool = True) -> pandas.core.frame.DataFrame method of financedatabase.etfs.ETFs instance
    Description
    ----
    Returns all etfs when no input is given and has the option to give
    a specific set of symbols for the category and/or family provided.
    
    The data depends on the combination of inputs. For example Category + Family
    gives all symbols for a specific category for a specific family.
    
    Input
    ----
    category (string, default is None)
        If filled, gives all data for a specific category.
    family (string, default is None)
        If filled, gives all data for a specific family.
    exclude_exchanges (boolean, default is True):
        Whether you want to exclude exchanges from the search. If False,
        you will receive multiple times the product from different exchanges.
    capitalize (boolean, default is True):
        Whether country, sector and industry needs to be capitalized. By default
        the values always are capitalized as that is also how it is represented
        in the csv files.
    base_url (string, default is GitHub location)
        The possibility to enter your own location if desired.
    use_local_location (string, default False)
        The possibility to select a local location (i.e. based on Windows path)
    
    Output
    ----
    etfs_df (pd.DataFrame)
        Returns a dictionary with a selection or all data based on the input.
```

With this information in hand, and having seen the available options within [Understanding the available options](#understanding-the-available-options), we can specify the selection as follows:

```python
import financedatabase as fd

etfs = fd.ETFs()

large_value_etfs = etfs.select(category="Large Value")
```

Which returns a total of approximately 80 ETFs in which below is a small snippet of the output:

| symbol   | short_name                      | long_name                                              | currency   | category    | family                        | exchange   | market    |   total_assets |
|:---------|:--------------------------------|:-------------------------------------------------------|:-----------|:------------|:------------------------------|:-----------|:----------|---------------:|
| ABEQ     | Absolute Core Strategy ETF      | Absolute Core Strategy ETF                             | USD        | Large Value | Absolute Investment Advisers  | PCX        | us_market |    4.79386e+07 |
| AFLG     | First Trust Active Factor Large | First Trust Active Factor Large Cap ETF                | USD        | Large Value | First Trust                   | PCX        | us_market |    7.46305e+06 |
| BUFF     | Innovator Laddered Fund of S&P  | Innovator Laddered Fund of S&P 500 Power Buffer ETFs   | USD        | Large Value | Innovator ETFs                | BTS        | us_market |    4.50859e+07 |
| CAPE     | iPath Shiller CAPE ETN          | Barclays ETN+ Shiller Capet ETN                        | USD        | Large Value | Milleis Investissements Funds | PCX        | us_market |    3.41154e+08 |
| CDL      | VictoryShares US Large Cap High | VictoryShares US Large Cap High Div Volatility Wtd ETF | USD        | Large Value | Victory Capital               | NMS        | us_market |    2.10381e+08 |


### Funds

If you wish to collect data from all funds you can use the following:

```python
import financedatabase as fd

funds = fd.Funds()

funds.select()
```

Which returns the following DataFrame:

| symbol   | short_name                      | long_name                                                        | currency   | manager_name    | category         | family                       | exchange   | market    |    total_assets |
|:---------|:--------------------------------|:-----------------------------------------------------------------|:-----------|:----------------|:-----------------|:-----------------------------|:-----------|:----------|----------------:|
| AAAAX    | DWS RREEF Real Assets Fund - Cl | DWS RREEF Real Assets Fund - Class A                             | USD        | John  Vojticek  | World Allocation | DWS                          | NAS        | us_market |     1.12876e+09 |
| AAACX    | A3 Alternative Credit Fund      | A3 Alternative Credit Fund                                       | USD        | nan             | nan              | nan                          | NAS        | us_market |   nan           |
| AAAEX    | AllianzGI Health Sciences Fund  | Virtus AllianzGI Health Sciences Fund Class P                    | USD        | Peter  Pirsch   | Health           | Virtus                       | NAS        | us_market |     1.87148e+08 |
| AAAFX    | nan                             | American Century One Choice Blend+ 2015 Portfolio Investor Class | USD        | Scott A. Wilson | Target-Date 2015 | American Century Investments | NAS        | us_market | 25562           |
| AAAGX    | Thrivent Large Cap Growth Fund  | Thrivent Large Cap Growth Fund Class A                           | USD        | Lauri  Brunner  | Large Growth     | Thrivent Funds               | NAS        | us_market |     1.98547e+09 |

This returns approximately 30.000 different Funds. Note that by default, only the American exchanges are selected. These are symbols that tend to be recognized by a majority of data providers and therefore is the default. To disable this, you can set the `exclude_exchanges` argument to `False` which then results in approximately 55.000 different symbols.


Note that the summary column is taken out on purpose to keep it organized for markdown. The summary is however very handy when it comes to querying specific words as found with the following description given for AAAGX. All of this information is available when you query the database.

```
The investment seeks long-term capital appreciation.  The fund invests at least 80% of its net assets (plus the amount of any borrowing for investment purposes) in equity securities of large companies. The Adviser focuses mainly on the equity securities of large domestic and international companies which have market capitalizations equivalent to those included in widely known indices such as the Russell 1000 Growth Index, S&P 500 Index, or the large company market capitalization classifications published by Lipper, Inc. These companies typically have a market capitalization of approximately $8 billion or more. The fund is non-diversified.
```

Find a more elaborate explanation with `help(funds.select)`:

```text
Help on method select in module financedatabase.funds:

select(category: str = '', family: str = '', exclude_exchanges: bool = True, capitalize: bool = True) -> pandas.core.frame.DataFrame method of financedatabase.funds.Funds instance
    Description
    ----
    Returns all funds when no input is given and has the option to give
    a specific set of symbols for the category and/or family provided.
    
    The data depends on the combination of inputs. For example Category + Family
    gives all symbols for a specific category for a specific family.
    
    Input
    ----
    category (string, default is None)
        If filled, gives all data for a specific category.
    family (string, default is None)
        If filled, gives all data for a specific family.
    exclude_exchanges (boolean, default is True):
        Whether you want to exclude exchanges from the search. If False,
        you will receive multiple times the product from different exchanges.
    capitalize (boolean, default is True):
        Whether country, sector and industry needs to be capitalized. By default
        the values always are capitalized as that is also how it is represented
        in the csv files.
    base_url (string, default is GitHub location)
        The possibility to enter your own location if desired.
    use_local_location (string, default False)
        The possibility to select a local location (i.e. based on Windows path)
    
    Output
    ----
    funds_df (pd.DataFrame)
        Returns a dictionary with a selection or all data based on the input.
```

With this information in hand, and having seen the available options within [Understanding the available options](#understanding-the-available-options), we can specify the selection as follows:

```python
import financedatabase as fd

funds = fd.Funds()

funds.select(category="Bear Market")
```

Which returns a total of 4 funds:

| symbol   | short_name                      | long_name                                     | currency   | manager_name     | category    | family      | exchange   | market    |   total_assets |
|:---------|:--------------------------------|:----------------------------------------------|:-----------|:-----------------|:------------|:------------|:-----------|:----------|---------------:|
| BRPIX    | Bear ProFund Investor Class     | ProFunds Bear Fund Investor Class             | USD        | Michael  Neches  | Bear Market | ProFunds    | NAS        | us_market |    1.26165e+07 |
| CPCRX    | Comstock Capital Value Fund  Cl | Comstock Capital Value Fund Class I           | USD        | Dennis J. DeCore | Bear Market | Gabelli     | NAS        | us_market |    3.85107e+06 |
| RYARX    | Rydex Series Fds, Inverse S&P 5 | Rydex Inverse S&P 500 Strategy Fund Class A   | USD        | Ryan A. Harder   | Bear Market | Rydex Funds | NAS        | us_market |    6.23792e+07 |
| SOPIX    | Short NASDAQ-100 ProFund Invest | ProFunds Short NASDAQ-100 Fund Investor Class | USD        | Michael  Neches  | Bear Market | ProFunds    | NAS        | us_market |    2.37906e+06 |

### Indices

If you wish to collect data from all indices you can use the following:

```python
import financedatabase as fd

indices = fd.Indices()

indices.select()
```

Which returns the following DataFrame:

|        | short_name                                    | currency   | market    | exchange   | exchange timezone   |
|:-------|:----------------------------------------------|:-----------|:----------|:-----------|:--------------------|
| GBKX   | KBW Nasdaq Global Bank Index                  | nan        | us_market | NIM        | EDT                 |
| GBKXN  | KBW Nasdaq Global Bank Net Total Return Index | nan        | us_market | NIM        | EDT                 |
| GBKXT  | KBW Nasdaq Global Bank Total Return Index     | nan        | us_market | NIM        | EDT                 |
| ^A1BSC | Dow Jones Americas Basic Materi               | USD        | us_market | DJI        | EDT                 |
| ^A1CYC | Dow Jones Americas Consumer Ser               | USD        | us_market | DJI        | EDT                 |

This returns approximately 60.000 different indices. Note that by default, only the American exchanges are selected. These are symbols like `^GSPC` (S&P 500) that tend to be recognized by a majority of data providers and therefore is the default. To disable this, you can set the `exclude_exchanges` argument to `False` which then results in approximately 90.000 different symbols. Find a more elaborate explanation with `help(indices.select)`:

```text
Help on method select in module financedatabase.indices:

select(currency: str = '', capitalize: bool = True, exclude_exchanges: bool = True) -> pandas.core.frame.DataFrame method of financedatabase.indices.Indices instance
    Description
    ----
    Returns all indices when no input is given and has the option to give
    a specific combination of indices based on the currency defined.
    
    Input
    ----
    currency (string, default is None)
        If filled, gives all data for a specific currency.
    capitalize (boolean, default is True):
        Whether the currency needs to be capitalized. By default the values
        always are capitalized as that is also how it is represented in the csv files.
    exclude_exchanges (boolean, default is True):
        Whether you want to exclude exchanges from the search. If False,
        you will receive multiple times the product from different exchanges.
    base_url (string, default is GitHub location)
        The possibility to enter your own location if desired.
    use_local_location (string, default False)
        The possibility to select a local location (i.e. based on Windows path)
    
    Output
    ----
    indices_df (pd.DataFrame)
        Returns a dictionary with a selection or all data based on the input.
```

### Currencies

If you wish to collect data from all currencies you can use the following:

```python
import financedatabase as fd

currencies = fd.Currencies()

currencies.select()
```

Which returns the following DataFrame:

| symbol   | short_name   | currency   | exchange   | market     |
|:---------|:-------------|:-----------|:-----------|:-----------|
| AED=X    | USD/AED      | AED        | CCY        | ccy_market |
| AEDAUD=X | AED/AUD      | AUD        | CCY        | ccy_market |
| AEDBRX=X | AED/BRX      | nan        | CCY        | ccy_market |
| AEDCAD=X | AED/CAD      | CAD        | CCY        | ccy_market |
| AEDCHF=X | AED/CHF      | CHF        | CCY        | ccy_market |

This returns approximately 2.500 different currencies. Find a more elaborate explanation with `help(currencies.select)`:

```text
Help on method select in module financedatabase.currencies:

select(currency: str = '', capitalize: bool = True) -> pandas.core.frame.DataFrame method of financedatabase.currencies.Currencies instance
    Description
    ----
    Returns all currencies when no input is given and has the option to give
    a specific combination of currencies based on the currency defined.
    
    Input
    ----
    currency (string, default is None)
        If filled, gives all data for a specific currency.
    capitalize (boolean, default is True):
        Whether the currency needs to be capitalized. By default the values
        always are capitalized as that is also how it is represented in the csv files.
    base_url (string, default is GitHub location)
        The possibility to enter your own location if desired.
    use_local_location (string, default False)
        The possibility to select a local location (i.e. based on Windows path)
    
    Output
    ----
    currencies_df (pd.DataFrame)
        Returns a dictionary with a selection or all data based on the input.
```

With this information in hand, and having seen the available options within [Understanding the available options](#understanding-the-available-options), we can specify the selection as follows:

```python
import financedatabase as fd

currencies = fd.Currencies()

usd_currency = currencies.select(currency='USD')
```

Which returns a total of 135 combination of currencies that include the USD in which below is a small snippet of the output:

| symbol   | short_name   | currency   | exchange   | market     |
|:---------|:-------------|:-----------|:-----------|:-----------|
| AEDUSD=X | AED/USD      | USD        | CCY        | ccy_market |
| AFNUSD=X | AFN/USD      | USD        | CCY        | ccy_market |
| ALLUSD=X | ALL/USD      | USD        | CCY        | ccy_market |
| ANGUSD=X | ANG/USD      | USD        | CCY        | ccy_market |
| AOAUSD=X | AOA/USD      | USD        | CCY        | ccy_market |

### Cryptocurrencies

If you wish to collect data from all cryptocurrencies you can use the following:

```python
import financedatabase as fd

cryptos = fd.Cryptos()

cryptos.select()
```

Which returns the following:

| symbol   | short_name   | cryptocurrency   | currency   | exchange   | market     |
|:---------|:-------------|:-----------------|:-----------|:-----------|:-----------|
| AAVE-CAD | Aave CAD     | AAVE             | CAD        | CCC        | ccc_market |
| AAVE-CNY | Aave CNY     | AAVE             | CNY        | CCC        | ccc_market |
| AAVE-ETH | Aave ETH     | AAVE             | ETH        | CCC        | ccc_market |
| AAVE-EUR | Aave EUR     | AAVE             | EUR        | CCC        | ccc_market |
| AAVE-GBP | Aave GBP     | AAVE             | GBP        | CCC        | ccc_market |


This returns approximately 3.000 different cryptocurrencies. Note that the summary column is taken out on purpose to keep it organized for markdown. The summary is however very handy when it comes to querying specific words as found with the following description given for Ethereum. All of this information is available when you query the database.

```
Ethereum (ETH) is a cryptocurrency . Users are able to generate ETH through the process of mining. Ethereum has a current supply of 115,789,021.8115. The last known price of Ethereum is 3,564.42544809 USD and is up 2.35 over the last 24 hours. It is currently trading on 5393 active market(s) with $38,633,938,662.39 traded over the last 24 hours. More information can be found at https://www.ethereum.org/.
```

Find a more elaborate explanation with `help(cryptos.select)`:

```text
Help on method select in module financedatabase.cryptos:

select(crypto: str = '', capitalize: bool = True) -> pandas.core.frame.DataFrame method of financedatabase.cryptos.Cryptos instance
    Description
    ----
    Returns all cryptos when no input is given and has the option to give
    a specific combination of cryptos based on the crypto defined.
    
    
    Input
    ----
    crypto (string, default is None)
        If filled, gives all data for a specific crypto.
    capitalize (boolean, default is True):
        Whether the crypto needs to be capitalized. By default the values
        always are capitalized as that is also how it is represented in the csv files.
    base_url (string, default is GitHub location)
        The possibility to enter your own location if desired.
    use_local_location (string, default False)
        The possibility to select a local location (i.e. based on Windows path)
    
    Output
    ----
    cryptos_df (pd.DataFrame)
        Returns a dictionary with a selection or all data based on the input.
```

With this information in hand, and having seen the available options within [Understanding the available options](#understanding-the-available-options), we can specify the selection as follows:

```python
import financedatabase as fd

cryptos = fd.Cryptos()

eth_cryptocurrency = cryptos.select(crypto='ETH')
```

Which returns a total of 5 combination of cryptocurrencies that include the ETH in which below is a small snippet of the output:

| symbol   | short_name   | cryptocurrency   | currency   | exchange   | market     |
|:---------|:-------------|:-----------------|:-----------|:-----------|:-----------|
| ETH-BTC  | Ethereum BTC | ETH              | BTC        | CCC        | ccc_market |
| ETH-CAD  | Ethereum CAD | ETH              | CAD        | CCC        | ccc_market |
| ETH-EUR  | Ethereum EUR | ETH              | EUR        | CCC        | ccc_market |
| ETH-GBP  | Ethereum GBP | ETH              | GBP        | CCC        | ccc_market |
| ETH-USD  | Ethereum USD | ETH              | USD        | CCC        | ccc_market |

### Moneymarkets

If you wish to collect data from all money markets you can use the following:

```python
import financedatabase as fd

moneymarkets = fd.Moneymarkets()

moneymarkets.select()
```

Which returns the following:

|       | short_name                      | long_name                                                | currency   | market    | exchange   |
|:------|:--------------------------------|:---------------------------------------------------------|:-----------|:----------|:-----------|
| AABXX | nan                             | nan                                                      | USD        | us_market | NAS        |
| AAFXX | American Funds U.S. Government  | nan                                                      | USD        | us_market | NAS        |
| AALXX | Thrivent Money Market Fund Clas | Thrivent Mutual Funds - Thrivent Money Market Fund       | USD        | us_market | NAS        |
| AAOXX | American Beacon U.S. Government | American Beacon U.S. Government Money Market Select Fund | USD        | us_market | NAS        |
| AARXX | nan                             | nan                                                      | USD        | us_market | NAS        |

This returns approximately 3.000 different money markets. Find a more elaborate explanation with `help(fd.select_moneymarkets)`:

```text
Help on method select in module financedatabase.moneymarkets:

select(currency: str = '', capitalize: bool = True, exclude_exchanges: bool = True) -> pandas.core.frame.DataFrame method of financedatabase.moneymarkets.Moneymarkets instance
    Description
    ----
    Returns all moneymarkets when no input is given and has the option to give
    a specific combination of moneymarkets based on the currency defined.
    
    Input
    ----
    currency (string, default is None)
        If filled, gives all data for a specific currency.
    capitalize (boolean, default is True):
        Whether the currency needs to be capitalized. By default the values
        always are capitalized as that is also how it is represented in the csv files.
    exclude_exchanges (boolean, default is True):
        Whether you want to exclude exchanges from the search. If False,
        you will receive multiple times the product from different exchanges.
    base_url (string, default is GitHub location)
        The possibility to enter your own location if desired.
    use_local_location (string, default False)
        The possibility to select a local location (i.e. based on Windows path)
    
    Output
    ----
    indices_df (pd.DataFrame)
        Returns a dictionary with a selection or all data based on the input. 
```

## Searching the database in detail
All asset classes have the capability to search each column with `search`, for example `equities.search()`. Through how this functionality is developed you can define multiple columns and search throughoutly. For example:

```
# Collect all Equities Database
equities = fd.Equities()

# Search Multiple Columns
equities.search(summary='automotive', currency='USD', country='Germany')
```

Which returns a selection of the DataFrame that matches all criteria. 

| symbol   | short_name                  | long_name                                   | currency   | sector             | industry                       | exchange   | market    | country   |   state | city                  |   zipcode | website                   | market_cap   |
|:---------|:----------------------------|:--------------------------------------------|:-----------|:-------------------|:-------------------------------|:-----------|:----------|:----------|--------:|:----------------------|----------:|:--------------------------|:-------------|
| AFRMF    | ALPHAFORM AG                | Alphaform AG                                | USD        | Industrials        | Specialty Industrial Machinery | PNK        | us_market | Germany   |     nan | Feldkirchen           |     85622 | nan                       | Nano Cap     |
| AUUMF    | AUMANN AG                   | Aumann AG                                   | USD        | Industrials        | Specialty Industrial Machinery | PNK        | us_market | Germany   |     nan | Beelen                |     48361 | http://www.aumann.com     | Micro Cap    |
| BAMXF    | BAYERISCHE MOTOREN WERKE AG | Bayerische Motoren Werke Aktiengesellschaft | USD        | Consumer Cyclical  | Auto Manufacturers             | PNK        | us_market | Germany   |     nan | Munich                |     80788 | http://www.bmwgroup.com   | Large Cap    |
| BASFY    | BASF SE                     | BASF SE                                     | USD        | Basic Materials    | Chemicals                      | PNK        | us_market | Germany   |     nan | Ludwigshafen am Rhein |     67056 | http://www.basf.com       | Large Cap    |
| BDRFF    | BEIERSDORF AG               | Beiersdorf Aktiengesellschaft               | USD        | Consumer Defensive | Household & Personal Products  | PNK        | us_market | Germany   |     nan | Hamburg               |     20245 | http://www.beiersdorf.com | Large Cap    |

## Storing the database at a different location
If you wish to store the database at a different location (for example your own Fork) you can do so with the variable 
`base_url` which you can find in each of the above 'select' functions. An example would be:
- `select_funds(category='Africa Equity', base_url=<YOUR URL>)`

You can also store the database locally and point to your local location with the variable `base_url` and by setting
`use_local_location` to True. An example would be:
- `select_etfs(category='Bank Loan', base_url='C:/Users/jerbo/FinanceDatabase/Database/ETFs/', use_local_location=True)`

# Contribution
After setting up Git, you can fork and pull the project in. Note that it is bulky given the large collection of files.

1. Fork the Project ([more info](https://docs.github.com/en/get-started/quickstart/fork-a-repo))
    - **Using GitHub Desktop:** [Getting started with GitHub Desktop](https://docs.github.com/en/desktop/installing-and-configuring-github-desktop/getting-started-with-github-desktop) will guide you through setting up Desktop. Once Desktop is set up, you can use it to [fork the repo](https://docs.github.com/en/desktop/contributing-and-collaborating-using-github-desktop/cloning-and-forking-repositories-from-github-desktop)!
    - **Using the command line:** [Fork the repo](https://docs.github.com/en/github/getting-started-with-github/fork-a-repo#fork-an-example-repository) so that you can make your changes without affecting the original project until you're ready to merge them.
2. Pull the Repository Locally ([more info](https://github.com/git-guides/git-pull))
2. Create your own branch (`git checkout -b Contribution`)
3. Add your changes (`git add .`)
4. Commit your Changes (`git commit -m 'Improve the Database'`)
5. Push to your Branch (`git push origin Contribution`)
6. Open a Pull Request

Please read more about how you can contribute to the Database by reading the [Contributing Guidelines](https://github.com/JerBouma/FinanceDatabase/blob/main/CONTRIBUTING.md).
