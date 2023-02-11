<p align="center">
    <img src="https://raw.githubusercontent.com/JerBouma/FinanceDatabase/main/examples/FinanceDatabaseCropped.png" alt="Logo">
</center>
<p align="center">
    <a href="https://www.buymeacoffee.com/jerbouma">
        <img src="https://img.shields.io/badge/Buy%20Me%20A%20Coffee-Donate-brightgreen?logo=buymeacoffee" alt="Logo">
    </a>
    <a href="https://github.com/JerBouma/FinanceDatabase/issues">
        <img src="https://img.shields.io/github/issues/jerbouma/financedatabase" alt="Logo">
    </a>
     <a href="https://github.com/JerBouma/FinanceDatabase/pulls">
        <img src="https://img.shields.io/github/issues-pr/JerBouma/FinanceDatabase?color=yellow" alt="Logo">
    </a>
    <a href="https://pypi.org/project/financedatabase/">
        <img src="https://img.shields.io/pypi/v/FinanceDatabase" alt="Logo">
    </a>
    <a href="https://pypi.org/project/financedatabase/">
        <img src="https://img.shields.io/pypi/dm/FinanceDatabase" alt="Logo">
    </a>
</center>

| :bulb: **Call for Contributors to the FinanceDatabase** :bulb:   |
|:------------------------------------------------------:|
| The **FinanceDatabase** serves the role of providing anyone with any type of financial product categorisation entirely for free. To be able to achieve this, the FinanceDatabase relies on involvement from the community to update, edit and remove tickers over time. This is made easy enough that anyone, even with a lack of coding experience can contribute because of the generation of JSON files that can be manually edited.
**I'd like to invite you to go to the [Contributing Guidelines](https://github.com/JerBouma/FinanceDatabase/blob/main/CONTRIBUTING.md) to understand how you can help. Thank you!** |

As a private investor, the sheer amount of information that can be found on the internet is rather daunting. Trying to 
understand what type of companies or ETFs are available is incredibly challenging with there being millions of
companies and derivatives available on the market. Sure, the most traded companies and ETFs can quickly be found
simply because they are known to the public (for example, Microsoft, Tesla, S&P500 ETF or an All-World ETF). However, 
what else is out there is often unknown.

**This database tries to solve that**. It features 300.000+ symbols containing Equities, ETFs, Funds, Indices, 
Currencies, Cryptocurrencies and Money Markets. It therefore allows you to obtain a broad overview of sectors,
industries, types of investments and much more.

