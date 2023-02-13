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
Understanding which countries, sectors, industries and categories exist is important to be able to search the database properly. Not only to understand the focus a specific the country but also to understand which area holds the most data. This is a demonstration of the ```show_options``` function, a function crucial to querying data from the Database. The output of all functionalities is cut off in this README for illustration purposes.

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

`Afghanistan, Anguilla, Argentina, Australia, Austria, Azerbaijan, Bahamas, Bangladesh, Barbados, Belgium, Belize, Bermuda, Botswana, Brazil, British Virgin Islands, Cambodia, Canada, Cayman Islands, Chile, China, Colombia, Costa Rica, Cyprus, Czech Republic, Denmark, Dominican Republic, Egypt, Estonia, Falkland Islands, Finland, France, French Guiana, Gabon, Georgia, Germany, Ghana, Gibraltar, Greece, Greenland, ...`

For sectors, you will find the following list if you print `equities_sectors`:

`Basic Materials, Communication Services, Conglomerates, Consumer Cyclical, Consumer Defensive, Consumer Goods, Energy, Financial, Financial Services, Healthcare, Industrial Goods, Industrials, Real Estate, Services, Technology, Utilities`

For industries, you will find the following list if you print `equities_industries`:

`Advertising Agencies, Aerospace & Defense, Aerospace Defense - Major Diversified, Aerospace Defense Products & Services, Agricultural Chemicals, Agricultural Inputs, Air Delivery & Freight Services, Airlines, Airports & Air Services, Aluminum, Apparel Manufacturing, Apparel Retail, Apparel Stores, Asset Management, Auto & Truck Dealerships, Auto Dealerships, Auto Manufacturers, ...`

When you wish to get country, sector or industry specific lists, you can use the related `country`, `sector` and `industry` tags as also found in the help window with `help(fd.show_options)`:

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

`AED, AFN, ALL, AMD, ANG, AOA, ARS, AUD, AWG, AZN, BAM, BBD, BDT, BGN, BHD, BIF, BMD, BND, BOB, BRL, BRX, BSD, BTN, BWP, BYN, BZD, CAD, CAX, CDF, CHF, CLF, CLP, CNH, CNY, COP, CRC, CUC, CUP, CVE, CZK, CZX, DJF, DKK, DKX, ...`

But also when it comes to `etfs` with 

```python
fd.show_options('etfs')
```

 Which returns:

`Allocation--15% to 30% Equity, Allocation--30% to 50% Equity, Allocation--50% to 70% Equity, Allocation--70% to 85% Equity, Allocation--85%+ Equity, Bank Loan, Bear Market, China Region, Commodities Broad Basket, Communications, Consumer Cyclical, Consumer Defensive, ...`

### Collecting information from the database

Once you have figured out how to make use of the `fd.show_options` function, you can query the database for relevant data. Each of the asset classes in the database have a specific `select_` function. This includes the following `select_` options:

