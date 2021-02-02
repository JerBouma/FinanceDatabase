# Finance Database
As a private investor, the sheer amount of information that can be found on the internet is rather daunting. Trying to 
understand what type of companies or ETFs are available is incredibly challenging with there being millions of
companies amd derivatives available on the market. Sure, the most traded companies and ETFs can quickly be found
simply because they are known to the public (for example, Microsoft, Tesla, S&P500 ETF or an All-World ETF). However, 
what else is out there is often unknown.

**This database tries to solve that**. It features 180.000+ symbols containing Equities, ETFs, Funds, Indices, Futures, 
Options, Currencies, Cryptocurrencies and Money Markets. It therefore allows you to obtain a broad overview of sectors,
industries, types of investments and much more.

The aim of this database is explicitly _not_ to provide up-to-date fundamentals or stock data as those can be obtained 
with ease (with the help of this database) by using [FundamentalAnalysis](https://github.com/JerBouma/FundamentalAnalysis) 
or [yfinance](https://github.com/ranaroussi/yfinance). Instead, it gives  insights into the products that exist in each 
country, industry and sector and gives the most essential information about each product. With this information, you 
can analyse specific areas of the financial world and/or find that product that is hard to find. See for examples
on how you can combine this database and the earlier mentioned packages the section [Examples](#Examples).

Some key statistics of the database:

| Product           | Quantity  | Sectors   | Industries    | Countries | Exchanges |
| ----------------- | --------- | --------- | ------------- | --------- | --------- |
| Equities          | 84.091    | 16        | 262           | 109       | 79        |
| ETFs              | 15.892    | 268*      | 88*           | 100**     | 44        |
| Funds             | 34.947    | 857*      | 416*          | 100**     | 25        |

| Product           | Quantity  | Exchanges |
| ----------------- | --------- | --------- |
| Indices           | 24.548    | 62        |
| Currencies        | 2.529     | 2         |
| Cryptocurrencies  | 3.624     | 1         |
| Options           | 13.819    | 1         |
| Futures           | 1.173     | 7         |
| Money Markets     | 1.384     | 2         |

\* These numbers refer to families (iShares, Vanguard) and categories (World Stock, Real Estate) respectively.  
\** This is an estimation. Obtaining the country distribution can only be done by collecting data on the underlying 
or by manual search.

## Examples
For example, if I wish to obtain all companies within the Semiconductor industry, I can load in the .json file in
Python with the following lines of code:

````
import json

with open('semiconductors.json') as json_file:
    semiconductors = json.load(json_file)
````
Then, I can use packages like [yfinance](https://github.com/ranaroussi/yfinance) to quickly collect data from 
Yahoo Finance for each symbol in the industry like this:
````
from yfinance.utils import get_json

semiconductors_data = {}
for symbol in semiconductors.keys():
    semiconductors_data[symbol] = get_json("https://finance.yahoo.com/quote/" + symbol)
```` 
With a few lines of code, I have collected all data from one specific industry. From here on you can compare pretty
much any key statistic, fundamental data and stock data. Please see the documentation from yfinance for the available
options and further examples.