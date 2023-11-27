name: Database Update

on:
  push:
  schedule:
    - cron: '0 12 * * SUN'

jobs:
  Add-New-Ticker:
    runs-on: ubuntu-latest
    steps:
      - name: checkout repo content
        uses: actions/checkout@v3
      - name: pull changes
        run: git pull https://${{secrets.PAT}}@github.com/JerBouma/FinanceDatabase.git main
      - name: setup python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - run: pip install -r requirements.txt
      - run: pip install financedatabase openpyxl
      - name: Add New Tickers and Update Old Ones
        uses: jannekem/run-python-script-action@v1
        with:
          script: |
            import numpy as np
            import pandas as pd

            # Collect NASDAQ data
            nasdaq = pd.read_json("https://raw.githubusercontent.com/rreichel3/US-Stock-Symbols/main/nasdaq/nasdaq_full_tickers.json")
            nasdaq = nasdaq.set_index('symbol')
            nasdaq['exchange'] = 'NMS'
            nasdaq['market'] = 'NASDAQ Global Select'

            # Collect NYSE data
            nyse = pd.read_json("https://raw.githubusercontent.com/rreichel3/US-Stock-Symbols/main/nyse/nyse_full_tickers.json")
            nyse = nyse.set_index('symbol')
            nyse['exchange'] = 'ASE'
            nyse['market'] = 'NYSE MKT'

            # Collect AMEX data, since it got acquired this is now the same exchange/market as NYSE
            amex = pd.read_json("https://raw.githubusercontent.com/rreichel3/US-Stock-Symbols/main/amex/amex_full_tickers.json")
            amex = amex.set_index('symbol')
            amex['exchange'] = 'ASE'
            amex['market'] = 'NYSE MKT'

            # Combine the datasets
            exchange_data = pd.concat([nasdaq, nyse, amex])

            # Obtain the categories from the FinanceDatabase for conversion
            fd_categories_path = 'compression/categories/github_exchange_categories.xlsx'
            fd_sectors = pd.read_excel(fd_categories_path, sheet_name='sector', index_col=1)
            fd_industry_groups = pd.read_excel(fd_categories_path, sheet_name='industry_group', index_col=1)
            fd_industries = pd.read_excel(fd_categories_path, sheet_name='industry', index_col=1)

            # Read the equities database
            equities = pd.read_csv('database/equities.csv', index_col=0)
            ticker_dict = {}

            # Loop over the exchange dataset and create a new object that will be added to the database
            for index, row in exchange_data.iterrows():
                if row['marketCap']:
                    market_cap_value = float(row['marketCap'])
                
                    if market_cap_value >= 200_000_000_000:
                        market_cap = 'Mega Cap'
                    elif market_cap_value >= 10_000_000_000 and market_cap_value < 200_000_000_000:
                        market_cap= 'Large Cap'
                    elif market_cap_value >= 2_000_000_000 and market_cap_value < 10_000_000_000:
                        market_cap = 'Mid Cap'
                    elif market_cap_value >= 300_000_000 and market_cap_value < 2_000_000_000:
                        market_cap = 'Small Cap'
                    elif market_cap_value >= 50_000_000 and market_cap_value < 300_000_000:
                        market_cap = 'Micro Cap' 
                    else:
                        market_cap = 'Nano Cap'
                else:
                    market_cap = np.nan
                    
                try:
                    # Checks if ticker exists, if yes, continue
                    fd_data = equities.loc[index]
                    
                    if fd_data['market_cap'] != market_cap and market_cap == market_cap:
                        ticker_dict[index] = {'symbol': index}
                        for column, value in fd_data.items():
                            if column == 'market_cap':
                                ticker_dict[index][column] = market_cap
                            else:
                                ticker_dict[index][column] = value
                    continue
                except KeyError:
                    if row['name'] == 'Nano Labs Ltd American Depositary Shares':
                      # Specific case where the ticker is NA which is recognized
                      # as a NaN instead meaning it will continuously be added
                      index = "NA"

                    ticker_dict[index] = {}

                    ticker_dict[index]['name'] = row['name']
                    ticker_dict[index]['summary'] = np.nan
                    ticker_dict[index]['currency'] = "USD"

                    try:
                        industry = fd_industries.loc[row['industry']].iloc[0]
                        
                        if isinstance(industry, pd.Series):
                            industry = industry[0]
                        
                        ticker_dict[index]['industry'] = industry
                    except KeyError:
                        ticker_dict[index]['industry'] = np.nan
                        
                    try:
                        industry_divison = equities[equities['industry'] == ticker_dict[index]['industry']]
                        industry_group = industry_divison['industry_group'].mode()[0]
                            
                        ticker_dict[index]['industry_group'] = industry_group
                    except KeyError:
                        ticker_dict[index]['industry_group'] = np.nan
                    
                    try:
                        sector_division = equities[(equities['industry_group'] == ticker_dict[index]['industry_group']) & (equities['industry'] == ticker_dict[index]['industry'])]
                        sector = sector_division['sector'].mode()[0]

                        ticker_dict[index]['sector'] = sector
                    except Exception:
                        ticker_dict[index]['sector'] = np.nan
                    
                    ticker_dict[index]['exchange'] = row['exchange']
                    ticker_dict[index]['market'] = row['market']  
                    ticker_dict[index]['country'] = row['country']
                    ticker_dict[index]['state'] = np.nan
                    ticker_dict[index]['city'] = np.nan
                    ticker_dict[index]['zipcode'] = np.nan
                    ticker_dict[index]['website'] = np.nan
                    ticker_dict[index]['market_cap'] = market_cap
                    ticker_dict[index]['isin'] = np.nan
                    ticker_dict[index]['cusip'] = np.nan
                    ticker_dict[index]['figi'] = np.nan
                    ticker_dict[index]['composite_figi'] = np.nan
                    ticker_dict[index]['shareclass_figi'] = np.nan

            # Create a DataFrame out of the created dictionary
            updated_companies = pd.DataFrame.from_dict(ticker_dict, orient='index')
            updated_companies.index.name = 'symbol'

            print(f"There are {len(updated_companies)} new updates!")

            if not updated_companies.empty:
                # Loop over all acquired values and update data
                for index, values in updated_companies.iterrows():
                    try:
                        equities.loc[index] = updated_companies.loc[index]
                    except KeyError:
                        equities = pd.concat([equities, values])

                # Sort the index        
                equities = equities.sort_index()
                
                # Send to CSV
                equities.to_csv('database/equities.csv')
      - name: Commit files and log
        run: |
          git config --global user.name 'GitHub Action'
          git config --global user.email 'action@github.com'
          git add -A
          git checkout main
          git diff-index --quiet HEAD || git commit -am "Update database with new tickers"
          git push
      - name: Check run status
        if: steps.run.outputs.status != '0'
        run: exit "${{ steps.run.outputs.status }}"

  Update-Compression-Files:
    needs: Add-New-Ticker
    runs-on: ubuntu-latest
    steps:
      - name: checkout repo content
        uses: actions/checkout@v3
      - name: pull changes
        run: git pull https://${{secrets.PAT}}@github.com/JerBouma/FinanceDatabase.git main
      - name: setup python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - run: pip install -r requirements.txt
      - run: pip install financedatabase
      - run : pip install openpyxl
      - name: Update Compressions
        uses: jannekem/run-python-script-action@v1
        with:
          script: |
            import financedatabase as fd
            import pandas as pd

            cryptos = pd.read_csv('database/cryptos.csv')
            cryptos.to_csv('compression/cryptos.bz2', index=False, compression='bz2')

            currencies = pd.read_csv('database/currencies.csv')
            currencies.to_csv('compression/currencies.bz2', index=False, compression='bz2')

            equities = pd.read_csv('database/equities.csv')
            equities.to_csv('compression/equities.bz2', index=False, compression='bz2')

            etfs = pd.read_csv('database/etfs.csv')
            etfs.to_csv('compression/etfs.bz2', index=False, compression='bz2')

            funds = pd.read_csv('database/funds.csv')
            funds.to_csv('compression/funds.bz2', index=False, compression='bz2')

            indices = pd.read_csv('database/indices.csv')
            indices.to_csv('compression/indices.bz2', index=False, compression='bz2')

            moneymarkets = pd.read_csv('database/moneymarkets.csv')
            moneymarkets.to_csv('compression/moneymarkets.bz2', index=False, compression='bz2')
      - name: Commit files and log
        run: |
          git config --global user.name 'GitHub Action'
          git config --global user.email 'action@github.com'
          git add -A
          git checkout main
          git diff-index --quiet HEAD || git commit -am "Update Compression Files"
          git push
      - name: Check run status
        if: steps.run.outputs.status != '0'
        run: exit "${{ steps.run.outputs.status }}"

  Update-Categorization-Files:
      needs:  [Add-New-Ticker, Update-Compression-Files]
      runs-on: ubuntu-latest
      steps:
        - name: checkout repo content
          uses: actions/checkout@v3
        - name: pull changes
          run: git pull https://${{secrets.PAT}}@github.com/JerBouma/FinanceDatabase.git main
        - name: setup python
          uses: actions/setup-python@v4
          with:
            python-version: '3.10'
        - run: pip install -r requirements.txt
        - run: pip install financedatabase
        - name: Update categories
          uses: jannekem/run-python-script-action@v1
          with:
            script: |
              import financedatabase as fd
              import pandas as pd

              cryptos = pd.read_csv("database/cryptos.csv", index_col=0)
              cryptos_categories = {}
              for column in cryptos:
                  if column in ['name', 'summary']:
                      continue
                      
                  cryptos_categories[column] = cryptos[column].dropna().unique()
                  cryptos_categories[column].sort()
                  
              df_temp = pd.DataFrame.from_dict(cryptos_categories, orient='index').reset_index()
              df_temp.to_csv('compression/categories/cryptos_categories.gzip', index=False, compression='gzip')
                  
              currencies = pd.read_csv("database/currencies.csv", index_col=0)
              currencies_categories = {}
              for column in currencies:
                  if column in ['name']:
                      continue

                  currencies_categories[column] = currencies[column].dropna().unique()
                  currencies_categories[column].sort()

              df_temp = pd.DataFrame.from_dict(currencies_categories, orient='index').reset_index()
              df_temp.to_csv('compression/categories/currencies_categories.gzip', index=False, compression='gzip')
                  
              equities =  pd.read_csv("database/equities.csv", index_col=0)
              equities_categories = {}
              for column in equities:
                  if column in ['name', 'summary', 'website']:
                      continue
                      
                  equities_categories[column] = equities[column].dropna().unique()
                  equities_categories[column].sort()
                  
              df_temp = pd.DataFrame.from_dict(equities_categories, orient='index').reset_index()
              df_temp.to_csv('compression/categories/equities_categories.gzip', index=False, compression='gzip')
                  
              etfs = pd.read_csv("database/etfs.csv", index_col=0)
              etfs_categories = {}
              for column in etfs:
                  if column in ['name', 'summary']:
                      continue
                      
                  etfs_categories[column] = etfs[column].dropna().unique()
                  etfs_categories[column].sort()

              df_temp = pd.DataFrame.from_dict(etfs_categories, orient='index').reset_index()
              df_temp.to_csv('compression/categories/etfs_categories.gzip', index=False, compression='gzip')
                  
              funds = pd.read_csv("database/funds.csv", index_col=0)
              funds_categories = {}
              for column in funds:
                  if column in ['name', 'summary', 'manager_name', 'manager_bio']:
                      continue
                      
                  funds_categories[column] = funds[column].dropna().unique()
                  funds_categories[column].sort()
                  
              df_temp = pd.DataFrame.from_dict(funds_categories, orient='index').reset_index()
              df_temp.to_csv('compression/categories/funds_categories.gzip', index=False, compression='gzip')
                  
              indices = pd.read_csv("database/indices.csv", index_col=0)
              indices_categories = {}
              for column in indices:
                  if column in ['name']:
                      continue
                      
                  indices_categories[column] = indices[column].dropna().unique()
                  indices_categories[column].sort()
                  
              df_temp = pd.DataFrame.from_dict(indices_categories, orient='index').reset_index()
              df_temp.to_csv('compression/categories/indices_categories.gzip', index=False, compression='gzip')
                  
              moneymarkets = pd.read_csv("database/moneymarkets.csv", index_col=0)
              moneymarkets_categories = {}
              for column in moneymarkets:
                  if column in ['name']:
                      continue
                      
                  moneymarkets_categories[column] = moneymarkets[column].dropna().unique()
                  moneymarkets_categories[column].sort()
                  
              df_temp = pd.DataFrame.from_dict(moneymarkets_categories, orient='index').reset_index()
              df_temp.to_csv('compression/categories/moneymarkets_categories.gzip', index=False, compression='gzip')

        - name: Commit files and log
          run: |
            git config --global user.name 'GitHub Action'
            git config --global user.email 'action@github.com'
            git add -A
            git checkout main
            git diff-index --quiet HEAD || git commit -am "Update Categorization Files"
            git push
        - name: Check run status
          if: steps.run.outputs.status != '0'
          run: exit "${{ steps.run.outputs.status }}"

  Check-GICS-Categorisation:
    needs:  [Add-New-Ticker, Update-Compression-Files, Update-Categorization-Files]
    runs-on: ubuntu-latest
    steps:
      - name: checkout repo content
        uses: actions/checkout@v3
      - name: setup python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - run: pip install -r requirements.txt
      - run: pip install financedatabase
      - name: Check GICS Categorisation
        uses: jannekem/run-python-script-action@v1
        with:
          script: |
            import pandas as pd
            import json

            invalid_rows = pd.DataFrame()
            errors = []
            gics = json.load(open("compression/categories/gics_categories.json", "r"))
            equities = pd.read_csv("database/equities.csv", index_col=0)
            filtered_data = equities[equities['sector'].notna() & equities['industry_group'].notna() & equities['industry'].notna()]

            for index, row in filtered_data.iterrows():
                sector, industry_group, industry = row['sector'], row['industry_group'], row['industry']

                try:
                    # Search whether it can find the combination
                    gics[sector][industry_group][industry]
                except KeyError as error:
                    # If it can't, add to invalid_rows DataFrame
                    row['error'] = error
                    invalid_rows = pd.concat([invalid_rows, row], axis=1)


            if not invalid_rows.empty:
                invalid_rows = invalid_rows.T

                print("Invalid Rows for:")
                for index, row in invalid_rows.iterrows():
                    print(f"{index}: {row['error']}")
                
                raise ValueError("There are invalid sector, industry groups and/or industries found. "
                                 "Please check if it adheres to https://www.msci.com/our-solutions/indexes/gics")
