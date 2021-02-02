# Methodology
The directories, together with this README, give some explanation to the methods used to create the database. I will
go over each folder seperately:

1. It starts with **collecting tickers**. I use the package 
[YahooTickerDownloader](https://github.com/Benny-/Yahoo-ticker-symbol-downloader) for this part where I relied on the
[Pull Request](https://github.com/Benny-/Yahoo-ticker-symbol-downloader/pull/58) by Bruno Hanzen to fix some mistakes
in the code. Furthermore, I have limited the search queries to prevent the downloader from searching tickers that are
specialized derivatives or short-lived contracts. I did this by limiting the length of the symbol search to max 5 
characters and not adding numbers which do not occur in regular equities. This results in approximately 200.000 symbols
after aproximately 12-15 hours of searching.
2. Then I **gather all data available for each symbol**. This is the most time consuming part. It uses a function from
[yfinance](https://github.com/ranaroussi/yfinance) named *get_json* to obtain all available data from Yahoo Finance for
that ticker. It also categorizes the data by type (i.e. Equity, Option, ETF) and saves to pickles. This takes 
approximately 5-7 days to run. This is another reason why I made some restrictions to the collection of tickers. 
Without restrictions you could end up with 500.000+ symbols (with most being not worthwhile to collect).
3. Lastly, **the database is created with the relevant (timeless) information**. I have multiple functions that create 
directories structures (i.e. based on Country, Sector, Category) and functions that search through the data to find 
relevant and useful data points to  store in a json file. I pay extra attention to whether the data does not change over
time. The reason for this is the purpose of the database is not to provide up-to-date fundamentals but instead to be 
used to find those symbols that match a specific criteria (i.e. all companies in Brazil that fall under the Sector 
"Basic Materials" and the  industry "Chemicals"). This is because it takes too long to collect all the data and 
with packages like [FundamentalAnalysis](https://github.com/JerBouma/FundamentalAnalysis) or 
[yfinance](https://github.com/ranaroussi/yfinance) it becomes easy to collect the fundamentals data.

By following these steps you should be able to reproduce the exact structure I have here. But why bother if I already
went through the whole process of collection and organizing! :wink: