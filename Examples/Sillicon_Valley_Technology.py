import financedatabase as fd
import FundamentalAnalysis as fa
import pandas as pd
import matplotlib.pyplot as plt

all_technology_companies = fd.select_equities(sector='Technology')
silicon_valley = fd.search_products(all_technology_companies, query='San Jose', search='city')

API_KEY = "YOUR_API_KEY_HERE"
data_set = {}
for ticker in silicon_valley:
    try:
        data_set[ticker] = fa.key_metrics(ticker, API_KEY, period='annual')
    except Exception:
        continue

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
market_cap_plot.legend(prop={'size': 5.25}, loc="upper left")
plt.show()
