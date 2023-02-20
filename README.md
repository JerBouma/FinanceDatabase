<p align="center">
    <img src="https://user-images.githubusercontent.com/46355364/219180773-7c70fe5d-8597-43ce-8b11-96dee2afb98a.png" alt="Logo">
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

# Table of Contents

1. [Installation](#installation)
2. [Basic Usage](#basic-usage)
    1. [Quick Start](#quick-start)
    3. [Collecting information from the database](#collecting-information-from-the-database)
    3. [Searching the database extensively](#searching-the-database-extensively)
    4. [Storing the database at a different location](#storing-the-database-at-a-different-location)
2. [Examples](#examples)
    1. [Companies in the Netherlands](#companies-in-the-netherlands)
    2. [Technical Analysis of Biotech ETFs](#technical-analysis-of-biotech-etfs)
    3. [Silicon Valley's Market Cap](#silicon-valleys-market-cap)
3. [Questions & Answers](#questions--answers)
4. [Contribution](#contribution)


# Installation
The package `financedatabase` allows you to select specific json files as well as search through collected data with a specific query.

You can install the package with the following steps:
1. `pip install financedatabase`
2. (within Python) `import financedatabase as fd`

#  Basic Usage
This section explains in detail how the database can be queried with the related `financedatabase` package, also see the Jupyter Notebook in which you can run the examples also demonstrated here. You can find this document [here](https://github.com/JerBouma/FinanceDatabase/blob/main/examples.ipynb).

## Quick Start

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

## Collecting information from the database

Please see the Jupyter Notebook for an elaborate explanation of each asset class. This includes Equities, ETFs, Funds, Indices, Currencies, Cryptocurrencies and Money Markets.
___

<b><div align="center">Find code examples of all Asset Classes in the Jupyter Notebook <a href="https://github.com/JerBouma/FinanceDatabase/blob/main/examples.ipynb">here</a>.</div></b>
___


As an example for Equities, If you wish to collect data from all equities you can use the following:

```python
import financedatabase as fd

# Initialize the Equities database
equities = fd.Equities()

# Obtain all data available excluding international exchanges
equities.select()
```

Which returns the following DataFrame:

| symbol   | short_name                    | long_name                      | currency   | sector             | industry                         | exchange   | market    | country       | state   | city        | zipcode    | website                             | market_cap   |
|:---------|:------------------------------|:-------------------------------|:-----------|:-------------------|:---------------------------------|:-----------|:----------|:--------------|:--------|:------------|:-----------|:------------------------------------|:-------------|
| A        | Agilent Technologies, Inc.    | Agilent Technologies, Inc.     | USD        | Healthcare         | Diagnostics & Research           | NYQ        | us_market | United States | CA      | Santa Clara | 95051      | http://www.agilent.com              | Large Cap    |
| AA       | Alcoa Corporation             | Alcoa Corporation              | USD        | Basic Materials    | Aluminum                         | NYQ        | us_market | United States | PA      | Pittsburgh  | 15212-5858 | http://www.alcoa.com                | Mid Cap      |
| AAALF    | AAREAL BANK AG                | Aareal Bank AG                 | USD        | nan                | nan                              | PNK        | us_market | Germany       | nan     | Wiesbaden   | 65189      | http://www.aareal-bank.com          | Small Cap    |
| AAALY    | AAREAL BANK AG                | Aareal Bank AG                 | USD        | nan                | nan                              | PNK        | us_market | nan           | nan     | nan         | nan        | nan                                 | nan          |
| AABB     | ASIA BROADBAND INC            | Asia Broadband, Inc.           | USD        | Basic Materials    | Other Industrial Metals & Mining | PNK        | us_market | United States | NV      | Las Vegas   | 89135      | http://www.asiabroadbandinc.com     | Micro Cap    |
| AABVF    | ABERDEEN INTERNATIONAL INC    | Aberdeen International Inc.    | USD        | Financial Services | Asset Management                 | PNK        | us_market | Canada        | ON      | Toronto     | M5H 2M5    | http://www.aberdeeninternational.ca | Nano Cap     |
| AAC      | Ares Acquisition Corporation  | Ares Acquisition Corporation   | USD        | Financial Services | Shell Companies                  | NYQ        | us_market | United States | NY      | New York    | 10167      | nan                                 | Small Cap    |

This returns approximately 20.000 different equities. Note that by default, only the American exchanges are selected. These are symbols like `TSLA` (Tesla) and `MSFT` (Microsoft) that tend to be recognized by a majority of data providers and therefore is the default. To disable this, you can set the `exclude_exchanges` argument to `False` which then results in approximately 155.000 different symbols. 

Note that the summary column is taken out on purpose to keep it organized for markdown. The summary is however very handy when it comes to querying specific words as found with the following description given for Apple. All of this information is available when you query the database.

```text
Apple Inc. designs, manufactures, and markets smartphones, personal computers, tablets, wearables, and accessories worldwide. It also sells various related services. The company offers iPhone, a line of smartphones; Mac, a line of personal computers; iPad, a line of multi-purpose tablets; and wearables, home, and accessories comprising AirPods, Apple TV, Apple Watch, Beats products, HomePod, iPod touch, and other Apple-branded and third-party accessories. It also provides AppleCare support services; cloud services store services; and operates various platforms, including the App Store, that allow customers to discover and download applications and digital content, such as books, music, video, games, and podcasts. In addition, the company offers various services, such as Apple Arcade, a game subscription service; Apple Music, which offers users a curated listening experience with on-demand radio stations; Apple News+, a subscription news and magazine service; Apple TV+, which offers exclusive original content; Apple Card, a co-branded credit card; and Apple Pay, a cashless payment service, as well as licenses its intellectual property. The company serves consumers, and small and mid-sized businesses; and the education, enterprise, and government markets. It sells and delivers third-party applications for its products through the App Store. The company also sells its products through its retail and online stores, and direct sales force; and third-party cellular network carriers, wholesalers, retailers, and resellers. Apple Inc. was founded in 1977 and is headquartered in Cupertino, California.
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

As an example, we can use `equities.options` to obtain specific country, sector and industry options. For example with `equities.options(selection='industry', country="United States", sector="Basic Materials")` all industries within the sector Basic Materials within the United States can be obtained. This allows us to look at a specific industry in the United States in detail. So with this information in hand, I can now query the industry `Aluminum` as follows:

```python
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

## Searching the database extensively
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
- `fd.Equities(base_url=<YOUR URL>)`

You can also store the database locally and point to your local location with the variable `base_url` and by setting
`use_local_location` to True. An example would be:
- `fd.Equities(base_url=<YOUR PATH>, use_local_location=True)`

# Examples
This section gives a few examples of the possibilities with this package. These are merely a few of the things you
can do with the package. **As you can obtain a wide range of symbols, pretty much any 
package that requires symbols should work.**

## Companies in the Netherlands
I want to see how many companies exist in each sector in the Netherlands. Let's count all companies with the 
following code, I skip a sector when it has no data and also do not include companies that are not categorized:

````python
import financedatabase as fd

equities = fd.Equities()

equities_per_sector_netherlands = {}

for sector in equities.options(selection='sector', country='Netherlands'):
    try:
        equities_per_sector_netherlands[sector] = len(equities.select(country='Netherlands', sector=sector))
    except ValueError as error:
        print(error)
````

Lastly, I plot the data in a pie chart and add some formatting to make the pie chart look a bit nicer:

````python
import matplotlib.pyplot as plt

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

![FinanceDatabase](https://user-images.githubusercontent.com/46355364/219180273-4ed5f3a5-6ecf-4994-8a8e-285d9c51fe7d.png)

## Technical Analysis of Biotech ETFs
With the help of [ta](https://github.com/bukosabino/ta) and [yfinance](https://github.com/ranaroussi/yfinance) I can 
quickly perform a basic technical analysis on a group of ETFs categorized by the FinanceDatabase. I start by 
searching the database for ETFs related to Health and then make a subselection by searching, in the collected database, 
for biotech-related ETFs:

````python
import financedatabase as fd

etfs = fd.ETFs()

health_etfs_in_biotech = etfs.search(category='Health', summary='biotech')
````

Then, I collect stock data on each ticker and remove tickers that have no data in my chosen period. The period I have 
chosen shows the initial impact of the Coronacrisis on the financial markets.

````python
import yfinance as yf

tickers = list(health_etfs_in_biotech['symbol'])

stock_data_biotech = yf.download(tickers, start="2020-01-01", end="2020-06-01")['Adj Close']
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
    long_name = health_etfs_in_biotech.loc[health_etfs_in_biotech.symbol == ticker, 'long_name'].iloc[0]

    indicator_bb = BollingerBands(close=stock_data_biotech[ticker], window=20, window_dev=2)

    data_plot['bb_bbm'] = indicator_bb.bollinger_mavg()
    data_plot['bb_bbh'] = indicator_bb.bollinger_hband()
    data_plot['bb_bbl'] = indicator_bb.bollinger_lband()

    axis[row, column].plot(data_plot)
    axis[row, column].set_title(long_name, fontsize=6)
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

![FinanceDatabase](https://user-images.githubusercontent.com/46355364/219180415-dc303fa3-a615-4f80-96cf-eadb2b804a65.png)

## Silicon Valley's Market Cap
If I want to understand which listed technology companies exist in Silicon Valley, I can collect all equities of the sector 'Technology' and then filter based on city to obtain all listed technology companies in 'Silicon Valley'. The city 'San Jose' is where Silicon Valley is located.

````python
import financedatabase as fd

equities = fd.Equities()

silicon_valley = equities.search(sector='Technology', city='San Jose')
````
Then I start collecting data with the [FundamentalAnalysis](https://github.com/JerBouma/FundamentalAnalysis) package. Here I collect the key metrics which include 57 different metrics (ranging from PE ratios to Market Cap).

````python
import fundamentalanalysis as fa

API_KEY = "YOUR_API_KEY_HERE"
data_set = {}

for ticker in silicon_valley['symbol']:
    try:
        data_set[ticker] = fa.key_metrics(ticker, API_KEY, period='annual', limit=10)
    except Exception:
        continue
````

Then I make a selection based on the last 5 years and filter by market cap to compare the companies in terms of size with each other. This also causes companies that have not been listed for 5 years to be filtered out of my dataset. Lastly, I plot the data.

````python
import pandas as pd
import matplotlib.pyplot as plt

years = ['2018', '2019', '2020', '2021', '2022']
market_cap = pd.DataFrame(index=years)

for ticker in data_set:
    try:
        data_years = []
        for year in years: 
            data_years.append(data_set[ticker].loc['marketCap'][year])
        market_cap[silicon_valley.loc[silicon_valley.symbol == ticker]['short_name'].iloc[0]] = data_years
    except Exception:
        continue

market_cap_plot = market_cap.plot.bar(stacked=True, rot=0, colormap='Spectral')
market_cap_plot.legend(prop={'size': 5.25}, loc='upper left')
plt.show()
````

This results in the graph displayed below which separates the small companies from the large companies. Note that  this does not include _all_ technology companies in Silicon Valley because most are not listed or are not included in the database of the FundamentalAnalysis package.

![FinanceDatabase](https://user-images.githubusercontent.com/46355364/219179328-7eb54138-42a1-4d51-9ae1-5ac182c33440.png)

# Questions & Answers
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

# Contribution
After setting up Git, you can fork and pull the project in.

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