- [Equities](https://github.com/JerBouma/FinanceDatabase/blob/main/financedatabase/README.md#equities) (`fd.select_equities`)
- [ETFs](https://github.com/JerBouma/FinanceDatabase/blob/main/financedatabase/README.md#etfs) (`fd.select_etfs`)
- [Funds](https://github.com/JerBouma/FinanceDatabase/blob/main/financedatabase/README.md#funds) (`fd.select_funds`)
- [Indices](https://github.com/JerBouma/FinanceDatabase/blob/main/financedatabase/README.md#indices) (`fd.select_indices`)
- [Currencies](https://github.com/JerBouma/FinanceDatabase/blob/main/financedatabase/README.md#currencies) (`fd.select_currencies`)
- [Cryptocurrencies](https://github.com/JerBouma/FinanceDatabase/blob/main/financedatabase/README.md#cryptocurrencies) (`fd.select_cryptocurrencies`)
- [Money Markets](https://github.com/JerBouma/FinanceDatabase/blob/main/financedatabase/README.md#moneymarkets) (`fd.select_moneymarkets`)

As an example, If you wish to collect data from all equities you can use the following:

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
{'AA': {'short_name': 'Alcoa Corporation',
  'long_name': 'Alcoa Corporation',
  'summary': 'Alcoa Corporation, together with its subsidiaries, produces and sells bauxite, alumina, and aluminum products in the United States, Spain, Australia, Brazil, Canada, and internationally. The company operates through three segments: Bauxite, Alumina, and Aluminum. It engages in bauxite mining operations; and processes bauxite into alumina and sells it to customers who process it into industrial chemical products, as well as aluminum smelting, casting, and rolling businesses. The company offers primary aluminum in the form of alloy ingot or value-add ingot to customers that produce products for the transportation, building and construction, packaging, wire, and other industrial markets; and flat-rolled aluminum sheets to customers that produce beverage and food cans. In addition, it owns hydro power plants that produce and sell electricity to the wholesale market to traders, large industrial consumers, distribution companies, and other generation companies. The company was formerly known as Alcoa Upstream Corporation and changed its name to Alcoa Corporation in October 2016. The company was founded in 1888 and is headquartered in Pittsburgh, Pennsylvania.',
  'currency': 'USD',
  'sector': 'Basic Materials',
  'industry': 'Aluminum',
  'exchange': 'NYQ',
  'market': 'us_market',
  'country': 'United States',
  'state': 'PA',
  'city': 'Pittsburgh',
  'zipcode': '15212-5858',
  'website': 'http://www.alcoa.com',
  'market_cap': 'Mid Cap'},
 'CENX': {'short_name': 'Century Aluminum Company',
  'long_name': 'Century Aluminum Company',
  'summary': 'Century Aluminum Company, together with its subsidiaries, produces standard-grade and value-added primary aluminum products in the United States and Iceland. The company was incorporated in 1981 and is headquartered in Chicago, Illinois.',
  'currency': 'USD',
  'sector': 'Basic Materials',
  'industry': 'Aluminum',
  'exchange': 'NMS',
  'market': 'us_market',
  'country': 'United States',
  'state': 'IL',
  'city': 'Chicago',
  'zipcode': '60606',
  'website': 'http://centuryaluminum.com',
  'market_cap': 'Small Cap'}

<continues>
```

As you can imagine, looking at such a specific selection only yields a few results but picking the entire sector `Basic Materials` would have returned 403 different companies (which excludes exchanges other than the United States).

<div align="center">:white_check_mark: <b>For other asset classes, please have a look <a href="https://github.com/JerBouma/FinanceDatabase/blob/main/financedatabase/README.md">here</a></b>.</div>

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

This results in the following graph which gives an indication which sectors are dominant within The Netherlands. Of course this is a mere example and to truly understand the importance of certain companies for the Netherlands, you would need to know market cap of each sector as well including demographics.

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

### Silicon Valley's Market Cap
If I want to understand which listed technology companies exist in Silicon Valley, I can collect all equities of the sector 'Technology' and then filter based on city to obtain all listed technology companies in 'Silicon Valley'. The city 'San Jose' is where Silicon Valley is located.

````python
import financedatabase as fd

all_technology_companies = fd.select_equities(sector='Technology')
silicon_valley = fd.search_products(all_technology_companies, query='San Jose', search='city')
````
Then I start collecting data with the [FundamentalAnalysis](https://github.com/JerBouma/FundamentalAnalysis) package. Here I collect the key metrics which include 57 different metrics (ranging from PE ratios to Market Cap).

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

Then I make a selection based on the last 5 years and filter by market cap to compare the companies in terms of size with each other. This also causes companies that have not been listed for 5 years to be filtered out of my dataset. Lastly, I plot the data.

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

This results in the graph displayed below which separates the small companies from the large companies. Note that  this does not include _all_ technology companies in Silicon Valley because most are not listed or are not included in the database of the FundamentalAnalysis package.

![FinanceDatabase](https://raw.githubusercontent.com/JerBouma/FinanceDatabase/main/examples/Silicon_Valley_Technology_MarketCap.png)

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
