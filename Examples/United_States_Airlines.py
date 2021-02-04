import FinanceDatabase as fd
from yfinance.utils import get_json
from yfinance import download
import matplotlib.pyplot as plt

airlines_us = fd.select_equities(country='United States', industry='Airlines')

airlines_us_fundamentals = {}
for symbol in airlines_us:
    airlines_us_fundamentals[symbol] = get_json("https://finance.yahoo.com/quote/" + symbol)

airlines_us_stock_data = download(list(airlines_us))

for symbol in airlines_us_fundamentals:
    quick_ratio = airlines_us_fundamentals[symbol]['financialData']['quickRatio']
    long_name = airlines_us_fundamentals[symbol]['quoteType']['longName']

    if quick_ratio is None:
        continue

    plt.barh(long_name, quick_ratio)

plt.tight_layout()
plt.show()

