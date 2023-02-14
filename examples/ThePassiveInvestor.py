import pandas as pd

import financedatabase as fd

core_selection = fd.select_etfs("core_selection_filtered", exclude_exchanges=False)

tickers = pd.Series(core_selection.keys())
tickers.to_excel("core_selection_tickers.xlsx", index=None, header=None)
