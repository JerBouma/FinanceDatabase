import financedatabase as fd
import matplotlib.pyplot as plt
import pandas as pd
import yfinance as yf
from ta.volatility import BollingerBands

# Obtain all ETFs in the category health then filter based on biotech
health_etfs = fd.select_etfs(category='Health')
health_etfs_in_biotech = fd.search_products(health_etfs, 'biotech')

# Download stock data on the Biotech companies
stock_data_biotech = yf.download(list(health_etfs_in_biotech.keys()), start="2020-01-01", end="2020-06-01")['Adj Close']
stock_data_biotech = stock_data_biotech.dropna(axis='columns')

# Initalise the plot and row/column variables
figure, axis = plt.subplots(4, 3)
row = 0
column = 0

# Loop over the tickers
for ticker in stock_data_biotech.columns:
    # Initalise the DataFrame
    data_plot = pd.DataFrame(stock_data_biotech[ticker])

    # Initialize Bollinger Bands Indicator
    indicator_bb = BollingerBands(close=stock_data_biotech[ticker], window=20, window_dev=2)

    # Add Bollinger Bands features
    data_plot['bb_bbm'] = indicator_bb.bollinger_mavg()
    data_plot['bb_bbh'] = indicator_bb.bollinger_hband()
    data_plot['bb_bbl'] = indicator_bb.bollinger_lband()

    # Create the plot
    axis[row, column].plot(data_plot)
    axis[row, column].set_title(health_etfs_in_biotech[ticker]['long_name'], fontsize=6)
    axis[row, column].set_xticks([])
    axis[row, column].set_yticks([])

    # Count a column further
    column += 1

    # If the column reaches the max, add another row
    if column == 3:
        row += 1
        column = 0

# Correct overlapping titles and axes
figure.suptitle('Technical Analysis of Biotech ETFs during the Coronacrisis')
figure.tight_layout()