The aim of this database is explicitly _not_ to provide up-to-date fundamentals or stock data as those can be obtained 
with ease (with the help of this database) by using [yfinance](https://github.com/ranaroussi/yfinance) or [FundamentalAnalysis](https://github.com/JerBouma/FundamentalAnalysis). Instead, it gives insights into the products 
that exist in each country, industry and sector and gives the most essential information about each product. With 
this information, you can analyse specific areas of the financial world and/or find a product that is hard to find. 
See for examples on how you can combine this database, and the earlier mentioned packages the section 
[Examples](#Examples).

Some key statistics of the database:

| Product           | Quantity   | Sectors    | Industries    | Countries | Exchanges |
| ----------------- | ---------- | ---------- | ------------- | --------- | --------- |
| Equities          | 155.705    | 16         | 242           | 111       | 82        |
| ETFs              | 36.727     | 364*       | 94*           | 100**     | 52        |
| Funds             | 57.816     | 1678*      | 438*          | 100**     | 34        |

| Product           | Quantity  | Category              |
| ----------------- | --------- | --------------------- |
| Currencies        | 2.590     | 174 Currencies        |
| Cryptocurrencies  | 3.624     | 299 Cryptocurrencies  |
| Indices           | 86.353    | 49 Exchanges          |
| Money Markets     | 1.384     | 2 Exchanges           |

\* These numbers refer to families (iShares, Vanguard) and categories (World Stock, Real Estate) respectively.  
\** This is an estimation. Obtaining the country distribution can only be done by collecting data on the underlying 
or by manual search.

## Table of Contents

1. [Installation](#installation)
2. [Basic Usage](#basic-usage)
    1. [Understanding the available options](#understanding-the-available-options)
    2. [Collecting information from the database](#collecting-information-from-the-database)
    3. [Storing the database at a different location](#storing-the-database-at-a-different-location)
2. [Examples](#examples)
    1. [Companies in the Netherlands](#companies-in-the-netherlands)
    2. [Technical Analysis of Biotech ETFs](#technical-analysis-of-biotech-etfs)
    3. [United States' Airlines](#united-states-airlines)
    4. [Silicon Valley's Market Cap](#silicon-valleys-market-cap)
    5. [Compare Japanese Stock ETFs](#compare-japanese-stock-etfs)
3. [Questions & Answers](#questions--answers)
4. [Contribution](#contribution)


## Installation
The package `financedatabase` allows you to select specific json files as well as search through collected data with a specific query.

You can install the package with the following steps:
1. `pip install financedatabase`
    - Alternatively, download the 'Searcher' directory.
2. (within Python) `import financedatabase as fd`

##  Basic Usage
This section gives a few examples of the possibilities with this package. These are merely a few of the things you
can do with the package. **As you can obtain a wide range of symbols, pretty much any 
package that requires symbols should work.**

### Understanding the available options
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

`Advertising Agencies, Aerospace & Defense, Aerospace Defense - Major Diversified, Aerospace Defense Products & Services, Agricultural Chemicals, Agricultural Inputs, Air Delivery & Freight Services, Airlines, Airports & Air Services, Aluminum, Apparel Manufacturing, Apparel Retail, Apparel Stores, Asset Management, Auto & Truck Dealerships, Auto Dealerships, Auto Manufacturers, Auto Manufacturers - Major, Auto Parts, Banks - Diversified, Banks - Regional, Beverages - Brewers, Beverages - Non-Alcoholic, Beverages - Soft Drinks, Beverages - Wineries & Distilleries, Beverages - Wineries & Distillers, Biotechnology, Broadcasting, Broadcasting - TV, Building Materials, Building Products & Equipment, Business Equipment, Business Equipment & Supplies, Business Services, Business Software & Services, Capital Markets, Chemicals, Chemicals - Major Diversified, Cigarettes, Closed-End Fund - Equity, Coking Coal, Communication Equipment, Computer Based Systems, Computer Hardware, Confectioners, Conglomerates, Consulting Services, Consumer Electronics, Copper, Credit Services, Department Stores, Diagnostics & Research, Discount Stores, Discount, Variety Stores, Diversified Computer Systems, Diversified Electronics, Diversified Investments, Diversified Machinery, Diversified Utilities, Drug Manufacturers - General, Drug Manufacturers - Major, Drug Manufacturers - Other, Drug Manufacturers - Specialty & Generic, Drugs - Generic, Education & Training Services, Electric Utilities, Electrical Equipment & Parts, Electronic Components, Electronic Equipment, Electronic Gaming & Multimedia, Electronics & Computer Distribution, Electronics Wholesale, Engineering & Construction, Entertainment, Entertainment - Diversified, Farm & Construction Machinery, Farm & Heavy Construction Machinery, Farm Products, Financial Conglomerates, Financial Data & Stock Exchanges, Food - Major Diversified, Food Distribution, Food Wholesale, Footwear & Accessories, Furnishings, Fixtures & Appliances, Gambling, Gaming Activities, General Building Materials, General Contractors, Gold, Grocery Stores, Health Care Plans, Health Information Services, Healthcare Information Services, Healthcare Plans, Heavy Construction, Home Furnishings & Fixtures, Home Improvement Retail, Hospitals, Household & Personal Products, Independent Oil & Gas, Industrial Distribution, Industrial Equipment Wholesale, Industrial Metals & Minerals, Information Technology Services, Infrastructure Operations, Insurance - Diversified, Insurance - Life, Insurance - Property & Casualty, Insurance - Reinsurance, Insurance - Specialty, Insurance Brokers, Integrated Freight & Logistics, Internet Content & Information, Internet Information Providers, Internet Retail, Internet Service Providers, Internet Software & Services, Investment Brokerage - National, Jewelry Stores, Leisure, Life Insurance, Lodging, Long Distance Carriers, Lumber & Wood Production, Lumber, Wood Production, Luxury Goods, Machine Tools & Accessories, Major Airlines, Major Integrated Oil & Gas, Marine Shipping, Marketing Services, Medical Appliances & Equipment, Medical Care Facilities, Medical Devices, Medical Distribution, Medical Instruments & Supplies, Medical Laboratories & Research, Metal Fabrication, Money Center Banks, Mortgage Finance, Mortgage Investment, Multimedia & Graphics Software, Networking & Communication Devices, Nonmetallic Mineral Mining, Oil & Gas Drilling, Oil & Gas Drilling & Exploration, Oil & Gas E&P, Oil & Gas Equipment & Services, Oil & Gas Integrated, Oil & Gas Midstream, Oil & Gas Pipelines, Oil & Gas Refining & Marketing, Other Industrial Metals & Mining, Other Precious Metals & Mining, Packaged Foods, Packaging & Containers, Paper & Paper Products, Personal Products, Personal Services, Pharmaceutical Retailers, Pollution & Treatment Controls, Printed Circuit Boards, Processed & Packaged Goods, Property & Casualty Insurance, Property Management, Publishing, Publishing - Newspapers, REIT - Diversified, REIT - Healthcare Facilities, REIT - Hotel & Motel, REIT - Industrial, REIT - Mortgage, REIT - Office, REIT - Residential, REIT - Retail, REIT - Specialty, Railroads, Real Estate - Development, Real Estate - Diversified, Real Estate Development, Real Estate Services, Recreational Goods, Other, Recreational Vehicles, Regional - Mid-Atlantic Banks, Rental & Leasing Services, Research Services, Residential Construction, Resorts & Casinos, Restaurants, Rubber & Plastics, Scientific & Technical Instruments, Security & Protection Services, Security Software & Services, Semiconductor - Broad Line, Semiconductor Equipment & Materials, Semiconductor- Memory Chips, Semiconductors, Shell Companies, Shipping, Silver, Software - Application, Software - Infrastructure, Solar, Specialized Health Services, Specialty Business Services, Specialty Chemicals, Specialty Industrial Machinery, Specialty Retail, Specialty Retail, Other, Staffing & Employment Services, Staffing & Outsourcing Services, Steel, Steel & Iron, Technical & System Software, Telecom Services, Textile - Apparel Clothing, Textile - Apparel Footwear & Accessories, Textile Industrial, Textile Manufacturing, Thermal Coal, Tobacco, Tobacco Products, Other, Tools & Accessories, Travel Services, Trucking, Trucks & Other Vehicles, Uranium, Utilities - Diversified, Utilities - Independent Power Producers, Utilities - Regulated Electric, Utilities - Regulated Gas, Utilities - Regulated Water, Utilities - Renewable, Waste Management, Water Utilities, Wireless Communications`

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

`Allocation--15% to 30% Equity, Allocation--30% to 50% Equity, Allocation--50% to 70% Equity, Allocation--70% to 85% Equity, Allocation--85%+ Equity, Bank Loan, Bear Market, China Region, Commodities Broad Basket, Communications, Consumer Cyclical, Consumer Defensive, Convertibles, Corporate Bond, Diversified Emerging Mkts, Diversified Pacific/Asia, Emerging Markets Bond, Emerging-Markets Local-Currency Bond, Energy Limited Partnership, Equity Energy, Equity Precious Metals, Europe Stock, Financial, Foreign Large Blend, Foreign Large Growth, Foreign Large Value, Foreign Small/Mid Blend, Foreign Small/Mid Growth, Foreign Small/Mid Value, Global Real Estate, Health, High Yield Bond, High Yield Muni, India Equity, Industrials, Inflation-Protected Bond, Infrastructure, Intermediate Government, Intermediate-Term Bond, Japan Stock, Large Blend, Large Growth, Large Value, Latin America Stock, Long Government, Long-Short Credit, Long-Short Equity, Long-Term Bond, Managed Futures, Market Neutral, Mid-Cap Blend, Mid-Cap Growth, Mid-Cap Value, Miscellaneous Region, Miscellaneous Sector, Multialternative, Multicurrency, Multisector Bond, Muni California Long, Muni Minnesota, Muni National Interm, Muni National Long, Muni National Short, Muni New York Intermediate, Natural Resources, Nontraditional Bond, Option Writing, Pacific/Asia ex-Japan Stk, Preferred Stock, Real Estate, Short Government, Short-Term Bond, Single Currency, Small Blend, Small Growth, Small Value, Tactical Allocation, Technology, Trading--Inverse Commodities, Trading--Inverse Debt, Trading--Inverse Equity, Trading--Leveraged Commodities, Trading--Leveraged Debt, Trading--Leveraged Equity, Trading--Miscellaneous, Ultrashort Bond, Utilities, Volatility, World Allocation, World Bond, World Stock`

### Collecting information from the database

Once you have figured out how to make use of the `fd.show_options` function, you can query the database for relevant data. Each of the asset classes in the database have a specific `select_` function. This includes the following `select_` options:

- [Equities](#equities) (`fd.select_equities`)
- [ETFs](#etfs) (`fd.select_etfs`)
- [Funds](#funds) (`fd.select_funds`)
- [Indices](#indices) (`fd.select_indices`)
- [Currencies](#currencies) (`fd.select_currencies`)
- [Cryptocurrencies](#cryptocurrencies) (`fd.select_cryptocurrencies`)
- [Money Markets](#moneymarkets) (`fd.select_moneymarkets`)

#### Equities

If you wish to collect data from all equities you can use the following:

```python
import financedatabase as fd

all_equities = fd.select_equities()
```

This returns 20.063 different equities. Note that by default, only the American exchanges are selected. These are symbols like `TSLA` (Tesla) and `MSFT` (Microsoft) that tend to be recognized by a majority of data providers and therefore is the default. To disable this, you can set the `exclude_exchanges` argument to `False` which then results in 155.728 different symbols. Find a more elaborate explanation with `help(fd.select_equities)`:

```text
Help on function select_equities in module financedatabase.json_picker:

select_equities(country=None, sector=None, industry=None, exclude_exchanges=True, base_url='https://raw.githubusercontent.com/JerBouma/FinanceDatabase/main/Database/Equities', use_local_location=False)
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
```


As an example, in [Understanding the available options](#understanding-the-available-options) we've used `fd.show_options(product="equities", country="United States", sector="Basic Materials")` which allowed us to look at a specific industry in the United States. So with this information in hand, I can now query the industry `Aluminum` as follows:

```python
import financedatabase as fd

aluminium_companies_usa = fd.select_equities(country="United States", sector="Basic Materials", industry="Aluminum")
```

This gives you a dictionary with the following information:

```text
{'AA': {'city': 'Pittsburgh',
  'country': 'United States',
  'currency': 'USD',
  'exchange': 'NYQ',
  'industry': 'Aluminum',
  'long_name': 'Alcoa Corporation',
  'market': 'us_market',
  'market_cap': 'Mid Cap',
  'sector': 'Basic Materials',
  'short_name': 'Alcoa Corporation',
  'state': 'PA',
  'summary': 'Alcoa Corporation, together with its subsidiaries, produces and sells bauxite, alumina, and aluminum products in the United States, Spain, Australia, Brazil, Canada, and internationally. The company operates through three segments: Bauxite, Alumina, and Aluminum. It engages in bauxite mining operations; and processes bauxite into alumina and sells it to customers who process it into industrial chemical products, as well as aluminum smelting, casting, and rolling businesses. The company offers primary aluminum in the form of alloy ingot or value-add ingot to customers that produce products for the transportation, building and construction, packaging, wire, and other industrial markets; and flat-rolled aluminum sheets to customers that produce beverage and food cans. In addition, it owns hydro power plants that produce and sell electricity to the wholesale market to traders, large industrial consumers, distribution companies, and other generation companies. The company was formerly known as Alcoa Upstream Corporation and changed its name to Alcoa Corporation in October 2016. The company was founded in 1888 and is headquartered in Pittsburgh, Pennsylvania.',
  'website': 'http://www.alcoa.com',
  'zipcode': '15212-5858'},
 'CENX': {'city': 'Chicago',
  'country': 'United States',
  'currency': 'USD',
  'exchange': 'NMS',
  'industry': 'Aluminum',
  'long_name': 'Century Aluminum Company',
  'market': 'us_market',
  'market_cap': 'Small Cap',
  'sector': 'Basic Materials',
  'short_name': 'Century Aluminum Company',
  'state': 'IL',
  'summary': 'Century Aluminum Company, together with its subsidiaries, produces standard-grade and value-added primary aluminum products in the United States and Iceland. The company was incorporated in 1981 and is headquartered in Chicago, Illinois.',
  'website': 'http://centuryaluminum.com',
  'zipcode': '60606'},
 'KALU': {'city': 'Foothill Ranch',
  'country': 'United States',
  'currency': 'USD',
  'exchange': 'NMS',
  'industry': 'Aluminum',
  'long_name': 'Kaiser Aluminum Corporation',
  'market': 'us_market',
  'market_cap': 'Mid Cap',
  'sector': 'Basic Materials',
  'short_name': 'Kaiser Aluminum Corporation',
  'state': 'CA',
  'summary': "Kaiser Aluminum Corporation manufactures and sells semi-fabricated specialty aluminum mill products. The company provides rolled, extruded, and drawn aluminum products used principally for aerospace and defense, automotive, consumer durables, electronics, electrical, and machinery and equipment applications. Its aerospace and high strength products include heat treat plates and sheets, hard alloy extruded shapes, cold finish rods and bars, seamless drawn tubes, and billets for aerospace and defense industries. The company's automotive extrusions include extruded aluminum products for structural components, crash management systems, anti-lock braking systems, and drawn tubes for drive shafts, as well as offers fabrication services, including sawing and cutting to length. Its general engineering products comprise alloy plate, sheet, rod, bar, tube, wire, and standard extrusion shapes used in various applications, including the production of military vehicles, ordnances, semiconductor manufacturing cells, electronic devices, after-market motor sport parts, tooling plates, parts for machinery and equipment, bolts, screws, nails, and rivets. The company also offers extruded, drawn, and cast billet aluminum products for industrial end uses. It sells its products directly to customers through sales personnel located in the United States, Canada, Western Europe, and China, as well as through independent sales agents in other regions of Asia, Latin America, and the Middle East. Kaiser Aluminum Corporation was founded in 1946 and is based in Foothill Ranch, California.",
  'website': 'http://www.kaiseraluminum.com',
  'zipcode': '92610-2831'},
 'NORNQ': {'city': 'Franklin',
  'country': 'United States',
  'currency': 'USD',
  'exchange': 'PNK',
  'industry': 'Aluminum',
  'long_name': 'Noranda Aluminum Holding Corporation',
  'market': 'us_market',
  'market_cap': 'Nano Cap',
  'sector': 'Basic Materials',
  'short_name': 'NORANDA ALUM HLDG CORP',
  'state': 'TN',
  'summary': "Noranda Aluminum Holding Corporation produces and sells primary aluminum, alumina, bauxite, and rolled aluminum coils in the United States. The company's Bauxite segment mines, produces, and sells bauxite used for alumina production. Its Alumina segment refines and converts bauxite into alumina, which is used in the production of primary aluminum; and sells smelter grade alumina and alumina hydrate, or chemical-grade alumina. The company's Primary Aluminum segment produces and sells aluminum products in various forms, such as billets, rods, sow and foundry, and commodity grade sow. Its Flat-Rolled Products segment primarily produces rolled aluminum products, including finstock for use in commercial, residential, and automotive applications; container stock for pre-packaged foods; converter foils for food, drink, agricultural, and industrial products; and transformer windings used as conducting medium. The company sells its products to original equipment manufacturers of air conditioners, transformers, semi-rigid containers, and foil packaging. The company was founded in 2007 and is headquartered in Franklin, Tennessee.",
  'website': None,
  'zipcode': '37067'},
 'ORMTQ': {'city': 'Hannibal',
  'country': 'United States',
  'currency': 'USD',
  'exchange': 'PNK',
  'industry': 'Aluminum',
  'long_name': 'Ormet Corporation',
  'market': 'us_market',
  'market_cap': 'Nano Cap',
  'sector': 'Basic Materials',
  'short_name': 'ORMET CORP',
  'state': 'OH',
  'summary': 'Ormet Corporation engages in the production and sale of primary aluminum and related products in the United States. It offers aluminum/sows and alumina primarily to commodity traders. The company was founded in 1956 and is headquartered in Hannibal, Ohio.',
  'website': None,
  'zipcode': '43931'}}
  ```

As you can imagine, looking at such a specific selection only yields a few results but picking the entire sector `Basic Materials` would have returned 403 different companies (which excludes exchanges other than the United States).

#### ETFs

If you wish to collect data from all etfs you can use the following:

```python
import financedatabase as fd


all_etfs = fd.select_etfs()
```

This returns 2841 different ETFs. Note that by default, only the American exchanges are selected. These are symbols like `SPY` (SPDR S&P 500 ETF Trust) and `VTI` (Vanguard Total Stock Market Index Fund ETF) that tend to be recognized by a majority of data providers and therefore is the default. To disable this, you can set the `exclude_exchanges` argument to `False` which then results in  36.734 different symbols. Find a more elaborate explanation with `help(fd.select_etfs)`:

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

Which returns a total of 80 ETFs in which below is a small snippet of the output:

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

#### Funds

If you wish to collect data from all funds you can use the following:

```python
import financedatabase as fd

all_funds = fd.select_funds()
```

This returns 31.440 different Funds. Note that by default, only the American exchanges are selected. These are symbols that tend to be recognized by a majority of data providers and therefore is the default. To disable this, you can set the `exclude_exchanges` argument to `False` which then results in 57.885 different symbols. Find a more elaborate explanation with `help(fd.select_funds)`:

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

#### Indices

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

This returns 62.140 different indices. Note that by default, only the American exchanges are selected. These are symbols like `^GSPC` (S&P 500) that tend to be recognized by a majority of data providers and therefore is the default. To disable this, you can set the `exclude_exchanges` argument to `False` which then results in 91.183 different symbols. Find a more elaborate explanation with `help(fd.select_indices)`:

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

#### Currencies

If you wish to collect data from all currencies you can use the following:

```python
import financedatabase as fd

all_currencies = fd.select_currencies()
```

This returns 2.590 different currencies. Find a more elaborate explanation with `help(fd.select_currencies)`:

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

#### Cryptocurrencies

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

This returns 3.367 different cryptocurrencies. Find a more elaborate explanation with `help(fd.select_cryptocurrencies)`:

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

#### Moneymarkets

If you wish to collect data from all money markets you can use the following:

```python
import financedatabase as fd

all_moneymarkets = fd.select_moneymarkets()
```

This returns 3.367 different money markets. Find a more elaborate explanation with `help(fd.select_moneymarkets)`:

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

## Examples
This section gives a few examples of the possibilities with this package. These are merely a few of the things you
can do with the package. **As you can obtain a wide range of symbols, pretty much any 
package that requires symbols should work.**

### Companies in the Netherlands
I want to see how many companies exist in each sector in the Netherlands. Let's count all companies with the 
following code, I skip a sector when it has no data and also do not include companies that are not categorized:

````python
equities_per_sector_netherlands = {}

for sector in equities_sectors[1:]:
    try:
        equities_per_sector_netherlands[sector] = len(fd.select_equities(country='Netherlands', sector=sector))
    except ValueError as error:
        print(error)
````

Lastly, I plot the data in a pie chart and add some formatting to make the pie chart look a bit nicer:

````python
legend, values = zip(*equities_per_sector_netherlands.items())

colors = ['b', 'g', 'r', 'c', 'm', 'y', 'k', 'tab:blue', 'tab:orange', 'tab:gray',
          'lightcoral', 'yellow', 'saddlebrown', 'lightblue', 'olive']
plt.pie(values, labels=legend, colors=colors,
        wedgeprops={'linewidth': 0.5, 'edgecolor': 'white'})
plt.title('Companies per sector in the Netherlands')
plt.tight_layout()

plt.show()
````

This results in the following graph which gives an indication which sectors are dominant within The Netherlands. 
Of course this is a mere example and to truly understand the importance of certain companies for the Netherlands, 
an in-depth analysis must be done.

![FinanceDatabase](https://raw.githubusercontent.com/JerBouma/FinanceDatabase/main/examples/CompaniesPerSectorInTheNetherlands.png)

### Technical Analysis of Biotech ETFs
With the help of [ta](https://github.com/bukosabino/ta) and [yfinance](https://github.com/ranaroussi/yfinance) I can 
quickly perform a basic technical analysis on a group of ETFs categorized by the FinanceDatabase. I start by 
searching the database for ETFs related to Health and then make a subselection by searching, in the collected database, 
for biotech-related ETFs:

````python
import financedatabase as fd

health_etfs = fd.select_etfs(category='Health')
health_etfs_in_biotech = fd.search_products(health_etfs, 'biotech')
````

Then, I collect stock data on each ticker and remove tickers that have no data in my chosen period. The period I have 
chosen shows the initial impact of the Coronacrisis on the financial markets.

````python
import yfinance as yf

stock_data_biotech = yf.download(list(health_etfs_in_biotech.keys()), start="2020-01-01", end="2020-06-01")['Adj Close']
stock_data_biotech = stock_data_biotech.dropna(axis='columns')
````

Next up I initialise subplots and loop over all collected tickers. Here, I create a new temporary DataFrame that I fill 
with the adjusted close prices of the ticker as well as the Bollinger Bands. Then I plot the data in one of 
the subplots.

````python
import pandas as pd
from ta.volatility import BollingerBands
import matplotlib.pyplot as plt

figure, axis = plt.subplots(4, 3)
row = 0
column = 0

for ticker in stock_data_biotech.columns:
    data_plot = pd.DataFrame(stock_data_biotech[ticker])

    indicator_bb = BollingerBands(close=stock_data_biotech[ticker], window=20, window_dev=2)

    data_plot['bb_bbm'] = indicator_bb.bollinger_mavg()
    data_plot['bb_bbh'] = indicator_bb.bollinger_hband()
    data_plot['bb_bbl'] = indicator_bb.bollinger_lband()

    axis[row, column].plot(data_plot)
    axis[row, column].set_title(health_etfs_in_biotech[ticker]['long_name'], fontsize=6)
    axis[row, column].set_xticks([])
    axis[row, column].set_yticks([])

    column += 1
    if column == 3:
        row += 1
        column = 0
        
figure.suptitle('Technical Analysis of Biotech ETFs during Coronacrisis')
figure.tight_layout()
````

This leads to the following graph which gives an indication whether Biotech ETFs were oversold or overbought and 
how this effect is neutralised (to some degree) in the months after. Read more 
about [Bollinger Bands](https://www.investopedia.com/terms/b/bollingerbands.asp) here.

![FinanceDatabase](https://raw.githubusercontent.com/JerBouma/FinanceDatabase/main/examples/Technical_Analysis_Biotech_Companies_Coronacrisis.png)

### United States' Airlines
If I wish to obtain all companies within the United States listed under 'Airlines' I can write the 
following code:

````python
import financedatabase as fd

airlines_us = fd.select_equities(country='United States', industry='Airlines')
````

Then, I can use packages like [yfinance](https://github.com/ranaroussi/yfinance) to quickly collect data from 
Yahoo Finance for each symbol in the industry like this:

````python
from yfinance.utils import get_json
from yfinance import download

airlines_us_fundamentals = {}
for symbol in airlines_us:
    airlines_us_fundamentals[symbol] = get_json("https://finance.yahoo.com/quote/" + symbol)

airlines_us_stock_data = download(list(airlines_us))
````

With a few lines of code, I have collected all data from a specific industry within the United States. From here on 
you can compare pretty much any key statistic, fundamental- and stock data. For example, let's plot a simple bar 
chart that gives insights in the Quick Ratios (indicator of the overall financial strength or weakness of a company):

````python
import matplotlib.pyplot as plt

for symbol in airlines_us_fundamentals:
    quick_ratio = airlines_us_fundamentals[symbol]['financialData']['quickRatio']
    long_name = airlines_us_fundamentals[symbol]['quoteType']['longName']

    if quick_ratio is None:
        continue

    plt.barh(long_name, quick_ratio)

plt.tight_layout()
plt.show()
``````

Which results in the graph displayed below (as of the 18th of October 2021). From this graph you can identify 
companies that currently lack enough assets to cover their liabilities (quick ratio < 1), and those that do have 
enough assets (quick ratio > 1). Both too low and too high could make you wonder whether the company adequately 
manages its assets.

![FinanceDatabase](https://raw.githubusercontent.com/JerBouma/FinanceDatabase/main/examples/United_States_Airlines_QuickRatio.png)

### Silicon Valley's Market Cap
If I want to understand which listed technology companies exist in Silicon Valley, I can collect all equities of 
the sector 'Technology' and then filter based on city to obtain all listed technology companies in 'Silicon Valley'. 
The city 'San Jose' is where Silicon Valley is located.

````python
import financedatabase as fd

all_technology_companies = fd.select_equities(sector='Technology')
silicon_valley = fd.search_products(all_technology_companies, query='San Jose', search='city')
````
Then I start collecting data with the [FundamentalAnalysis](https://github.com/JerBouma/FundamentalAnalysis) package. 
Here I collect the key metrics which include 57 different metrics (ranging from PE ratios to Market Cap).

````python
import FundamentalAnalysis as fa

API_KEY = "YOUR API KEY HERE"
data_set = {}
for ticker in silicon_valley:
    try:
        data_set[ticker] = fa.key_metrics(ticker, API_KEY, period='annual')
    except Exception:
        continue
````

Then I make a selection based on the last 5 years and filter by market cap to compare the companies in terms of size
with each other. This also causes companies that have not been listed for 5 years to be filtered out of my dataset.
Lastly, I plot the data.

````python
import pandas as pd
import matplotlib.pyplot as plt

years = ['2016', '2017', '2018', '2019', '2020']
market_cap = pd.DataFrame(index=years)
for ticker in data_set:
    try:
        data_years = []
        for year in years:
            data_years.append(data_set[ticker].loc['marketCap'][year])
        market_cap[all_technology_companies[ticker]['short_name']] = data_years
    except Exception:
        continue

market_cap_plot = market_cap.plot.bar(stacked=True, rot=0, colormap='Spectral')
market_cap_plot.legend(prop={'size': 5.25})
plt.show()
````

This results in the graph displayed below which separates the small companies from the large companies. Note that 
this does not include _all_ technology companies in Silicon Valley because most are not listed or are not included 
in the database of the FundamentalAnalysis package.

![FinanceDatabase](https://raw.githubusercontent.com/JerBouma/FinanceDatabase/main/examples/Silicon_Valley_Technology_MarketCap.png)

### Compare Japanese Stock ETFs
Sometimes, Excel simply offers the best solution if you want compare a range of ETFs quickly. Therefore, another 
option is to use my program [ThePassiveInvestor](https://github.com/JerBouma/ThePassiveInvestor). The goal of 
this package is to quickly compare a large selection of ETFs by collecting their most important attributes 
(i.e. holdings, return, volatility, tracking error).

For example, let's obtain ETFs that track the Japanese Stock Market:

````python
import financedatabase as fd

# Obtain Japanese Stock ETFs (found via fd.show_options("etfs"))
japanese_stock = fd.select_etfs("Japan Stock")

# Convert tickers to a list
japanese_stock_tickers = list(japanese_stock.keys())
````

Then I create the Excel report

````python
import thepassiveinvestor as pi

pi.create_ETF_report(japanese_stock_tickers, "Japanese Stock ETFs.xlsx")
````

When you run this function it starts collecting data on each ticker and fills the Excel with data. After the function 
is finished you are able to find an Excel that looks to the GIF you see below. With this data you can 
get an indication whether the ETF is what you are looking for.

![ThePassiveInvestor](https://raw.githubusercontent.com/JerBouma/FinanceDatabase/main/examples/ThePassiveInvestor_GIF.gif)

Alternatively, you can also use the comparison method from `pi.collect_data` as follows:

````python
import financedatabase as fd
import thepassiveinvestor as pi

# Obtain Japanese Stock ETFs (found via fd.show_options("etfs"))
japanese_stock = fd.select_etfs("Japan Stock")

# Convert tickers to a list
japanese_stock_tickers = list(japanese_stock.keys())

# Create a comparison DataFrame
comparison = pi.collect_data(japanese_stock_tickers, comparison=True)
````

Which returns the following:

|                                               | BBJP        | DBJP        | EWJ         | EWJV        | GSJY        | JPXN        | SCJ         |
|:----------------------------------------------|:------------|:------------|:------------|:------------|:------------|:------------|:------------|
| ('sector_holdings', 'realestate')             | 3.88%       | 3.11%       | 3.37%       | 5.04%       | 2.39%       | 2.52%       | 10.52%      |
| ('sector_holdings', 'consumer_cyclical')      | 15.79%      | 13.65%      | 14.81%      | 18.81%      | 14.7%       | 10.8%       | 17.44%      |
| ('sector_holdings', 'basic_materials')        | 4.73%       | 4.1%        | 4.43%       | 4.1%        | 3.18%       | 5.38%       | 8.69%       |
| ('sector_holdings', 'consumer_defensive')     | 6.53%       | 6.09%       | 6.56%       | 3.62%       | 7.63%       | 8.23%       | 7.93%       |
| ('sector_holdings', 'technology')             | 14.7%       | 14.76%      | 15.9%       | 4.5%        | 14.84%      | 14.07%      | 9.69%       |
| ('sector_holdings', 'communication_services') | 7.47%       | 7.66%       | 8.26%       | 8.66%       | 8.76%       | 8.53%       | 2.69%       |
| ('sector_holdings', 'financial_services')     | 11.85%      | 11.19%      | 12.17%      | 20.44%      | 12.92%      | 11.96%      | 6.97%       |
| ('sector_holdings', 'utilities')              | 1.17%       | 1.02%       | 1.02%       | 1.85%       | 1.57%       | 1.3%        | 2.23%       |
| ('sector_holdings', 'industrials')            | 23.02%      | 20.72%      | 22.32%      | 25.99%      | 22.8%       | 23.89%      | 24.94%      |
| ('sector_holdings', 'energy')                 | 0.79%       | 0.79%       | 0.84%       | 1.61%       | 1.43%       | 1.02%       | 0.54%       |
| ('sector_holdings', 'healthcare')             | 10.1%       | 9.18%       | 9.92%       | 4.81%       | 10.63%      | 12.01%      | 8.06%       |
| ('annual_returns', '2022')                    | -16.79%     | -2.53%      | -17.36%     | -5.68%      | -15.6%      | -16.04%     | -12.7%      |
| ('annual_returns', '2021')                    | 1.39%       | 12.89%      | 1.56%       | 6.16%       | 0.6%        | 0.4%        | -2.4%       |
| ('annual_returns', '2020')                    | 15.05%      | 9.49%       | 14.03%      | 0.89%       | 12.56%      | 13.78%      | 6.28%       |
| ('annual_returns', '2019')                    | 18.62%      | 20.78%      | 19.19%      | N/A         | 18.28%      | 19.36%      | 19.04%      |
| ('annual_returns', '2018')                    | N/A         | -14.03%     | -13.17%     | nan         | -10.52%     | -13.94%     | -16.36%     |
| ('key_characteristics', 'fundInceptionDate')  | 2018-06-15  | 2011-06-09  | 1996-03-12  | 2019-03-05  | 2016-03-02  | 2001-10-23  | 2007-12-20  |
| ('key_characteristics', 'category')           | Japan Stock | Japan Stock | Japan Stock | Japan Stock | Japan Stock | Japan Stock | Japan Stock |
| ('key_characteristics', 'totalAssets')        | 6722127360  | 229223424   | 9353692160  | 83362744    | 12140200    | 52644332    | 65078772    |
| ('key_characteristics', 'currency')           | USD         | USD         | USD         | USD         | USD         | USD         | USD         |
| ('key_characteristics', 'navPrice')           | 46.83       | 49.34       | 56.87       | 25.39       | 31.51       | 60.73       | 66.02       |
| ('key_characteristics', 'previousClose')      | 47.21       | 49.5855     | 57.31       | 25.4712     | 31.45       | 61.14       | 65.98       |
| ('risk_data_3y', 'year')                      | 3y          | 3y          | 3y          | 3y          | 3y          | 3y          | 3y          |
| ('risk_data_3y', 'alpha')                     | -1.2        | 5.92        | -1.64       | 0.18        | -1.74       | -1.54       | -3.46       |
| ('risk_data_3y', 'beta')                      | 0.78        | 0.6         | 0.8         | 0.76        | 0.76        | 0.8         | 0.67        |
| ('risk_data_3y', 'meanAnnualReturn')          | 0.04        | 0.62        | 0.01        | 0.16        | -0.01       | 0.02        | -0.16       |
| ('risk_data_3y', 'rSquared')                  | 75.22       | 54.25       | 76.73       | 69.7        | 73.88       | 74.18       | 58.87       |
| ('risk_data_3y', 'stdDev')                    | 17.63       | 15.75       | 17.95       | 17.66       | 17.18       | 18.06       | 17.11       |
| ('risk_data_3y', 'sharpeRatio')               | 0.28        | 0.18        | 0.51        | 0.24        | 0.3         | 0.58        | 0.14        |
| ('risk_data_3y', 'treynorRatio')              | -2.35       | 9.32        | -2.86       | -0.68       | -3.11       | -2.8        | -6.11       |
| ('risk_data_5y', 'year')                      | 5y          | 5y          | 5y          | 5y          | 5y          | 5y          | 5y          |
| ('risk_data_5y', 'alpha')                     | 0           | 3.62        | -1.13       | 0           | -0.76       | -1.22       | -2.94       |
| ('risk_data_5y', 'beta')                      | 0           | 0.68        | 0.81        | 0           | 0.75        | 0.8         | 0.7         |
| ('risk_data_5y', 'meanAnnualReturn')          | 0           | 0.47        | 0.09        | 0           | 0.11        | 0.08        | -0.08       |
| ('risk_data_5y', 'rSquared')                  | 0           | 57.38       | 77.72       | 0           | 74.52       | 75.54       | 62.08       |
| ('risk_data_5y', 'stdDev')                    | 0           | 15.33       | 15.76       | 0           | 14.95       | 15.86       | 15.39       |
| ('risk_data_5y', 'sharpeRatio')               | 0           | 0.23        | 0.81        | 0           | 0.7         | 0.9         | 0.49        |
| ('risk_data_5y', 'treynorRatio')              | 0           | 4.79        | -1.9        | 0           | -1.49       | -2.05       | -4.82       |
| ('risk_data_10y', 'year')                     | 10y         | 10y         | 10y         | 10y         | 10y         | 10y         | 10y         |
| ('risk_data_10y', 'alpha')                    | 0           | 7.31        | 1.96        | 0           | 0           | 1.98        | 3.32        |
| ('risk_data_10y', 'beta')                     | 0           | 0.72        | 0.81        | 0           | 0           | 0.8         | 0.7         |
| ('risk_data_10y', 'meanAnnualReturn')         | 0           | 0.92        | 0.5         | 0           | 0           | 0.5         | 0.58        |
| ('risk_data_10y', 'rSquared')                 | 0           | 44.31       | 70          | 0           | 0           | 68.8        | 53.61       |
| ('risk_data_10y', 'stdDev')                   | 0           | 15.7        | 14.14       | 0           | 0           | 14.08       | 13.96       |
| ('risk_data_10y', 'sharpeRatio')              | 0           | 0.32        | 0.84        | 0           | 0           | 0.94        | 0.78        |
| ('risk_data_10y', 'treynorRatio')             | 0           | 13.09       | 5.32        | 0           | 0           | 5.37        | 7.58        |
| ('annual_returns', '2017')                    | nan         | 20.83%      | 23.56%      | nan         | 24.52%      | 24.01%      | 30.92%      |

## Questions & Answers
In this section you can find answers to commonly asked questions. In case the answer to your question is not here, 
consider creating an [Issue](https://github.com/JerBouma/FinanceDatabase/issues).

- **How is the data obtained?**
    - The data is an aggregation of a variety of sources and is driven by the community to extend further.
- **How can I contribute?**
    - Please see the [Contributing Guidelines](https://github.com/JerBouma/FinanceDatabase/blob/main/CONTRIBUTING.md). Thank you!
- **Is there support for my country?**
    - Yes, most likely there is as the database includes 111 countries. Please check 
    [here](https://github.com/JerBouma/FinanceDatabase/tree/main/Database/Equities/Countries).
- **How can I find out which countries, sectors and/or industries exists within the database without needing to check 
  the database manually?**
    - For this you can use the ``show_options`` function from the package attached to this database. Please see 
    [this example](#companies-in-the-netherlands)
- **When I try collect data I notice that not all tickers return output, why is that?**
    - Some tickers are merely holdings of companies and therefore do not really have any data attached to them. 
      Therefore, it makes sense that not all tickers return data. If you are still in doubt, search the ticker on 
      Google to see if there is really no data available. If you can't find anything about the ticker, consider updating the database by visiting the [Contributing Guidelines](https://github.com/JerBouma/FinanceDatabase/blob/main/CONTRIBUTING.md).

## Contribution
After setting up Git, you can fork and pull the project in. Note that is bulky given the large collection of files.

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
