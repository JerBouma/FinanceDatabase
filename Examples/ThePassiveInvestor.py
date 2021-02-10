import FinanceDatabase as fd
import pandas as pd

core_selection = fd.select_etfs("core_selection_degiro_filtered")

tickers = pd.Series(core_selection.keys())
tickers.to_excel('core_selection_tickers.xlsx', index=None, header=None)
