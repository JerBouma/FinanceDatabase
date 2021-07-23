# Methodology

The directories, together with this README, give some explanation to the methods used to create the database. I will go
over each folder seperately:

1. It starts with **collecting tickers**. I use the package
   [YahooTickerDownloader](https://github.com/Benny-/Yahoo-ticker-symbol-downloader) for this part where I relied on the
   [Pull Request](https://github.com/Benny-/Yahoo-ticker-symbol-downloader/pull/58) by Bruno Hanzen to fix some mistakes
   in the code. This results in approximately 950.000 symbols after aproximately around 50 days of searching. Due to the
   fact that a large portion of the symbols are Options & Futures, and these being time-dependent I do not include them
   in the database. This results in a large decrease (to around 350.000 symbols).
2. Then I **gather all data available for each symbol**. It uses a function from
   [yfinance](https://github.com/ranaroussi/yfinance) named *get_json* to obtain all available data from Yahoo Finance
   for that ticker. It also categorizes the data by type (i.e. Equity, Fund, ETF) and saves each symbol to a pickle.
   This takes approximately 10-20 days to run. Whenever the symbol is an option or a future, I fill an empty pickle. 
   Due to the file limit of 100MB for GitHub, I seperate some JSON files in parts
3. Lastly, **the database is created with the relevant (timeless) information**. I have multiple functions that create
   directories structures (i.e. based on Country, Sector, Category) and functions that search through the data to find
   relevant and useful data points to store in a json file. I pay extra attention to whether the data does not change
   over time. The reason for this is the purpose of the database is not to provide up-to-date fundamentals but instead
   to be used to find those symbols that match a specific criteria (i.e. all companies in Brazil that fall under the
   Sector "Basic Materials" and the industry "Chemicals"). This is because it takes too long to collect all the data and
   with packages like [FundamentalAnalysis](https://github.com/JerBouma/FundamentalAnalysis) or
   [yfinance](https://github.com/ranaroussi/yfinance) it becomes easy to collect fundamental data.

By following these steps you should be able to reproduce the exact structure I have here. I highly appreciate it when
you make updates to the database by following above steps. This way we can keep the database as up to date and complete
as possible. Please do inform me first when you attempt to update the database to prevent multiple users from doing the 
exact same thing.
