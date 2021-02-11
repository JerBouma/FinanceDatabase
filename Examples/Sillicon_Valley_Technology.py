import FinanceDatabase as fd
import FundamentalAnalysis as fa
import pandas as pd

all_technology_companies = fd.select_equities(sector='Technology')
silicon_valley = fd.search_products(all_technology_companies, query='San Jose', search='city')

# Remove tickers with a dot in it which refer to different markets
for ticker in silicon_valley.copy():
    if '.' in ticker:
        del silicon_valley[ticker]

API_KEY = "YOUR API KEY HERE"
data_set = {}
for ticker in silicon_valley:
    try:
        data_set[ticker] = fa.key_metrics(ticker, API_KEY, period='annual')
    except Exception:
        continue

years = ['2020', '2019', '2018', '2017', '2016']
market_cap = pd.DataFrame(columns=years)
for ticker in data_set:
    try:
        data_years = []
        for year in years:
            data_years.append(data_set[ticker].loc['marketCap'][year])
        market_cap.loc[ticker] = data_years
    except Exception:
        continue

names = [all_technology_companies[name]['short_name']
         for name in all_technology_companies
         if name in market_cap.index]
market_cap.index = names

market_cap.T.plot.bar(stacked=True, rot=0)

