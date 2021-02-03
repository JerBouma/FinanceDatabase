import FinanceDatabase as fd
from yfinance.utils import get_json
import matplotlib.pyplot as plt

all_etfs = fd.select_etfs()

semiconductor_etfs = fd.search_products(all_etfs, 'semiconductor')

# Remove some unwanted ETFs
del semiconductor_etfs['DXSH.DE']
del semiconductor_etfs['DXSH.F']

semiconductor_etfs_fundamentals = {}
for symbol in semiconductor_etfs:
    semiconductor_etfs_fundamentals[symbol] = get_json("https://finance.yahoo.com/quote/" + symbol)

for symbol in semiconductor_etfs_fundamentals:
    ytd_return = semiconductor_etfs_fundamentals[symbol]['fundPerformance']['trailingReturns']['ytd']
    long_name = semiconductor_etfs_fundamentals[symbol]['quoteType']['longName']

    if ytd_return is None:
        continue

    plt.barh(long_name, ytd_return)

plt.tight_layout()
plt.xticks([-1, -0.5, 0, 0.5, 1], ['-100%', '-50%', '0%', '50%', '100%'])
plt.show()
