import json
from yfinance.utils import get_json
import matplotlib.pyplot as plt

all_etfs = json.load(open(r"C:\Users\jerbo\Google Drive\Programming\Python\FinanceDatabase\Database\ETFs\_ETFs.json", "rb"))


def search_products(database, query, new_database=None):
    if new_database is None:
        new_database = {}

    for symbol in database:
        try:
            if query in database[symbol]['summary']:
                new_database[symbol] = database[symbol]
        except (TypeError, KeyError):
            continue

    return new_database


semiconductor_etfs = search_products(all_etfs, 'semiconductor')

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
