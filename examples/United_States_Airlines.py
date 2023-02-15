import random

import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
from yfinance import download
from yfinance.utils import get_json

import financedatabase as fd

airlines_us = fd.select_equities(country="United States", industry="Airlines")

airlines_us_fundamentals = {}
for symbol in airlines_us:
    airlines_us_fundamentals[symbol] = get_json(
        "https://finance.yahoo.com/quote/" + symbol
    )

airlines_us_stock_data = download(list(airlines_us))

colors = list(mcolors.CSS4_COLORS.items())

for symbol in airlines_us_fundamentals:
    color = random.choice(colors)[1]
    quick_ratio = airlines_us_fundamentals[symbol]["financialData"]["quickRatio"]
    long_name = airlines_us_fundamentals[symbol]["quoteType"]["longName"]

    if quick_ratio is None:
        continue

    plt.barh(long_name, quick_ratio, color=color)

plt.tight_layout()
plt.show()
