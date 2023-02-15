# Table of Contents

1. [Installation](#installation)
2. [Basic Usage](#basic-usage)
    1. [Understanding the available options](#understanding-the-available-options) (`fd.select_options`)
    2. [Collecting information from the database](#collecting-information-from-the-database)
        1. [Equities](#equities) (`fd.select_equities`)
        2. [ETFs](#etfs) (`fd.select_etfs`)
        3. [Funds](#funds) (`fd.select_funds`)
        4. [Indices](#indices) (`fd.select_indices`)
        5. [Currencies](#currencies) (`fd.select_currencies`)
        6. [Cryptocurrencies](#cryptocurrencies) (`fd.select_cryptocurrencies`)
        7. [Money Markets](#moneymarkets) (`fd.select_moneymarkets`)
    3. [Storing the database at a different location](#storing-the-database-at-a-different-location)
4. [Contribution](#contribution)

# Installation
The package `financedatabase` allows you to select specific json files as well as search through collected data with a specific query.

You can install the package with the following steps:
1. `pip install financedatabase`
    - Alternatively, download the 'Searcher' directory.
2. (within Python) `import financedatabase as fd`

#  Basic Usage
This section gives a few examples of the possibilities with this package. These are merely a few of the things you
can do with the package. **As you can obtain a wide range of symbols, pretty much any 
package that requires symbols should work.**

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

### Collecting information from the database

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

|        | symbol   | short_name                      | long_name                                | currency   | sector                 | industry                         | exchange   | market    | country       | state   | city        | zipcode    | website                         | market_cap   |
|-------:|:---------|:--------------------------------|:-----------------------------------------|:-----------|:-----------------------|:---------------------------------|:-----------|:----------|:--------------|:--------|:------------|:-----------|:--------------------------------|:-------------|
|  24332 | A        | Agilent Technologies, Inc.      | Agilent Technologies, Inc.               | USD        | Healthcare             | Diagnostics & Research           | NYQ        | us_market | United States | CA      | Santa Clara | 95051      | http://www.agilent.com          | Large Cap    |
|  25583 | AA       | Alcoa Corporation               | Alcoa Corporation                        | USD        | Basic Materials        | Aluminum                         | NYQ        | us_market | United States | PA      | Pittsburgh  | 15212-5858 | http://www.alcoa.com            | Mid Cap      |
|  25624 | AAALF    | AAREAL BANK AG                  | Aareal Bank AG                           | USD        | nan                    | nan                              | PNK        | us_market | Germany       | nan     | Wiesbaden   | 65189      | http://www.aareal-bank.com      | Small Cap    |
|  25626 | AAALY    | AAREAL BANK AG                  | Aareal Bank AG                           | USD        | nan                    | nan                              | PNK        | us_market | nan           | nan     | nan         | nan        | nan                             | nan          |
|  25645 | AABB     | ASIA BROADBAND INC              | Asia Broadband, Inc.                     | USD        | Basic Materials        | Other Industrial Metals & Mining | PNK        | us_market | United States | NV      | Las Vegas   | 89135      | http://www.asiabroadbandinc.com | Micro Cap    |
|      0 | ...      | ...                             | ...                                      | ...        | ...                    | ...                              | ...        | ...       | ...           | ...     | ...         | ...        | ...                             | ...          |
| 155684 | ZYXI     | Zynex, Inc.                     | Zynex, Inc.                              | USD        | Healthcare             | Medical Devices                  | NCM        | us_market | United States | CO      | Englewood   | 80112      | http://www.zynex.com            | Small Cap    |
| 155717 | ZZHGF    | ZHONGAN ONLINE P & C INS CO LTD | ZhongAn Online P & C Insurance Co., Ltd. | USD        | Financial Services     | Insurance - Property & Casualty  | PNK        | us_market | China         | nan     | Shanghai    | nan        | http://www.zhongan.com          | Mid Cap      |
| 155718 | ZZHGY    | ZHONGAN ONLINE P & C INS CO LTD | ZhongAn Online P & C Insurance Co., Ltd. | USD        | nan                    | nan                              | PNK        | us_market | nan           | nan     | nan         | nan        | nan                             | nan          |
| 155719 | ZZLL     | ZZLL INFORMATION TECHNOLOGY INC | ZZLL Information Technology, Inc.        | USD        | Communication Services | Internet Content & Information   | PNK        | us_market | Hong Kong     | nan     | North Point | nan        | http://www.zzlliti.com          | Nano Cap     |
| 155727 | ZZZOF    | ZINC ONE RESOURCES INC          | Zinc One Resources Inc.                  | USD        | Basic Materials        | Other Industrial Metals & Mining | PNK        | us_market | Canada        | BC      | Vancouver   | V6E 4H1    | http://www.zincone.com          | Micro Cap    |

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

|        | symbol   | short_name                  | long_name                            | currency   | sector          | industry   | exchange   | market    | country       | state   | city           | zipcode    | website                       | market_cap   |
|-------:|:---------|:----------------------------|:-------------------------------------|:-----------|:----------------|:-----------|:-----------|:----------|:--------------|:--------|:---------------|:-----------|:------------------------------|:-------------|
|  25583 | AA       | Alcoa Corporation           | Alcoa Corporation                    | USD        | Basic Materials | Aluminum   | NYQ        | us_market | United States | PA      | Pittsburgh     | 15212-5858 | http://www.alcoa.com          | Mid Cap      |
|  48264 | CENX     | Century Aluminum Company    | Century Aluminum Company             | USD        | Basic Materials | Aluminum   | NMS        | us_market | United States | IL      | Chicago        | 60606      | http://centuryaluminum.com    | Small Cap    |
|  83162 | KALU     | Kaiser Aluminum Corporation | Kaiser Aluminum Corporation          | USD        | Basic Materials | Aluminum   | NMS        | us_market | United States | CA      | Foothill Ranch | 92610-2831 | http://www.kaiseraluminum.com | Mid Cap      |
| 102260 | NORNQ    | NORANDA ALUM HLDG CORP      | Noranda Aluminum Holding Corporation | USD        | Basic Materials | Aluminum   | PNK        | us_market | United States | TN      | Franklin       | 37067      | nan                           | Nano Cap     |
| 106568 | ORMTQ    | ORMET CORP                  | Ormet Corporation                    | USD        | Basic Materials | Aluminum   | PNK        | us_market | United States | OH      | Hannibal       | 43931      | nan                           | Nano Cap     |

As you can imagine, looking at such a specific selection only yields a few results but picking the entire sector `Basic Materials` would have returned 403 different companies (which excludes exchanges other than the United States).

### ETFs

If you wish to collect data from all etfs you can use the following:

```python
import financedatabase as fd


all_etfs = fd.select_etfs()
```

This returns approximately 2.500 different ETFs. Note that by default, only the American exchanges are selected. These are symbols like `SPY` (SPDR S&P 500 ETF Trust) and `VTI` (Vanguard Total Stock Market Index Fund ETF) that tend to be recognized by a majority of data providers and therefore is the default. To disable this, you can set the `exclude_exchanges` argument to `False` which then results in approximately 35.000 different symbols. Find a more elaborate explanation with `help(fd.select_etfs)`:

```text
Help on function select_etfs in module financedatabase.json_picker:

select_etfs(category=None, exclude_exchanges=True, base_url='https://raw.githubusercontent.com/JerBouma/FinanceDatabase/master/Database/ETFs', use_local_location=False, all_etfs_json='_ETFs')
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
```

With this information in hand, and having seen the available options within [Understanding the available options](#understanding-the-available-options), we can specify the selection as follows:

```python
import financedatabase as fd

large_value_etfs = fd.select_etfs(category="Large Value")
```

Which returns a total of approximately 80 ETFs in which below is a small snippet of the output:

```text
{'ABEQ': {'category': 'Large Value',
  'currency': 'USD',
  'exchange': 'PCX',
  'family': 'Absolute Investment Advisers',
  'long_name': 'Absolute Core Strategy ETF',
  'market': 'us_market',
  'short_name': 'Absolute Core Strategy ETF',
  'summary': 'The investment seeks positive absolute returns. The fund';s investment sub-adviser (the "Subadviser"), seeks to achieve it's objective by investing primarily in equity securities of U.S. companies that the Subadviser believes are priced at a substantial discount to the Subadviser&#39;s estimate of fair value. The fund may invest in companies of any market capitalization and in any economic sector, including equity securities of foreign companies that trade on U.S. exchanges, either directly or through American Depositary Receipts ("ADRs"). It is non-diversified.',
  'total_assets': null},
 'AFLG': {'category': 'Large Value',
  'currency': 'USD',
  'exchange': 'PCX',
  'family': 'First Trust',
  'long_name': 'First Trust Active Factor Large Cap ETF',
  'market': 'us_market',
  'short_name': 'First Trust Active Factor Large',
  'summary': 'The investment seeks to provide capital appreciation.\n Under normal market conditions, the fund will invest at least 80% of its net assets (including investment borrowings) in U.S.-listed equity securities issued by large capitalization companies. The manager defines large capitalization companies as those that, at the time of investment, have a minimum market capitalization equal to or greater than the minimum market capitalization of a widely recognized index of large capitalization companies based upon the composition of the index at the time of investment. It is non-diversified.',
  'total_assets': null},

<continues>
```

### Funds

If you wish to collect data from all funds you can use the following:

```python
import financedatabase as fd

all_funds = fd.select_funds()
```

This returns approximately 30.000 different Funds. Note that by default, only the American exchanges are selected. These are symbols that tend to be recognized by a majority of data providers and therefore is the default. To disable this, you can set the `exclude_exchanges` argument to `False` which then results in approximately 55.000 different symbols. Find a more elaborate explanation with `help(fd.select_funds)`:

```text
Help on function select_funds in module financedatabase.json_picker:

select_funds(category=None, exclude_exchanges=True, base_url='https://raw.githubusercontent.com/JerBouma/FinanceDatabase/master/Database/Funds', use_local_location=False, all_funds_json='_Funds')
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
```

With this information in hand, and having seen the available options within [Understanding the available options](#understanding-the-available-options), we can specify the selection as follows:

```python
import financedatabase as fd

bear_market_funds = fd.select_funds(category="Bear Market")
```

Which returns a total of 4 funds in which below is a small snippet of the output:

```text
{'BRPIX': {'category': 'Bear Market',
  'currency': 'USD',
  'exchange': 'NAS',
  'family': 'ProFunds',
  'long_name': 'ProFunds Bear Fund Investor Class',
  'manager_bio': 'Michael Neches joined ProShare Advisors in 2000, and presently serves as a Senior Portfolio Manager. He previously served as the Senior Portfolio Manager responsible for the companyâ\x80\x99s commodities desk for two years, as a Portfolio Manager and team lead, as an Associate Portfolio Manager and as a Portfolio Analyst. Mr. Neches earned a Bachelor of Science in Finance from the University of Maryland, College Park and an MBA from Georgetown University.',
  'manager_name': 'Michael  Neches',
  'market': 'us_market',
  'short_name': 'Bear ProFund Investor Class',
  'summary': 'The investment seeks daily investment results, before fees and expenses, that correspond to the inverse (-1x) of the daily performance of the S&P 500Â® Index.\n The fund invests in financial instruments that ProFund Advisors believes, in combination, should produce daily returns consistent with its investment objective. The index is a float-adjusted, market capitalization-weighted index of 500 U.S. operating companies and real estate investment trusts selected through a process that factors in criteria such as liquidity, price, market capitalization and financial viability. The fund is non-diversified.',
  'total_assets': null},

<continues>
```

### Indices

If you wish to collect data from all indices you can use the following:

```python
import financedatabase as fd


all_indices = fd.select_indices()
```

Which returns the following:

```test
{'GBKX': {'short_name': 'KBW Nasdaq Global Bank Index',
  'currency': None,
  'market': 'us_market',
  'exchange': 'NIM',
  'exchange timezone': 'EDT'},
 'GBKXN': {'short_name': 'KBW Nasdaq Global Bank Net Total Return Index',
  'currency': None,
  'market': 'us_market',
  'exchange': 'NIM',
  'exchange timezone': 'EDT'},
 'GBKXT': {'short_name': 'KBW Nasdaq Global Bank Total Return Index',
  'currency': None,
  'market': 'us_market',
  'exchange': 'NIM',
  'exchange timezone': 'EDT'},
 '^A1BSC': {'short_name': 'Dow Jones Americas Basic Materi',
  'currency': 'USD',
  'market': 'us_market',
  'exchange': 'DJI',
  'exchange timezone': 'EDT'}

<continues>
````

This returns approximately 60.000 different indices. Note that by default, only the American exchanges are selected. These are symbols like `^GSPC` (S&P 500) that tend to be recognized by a majority of data providers and therefore is the default. To disable this, you can set the `exclude_exchanges` argument to `False` which then results in approximately 90.000 different symbols. Find a more elaborate explanation with `help(fd.select_indices)`:

```text
Help on function select_indices in module financedatabase.json_picker:

select_indices(market=None, exclude_exchanges=True, base_url='https://raw.githubusercontent.com/JerBouma/FinanceDatabase/master/Database/Indices', use_local_location=False, all_indices_json='_Indices')
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
```

### Currencies

If you wish to collect data from all currencies you can use the following:

```python
import financedatabase as fd

all_currencies = fd.select_currencies()
```

This returns approximately 2.500 different currencies. Find a more elaborate explanation with `help(fd.select_currencies)`:

```text
Help on function select_currencies in module financedatabase.json_picker:

select_currencies(currency=None, base_url='https://raw.githubusercontent.com/JerBouma/FinanceDatabase/master/Database/Currencies', use_local_location=False, all_currencies_json='_Currencies')
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
```

With this information in hand, and having seen the available options within [Understanding the available options](#understanding-the-available-options), we can specify the selection as follows:

```python
import financedatabase as fd

usd_currency = fd.select_currencies(currency="USD")
```

Which returns a total of 135 combination of currencies that include the USD in which below is a small snippet of the output:

```text
{'AEDUSD=X': {'currency': 'USD',
  'exchange': 'CCY',
  'market': 'ccy_market',
  'short_name': 'AED/USD'},
 'AFNUSD=X': {'currency': 'USD',
  'exchange': 'CCY',
  'market': 'ccy_market',
  'short_name': 'AFN/USD'},
 'ALLUSD=X': {'currency': 'USD',
  'exchange': 'CCY',
  'market': 'ccy_market',
  'short_name': 'ALL/USD'},
 'ANGUSD=X': {'currency': 'USD',
  'exchange': 'CCY',
  'market': 'ccy_market',
  'short_name': 'ANG/USD'}

<continues>
```

### Cryptocurrencies

If you wish to collect data from all cryptocurrencies you can use the following:

```python
import financedatabase as fd


all_cryptocurrencies = fd.select_cryptocurrencies()
```

Which returns the following:

```text
{'AAVE-CAD': {'cryptocurrency': 'AAVE',
  'currency': 'CAD',
  'exchange': 'CCC',
  'market': 'ccc_market',
  'short_name': 'Aave CAD',
  'summary': 'Aave (AAVE) is a cryptocurrency and operates on the Ethereum platform. Aave has a current supply of 16,000,000 with 12,488,045.98548802 in circulation. The last known price of Aave is 472.51174201 USD and is down -7.08 over the last 24 hours. It is currently trading on 194 active market(s) with $808,255,779.93 traded over the last 24 hours. More information can be found at https://aave.com/.'},
 'AAVE-CNY': {'cryptocurrency': 'AAVE',
  'currency': 'CNY',
  'exchange': 'CCC',
  'market': 'ccc_market',
  'short_name': 'Aave CNY',
  'summary': 'Aave (AAVE) is a cryptocurrency and operates on the Ethereum platform. Aave has a current supply of 16,000,000 with 12,488,045.98548802 in circulation. The last known price of Aave is 472.51174201 USD and is down -7.08 over the last 24 hours. It is currently trading on 194 active market(s) with $808,255,779.93 traded over the last 24 hours. More information can be found at https://aave.com/.'}

<continues>
````

This returns approximately 3.000 different cryptocurrencies. Find a more elaborate explanation with `help(fd.select_cryptocurrencies)`:

```text
Help on function select_cryptocurrencies in module financedatabase.json_picker:

select_cryptocurrencies(cryptocurrency=None, base_url='https://raw.githubusercontent.com/JerBouma/FinanceDatabase/master/Database/Cryptocurrencies', use_local_location=False, all_cryptocurrencies_json='_Cryptocurrencies')
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
```

With this information in hand, and having seen the available options within [Understanding the available options](#understanding-the-available-options), we can specify the selection as follows:

```python
import financedatabase as fd

eth_cryptocurrency = fd.select_cryptocurrencies(cryptocurrency="ETH")
```

Which returns a total of 5 combination of cryptocurrencies that include the ETH in which below is a small snippet of the output:

```text
{'ETH-BTC': {'cryptocurrency': 'ETH',
  'currency': 'BTC',
  'exchange': 'CCC',
  'market': 'ccc_market',
  'short_name': 'Ethereum BTC',
  'summary': 'Ethereum (ETH) is a cryptocurrency . Users are able to generate ETH through the process of mining. Ethereum has a current supply of 115,748,447.249. The last known price of Ethereum is 3,363.79331068 USD and is down -3.44 over the last 24 hours. It is currently trading on 6358 active market(s) with $56,906,207,070.13 traded over the last 24 hours. More information can be found at https://www.ethereum.org/.'},
 'ETH-CAD': {'cryptocurrency': 'ETH',
  'currency': 'CAD',
  'exchange': 'CCC',
  'market': 'ccc_market',
  'short_name': 'Ethereum CAD',
  'summary': 'Ethereum (ETH) is a cryptocurrency . Users are able to generate ETH through the process of mining. Ethereum has a current supply of 115,809,211.249. The last known price of Ethereum is 3,942.58538843 USD and is up 1.53 over the last 24 hours. It is currently trading on 5438 active market(s) with $50,452,624,669.75 traded over the last 24 hours. More information can be found at https://www.ethereum.org/.'}

<continues>
```

### Moneymarkets

If you wish to collect data from all money markets you can use the following:

```python
import financedatabase as fd

all_moneymarkets = fd.select_moneymarkets()
```

Which returns the following:

```
{'AABXX': {'currency': 'USD',
  'exchange': 'NAS',
  'long_name': None,
  'market': 'us_market',
  'short_name': None},
 'AAFXX': {'currency': 'USD',
  'exchange': 'NAS',
  'long_name': None,
  'market': 'us_market',
  'short_name': 'American Funds U.S. Government '},
 'AALXX': {'currency': 'USD',
  'exchange': 'NAS',
  'long_name': 'Thrivent Mutual Funds - Thrivent Money Market Fund',
  'market': 'us_market',
  'short_name': 'Thrivent Money Market Fund Clas'}

<continues>
```

This returns approximately 3.000 different money markets. Find a more elaborate explanation with `help(fd.select_moneymarkets)`:

```text
Help on function select_moneymarkets in module financedatabase.json_picker:

select_moneymarkets(market=None, exclude_exchanges=True, base_url='https://raw.githubusercontent.com/JerBouma/FinanceDatabase/master/Database/Moneymarkets', use_local_location=False, all_moneymarkets_json='_Moneymarkets')
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
```

### Storing the database at a different location
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
