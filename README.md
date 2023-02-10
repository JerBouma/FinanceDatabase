![FinanceDatabase](https://raw.githubusercontent.com/JerBouma/FinanceDatabase/main/examples/FinanceDatabaseCropped.png)

[![BuyMeACoffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-Donate-brightgreen?logo=buymeacoffee)](https://www.buymeacoffee.com/jerbouma)
[![Issues](https://img.shields.io/github/issues/jerbouma/financedatabase)](https://github.com/JerBouma/FinanceDatabase/issues)
[![Pull Requests](https://img.shields.io/github/issues-pr/JerBouma/FinanceDatabase?color=yellow)](https://github.com/JerBouma/FinanceDatabase/pulls)
[![PYPI Version](https://img.shields.io/pypi/v/FinanceDatabase)](https://pypi.org/project/FinanceDatabase/)
[![PYPI Downloads](https://img.shields.io/pypi/dm/FinanceDatabase)](https://pypi.org/project/FinanceDatabase/)

| :bulb: **Call for Contributors for the FinanceDatabase** :bulb:   |
|:------------------------------------------------------:|
| The FinanceDatabase serves the role of providing any type of investor with any type of financial product categorisation completely for free. To be able to achieve this, the FinanceDatabase relies on involvement from the community to update, edit and remove tickers over time. This is made easy enough that anyone, even with a lack of coding experience can contribute because of the generation of JSON files that can be manually edited. I'd like to invite you to go to the [Contributing Guidelines](https://github.com/JerBouma/FinanceDatabase/blob/main/CONTRIBUTING.md) to understand how you can help. **Thank you!** |

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

1. [Using the Database](#using-the-database)
    1. [Installation](#installation)
    2. [Functions](#functions)
    3. [Advanced Usage](#advanced-usage)
2. [Examples](#examples)
    1. [Companies in the Netherlands](#companies-in-the-netherlands)
    2. [Technical Analysis of Biotech ETFs](#technical-analysis-of-biotech-etfs)
    3. [United States' Airlines](#united-states-airlines)
    4. [Silicon Valley's Market Cap](#silicon-valleys-market-cap)
    5. [Compare Japanese Stock ETFs](#compare-japanese-stock-etfs)
3. [Questions & Answers](#questions--answers)
4. [Contribution](#contribution)


## Using the Database
To access the database you can download the entire repository, but I strongly recommend making use of the package 
closely attached to the database. It allows you to select specific json files as well as search through collected
data with a specific query.

### Installation
You can install the package with the following steps:
1. `pip install financedatabase`
    - Alternatively, download the 'Searcher' directory.
2. (within Python) `import financedatabase as fd`

### Functions
The package has the following functions:
- `show_options(product, equities_selection=None, country=None, sector=None, industry=None)` - gives all available options from 
  the functions below per product (i.e. Equities, Funds) which then can be used to collect data. You can select a 
  sub selection of equities by entering 'countries', 'sectors' or 'industries' for equities_selection as well as select 
  the specific sectors and industries per country and industries per sector via the 'country' and 'sector' parameters. 
  The industry variable is a boolean that returns all industries, to what sector each corresponds and all countries 
  that have companies in this industry.
- `select_cryptocurrencies(cryptocurrency=None)` - with no input gives all cryptocurrencies, with input gives 
the cryptocurrency of choice.
- `select_currencies(currency=None)` - with no input gives all currencies, with input gives 
the currency of choice.
- `select_etfs(category=None)` - with no input gives all etfs, with input gives all etfs of a 
specific category.
- `select_equities(country=None, sector=None, industry=None)` - with no input gives all equities, with input 
gives all equities of a country, sector, industry or a combination of the three.
- `select_funds(category=None)` - with no input gives all funds, with input gives all funds of a 
specific category.
- `select_indices(market=None)` - with no input gives all indices, with input gives all indices of a 
specific market which usually refers to indices in a specific country (like de_market gives DAX).
- `select_moneymarkets(market=None)` - with no input gives all moneymarkets, with input gives all moneymarkets of a 
specific market which usually refers to moneymarkets in a specific country.
- `search_products(database, query, search='summary', case_sensitive=False, new_database=None)` - with input 
  from the above functions, this function searches for specific values (i.e. the query 'sustainable') in 
  one of the keys of the dictionary (which is by default the summary). It also has the option to enable 
  case-sensitive searching which is off by default.
  
For users of the broker **DeGiro**, you are able to find data on the tickers found in the 
[Commission Free ETFs](https://www.degiro.ie/data/pdf/ie/commission-free-etfs-list.pdf) list by selecting either 
`core_selection_degiro_filled` (all data) or `core_selection_degiro_filtered` (filtered by summary) as category 
when using the function `select_etfs`.

By default, exchanges are not included in the selection functions. Therefore, the amount of data returned is less 
than depicted in the key statistics. If you wish to include all exchanges, please set `exclude_exchanges` to `False`.

For additional information about each function you can use the built-in help function of Python. For 
example `help(show_options)` returns a general description, the possible input parameters and what is returned 
as output.
  
### Advanced Usage
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
This gives the following lists (where  ```equities_all_categories``` is a dictionary with these three lists):

![FinanceDatabase](https://raw.githubusercontent.com/JerBouma/FinanceDatabase/main/examples/CountriesSectorsIndustries.png)

Then, I want to see how many companies exist in each sector in the Netherlands. Let's count all companies with the 
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

- **How did you get your data?**
    - Please check the [Methodology](https://github.com/JerBouma/FinanceDatabase/tree/main/Methodology).
- **Is there support for <insert_country>?**
    - Yes, most likely there is as the database includes 111 countries. Please check 
    [here](https://github.com/JerBouma/FinanceDatabase/tree/main/Database/Equities/Countries).
- **How can I find out which countries, sectors and/or industries exists within the database without needing to check 
  the database manually?**
    - For this you can use the ``show_options`` function from the package attached to this database. Please see 
    [this example](#companies-in-the-netherlands)
- **When I collect data via yfinance I notice that not all tickers return output, why is that?**
    - Some tickers are merely holdings of companies and therefore do not really have any data attached to them. 
      Therefore, it makes sense that not all tickers return data. If you are still in doubt, search the ticker on 
      Google to see if there is really no data available.
- **How frequently does the Database get updated?**
    - I aim at doing this every few months. The database does not have to get updated frequently because the data 
      collected is only general information. For example, a Sector name hardly changes and companies do not tend to 
      move to another country every few months. Therefore, the data should stay up to date for several months. 
      *If you wish to contribute to updating the database then that is much appreciated. Please check the 
      [Methodology](https://github.com/JerBouma/FinanceDatabase/tree/main/Methodology) for guidance on how.*
- **Do your sector and industry names use the same naming convention as GIC sector**?
    - Not entirely but very similar, it's based on Yahoo Finance's sectors and industries. See industries and 
      sectors. Perhaps a future adjustment could be to make them aligned with GICS.

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
