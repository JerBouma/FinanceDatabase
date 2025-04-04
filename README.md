<img src="https://user-images.githubusercontent.com/46355364/220746807-669cdbc1-ac67-404c-b0bb-4a3d67d9931f.jpg" alt="Logo">

[![GitHub Sponsors](https://img.shields.io/badge/Sponsor_this_Project-grey?logo=github)](https://github.com/sponsors/JerBouma)
[![Buy Me a Coffee](https://img.shields.io/badge/Buy_Me_a_Coffee-grey?logo=buymeacoffee)](https://www.buymeacoffee.com/jerbouma)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-grey?logo=Linkedin&logoColor=white)](https://www.linkedin.com/in/boumajeroen/)
[![Documentation](https://img.shields.io/badge/Documentation-grey?logo=readme)](https://www.jeroenbouma.com/projects/financedatabase)
[![Supported Python Versions](https://img.shields.io/pypi/pyversions/financedatabase)](https://pypi.org/project/financedatabase/)
[![PYPI Version](https://img.shields.io/pypi/v/financedatabase)](https://pypi.org/project/financedatabase/)
[![PYPI Downloads](https://static.pepy.tech/badge/financedatabase/month)](https://pepy.tech/project/financedatabase)

| **Call for Contributors to the FinanceDatabase**    |
|:------------------------------------------------------:|
| The **FinanceDatabase** serves the role of providing anyone with any type of financial product categorization entirely for free. To be able to achieve this, the FinanceDatabase relies on involvement from the community to add, edit and remove tickers over time. This is made easy enough that anyone, even with a lack of coding experience can contribute because of the usage of CSV files that can be manually edited with ease.
**I'd like to invite you to go to the [Contributing Guidelines](https://github.com/JerBouma/FinanceDatabase/blob/main/CONTRIBUTING.md) to understand how you can help. Thank you!** |

As a private investor, the sheer amount of information that can be found on the internet is rather daunting. Trying to understand what type of companies or ETFs are available is incredibly challenging with there being millions of companies and derivatives available on the market. Sure, the most traded companies and ETFs can quickly be found simply because they are known to the public (for example, Microsoft, Tesla, S&P500 ETF or an All-World ETF). However, what else is out there is often unknown.

**This database tries to solve that**. It features 300.000+ symbols containing Equities, ETFs, Funds, Indices, Currencies, Cryptocurrencies and Money Markets. It therefore allows you to obtain a broad overview of sectors, industries, types of investments and much more.

The aim of this database is explicitly _not_ to provide up-to-date fundamentals or stock data as those can be obtained with ease (with the help of this database) by using the [Finance Toolkit 🛠️](https://github.com/JerBouma/FinanceToolkit). Instead, it gives insights into the products that exist in each country, industry and sector and gives the most essential information about each product. With this information, you can analyse specific areas of the financial world and/or find a product that is hard to find. See for examples on how you can combine this database, and the earlier mentioned packages the section [Usage](#usage).

Some key statistics of the database:

| Product           | Quantity   | Sectors    | Industries    | Countries | Exchanges |
| ----------------- | ---------- | ---------- | ------------- | --------- | --------- |
| Equities          | 158.429    | 12         | 63            | 111       | 83        | 
| ETFs              | 36.786     | 295        | 22            | 111       | 53        |
| Funds             | 57.881     | 1541       | 52            | 111       | 34        |

| Product           | Quantity  | Category              |
| ----------------- | --------- | --------------------- |
| Currencies        | 2.556     | 175 Currencies        |
| Cryptocurrencies  | 3.367     | 352 Cryptocurrencies  |
| Indices           | 91.183    | 64 Exchanges          |
| Money Markets     | 1.367     | 3 Exchanges           |

The Finance Database is used within or referenced by:

<a href="https://algotrading101.com/learn/financedatabase-python-guide/"><img width="200" height="100" alt="AlgoTrading" src="https://github-production-user-asset-6210df.s3.amazonaws.com/46355364/265290727-4c113348-45fc-45fe-afb5-e043b738ee94.png"></a>
<a href="https://twitter.com/pyquantnews/status/1576185955677077504?lang=en"><img width="200" height="100" alt="PyQuantNews" src="https://github-production-user-asset-6210df.s3.amazonaws.com/46355364/265290754-8c9025fb-3830-4f41-95fd-e5e6d0f84758.png"></a>
<a href="https://alpha2phi.medium.com/investment-analysis-finance-database-61f47ecfe7ca"><img width="200" height="100" alt="Medium" src="https://github-production-user-asset-6210df.s3.amazonaws.com/46355364/265290765-dfbd0f4c-85eb-4de6-adba-345cb5189f31.png"></a>

___

# Installation

Before installation, consider starring the project on GitHub which helps others find the project as well.

<img width="1353" alt="image" src="https://github.com/JerBouma/FinanceDatabase/assets/46355364/4132edde-72f9-4e32-adfe-8872207f46ff">

To install the FinanceDatabase it simply requires the following:

```
pip install financedatabase -U
```

Then within Python use:

```python
import financedatabase as fd
```

# Usage
This section explains in detail how the database can be queried with the related `financedatabase` package. Note that examples here are purposely cut off to a maximum of 10 entries due to the sheer size of the database. Furthermore, the summary column is also taken out for readability. For the full detailed results, see the Notebook [here](https://www.jeroenbouma.com/projects/financedatabase/getting-started). Let's start by importing the package:

```python
import financedatabase as fd
```

Initialization of each asset class is only required <u>once</u>. It is therefore important you save the class to a variable so that you can query the database much quicker. A simple example is shown below.

```python
equities = fd.Equities()

equities.select()
```

A sample of the output is shown below:

| symbol   | name                           | currency   | sector                 | industry_group                                 | industry                               | exchange   | market                    | country       | state   | city                | zipcode    | website                          | market_cap   | isin         | cusip     | figi         | composite_figi   | shareclass_figi   |
|:---------|:-------------------------------|:-----------|:-----------------------|:-----------------------------------------------|:---------------------------------------|:-----------|:--------------------------|:--------------|:--------|:--------------------|:-----------|:---------------------------------|:-------------|:-------------|:----------|:-------------|:-----------------|:------------------|
| PMTA.DU  | PTC Inc.                       | EUR        | Information Technology | Software & Services                            | Software                               | DUS        | Dusseldorf Stock Exchange | United States | MA      | Boston              | 2210       | http://www.ptc.com               | Large Cap    | US69370C1009 | 69370C100 | BBG000FC6SC5 | BBG000FC5PS5     | BBG001S6DNK6      |
| VAW.F    | VAALCO Energy, Inc.            | EUR        | Energy                 | Energy                                         | Oil, Gas & Consumable Fuels            | FRA        | Frankfurt Stock Exchange  | United States | TX      | Houston             | 77042      | http://www.vaalco.com            | Micro Cap    | US91851C2017 | 91851C201 | BBG000CN15Y5 | BBG000CN15F6     | BBG001S76ZS7      |
| ORC.DE   | Oracle Corporation             | EUR        | Information Technology | Software & Services                            | Software                               | GER        | XETRA                     | United States | TX      | Austin              | 78741      | http://www.oracle.com            | Mega Cap     | US68389X1054 | 68389X105 | BBG000C0RY38 | BBG000C0RWW0     | BBG001S5SJG6      |
| PAYX     | Paychex, Inc.                  | USD        | Industrials            | Commercial & Professional Services             | Professional Services                  | NMS        | NASDAQ Global Select      | United States | NY      | Rochester           | 14625-2396 | http://www.paychex.com           | Large Cap    | US7043261079 | 704326107 | BBG000BQT1J5 | BBG000BQSQ38     | BBG001S5V135      |
| RI2A.F   | Rigel Pharmaceuticals, Inc.    | EUR        | Health Care            | Pharmaceuticals, Biotechnology & Life Sciences | Biotechnology                          | FRA        | Frankfurt Stock Exchange  | United States | CA      | South San Francisco | 94080      | http://www.rigel.com             | Small Cap    | US7665596034 | 766559603 | BBG000BKZNR4 | BBG000BKZNC0     | BBG001SD33Z0      |
| PGEN     | Precigen, Inc.                 | USD        | Health Care            | Pharmaceuticals, Biotechnology & Life Sciences | Biotechnology                          | NMS        | NASDAQ Global Select      | United States | MD      | Germantown          | 20876      | http://www.precigen.com          | Small Cap    | US74017N1054 | 74017N105 | BBG004TDDJ32 | BBG000QL8VH9     | BBG001SSB3T5      |
| GOGO     | Gogo Inc.                      | USD        | Communication Services | Telecommunication Services                     | Diversified Telecommunication Services | NMS        | NASDAQ Global Select      | United States | IL      | Chicago             | 60606      | http://www.gogoair.com           | Small Cap    | US38046C1099 | 38046C109 | BBG002CN8Y71 | BBG002CN8XN5     | BBG002CN8YD4      |
| CRK      | Comstock Resources, Inc.       | USD        | Energy                 | Energy                                         | Oil, Gas & Consumable Fuels            | NYQ        | New York Stock Exchange   | United States | TX      | Frisco              | 75034      | http://www.comstockresources.com | Mid Cap      | US2057683029 | 205768302 | BBG000DNBMJ3 | BBG000DNBK89     | BBG001S8FX55      |
| OIS      | Oil States International, Inc. | USD        | Energy                 | Energy                                         | Energy Equipment & Services            | NYQ        | New York Stock Exchange   | United States | TX      | Houston             | 77002      | http://www.oilstatesintl.com     | Small Cap    | US6780261052 | 678026105 | BBG000BDDQ06 | BBG000BDDN94     | BBG001S7WK56      |
| CVLC.BE  | Vale S.A.                      | EUR        | Materials              | Materials                                      | Metals & Mining                        | BER        | Berlin Stock Exchange     | Brazil        | RJ      | Rio De Janeiro      | 22250-145  | http://www.vale.com              | Large Cap    | US91912E1055 | 9.19E+109 | BBG000HCJTN5 | BBG000HCJNQ5     | BBG001S7RS91      |


With `show_options` all possible options are given per column. **This is useful as it doesn't require loading the larger data files.** For example, obtaining all options for equities is done as follows.

```python
fd.show_options("equities")
```

This returns all available options for each column.

```text
{'currency': array(['ARS', 'AUD', 'BRL', 'CAD', 'CHF', 'CLP', 'CNY', 'COP', 'CZK',
        'DKK', 'EUR', 'GBP', 'HKD', 'HUF', 'IDR', 'ILA', 'ILS', 'INR',
        'ISK', 'JPY', 'KES', 'KRW', 'LKR', 'MXN', 'MYR', 'NOK', 'NZD',
        'PEN', 'PHP', 'PLN', 'QAR', 'RUB', 'SAR', 'SEK', 'SGD', 'THB',
        'TRY', 'TWD', 'USD', 'ZAC', 'ZAR'], dtype=object),
 'sector': array(['Communication Services', 'Consumer Discretionary',
        'Consumer Staples', 'Energy', 'Financials', 'Health Care',
        'Industrials', 'Information Technology', 'Materials',
        'Real Estate', 'Utilities'], dtype=object),
 'industry_group': array(['Automobiles & Components', 'Banks', 'Capital Goods',
        'Commercial & Professional Services',
        'Consumer Durables & Apparel', 'Consumer Services',
        'Diversified Financials', 'Energy', 'Food & Staples Retailing',
        'Food, Beverage & Tobacco', 'Health Care Equipment & Services',
        'Household & Personal Products', 'Insurance', 'Materials',
        'Media & Entertainment',
        'Pharmaceuticals, Biotechnology & Life Sciences', 'Real Estate',
        'Retailing', 'Semiconductors & Semiconductor Equipment',
        'Software & Services', 'Technology Hardware & Equipment',
        'Telecommunication Services', 'Transportation', 'Utilities'],
       dtype=object)}
```

As the equities database has already been loaded in, it is also possible to use a similar functionality from within the class as follows. The main difference is that this functionality allows you to see the options based on a specific filtering. For example.

```python
equities.show_options(country='Netherlands')
```

This shows a more concise list of parameters given the focus on the Netherlands.

```text
{'currency': array(['ARS', 'AUD', 'BRL', 'CHF', 'CZK', 'EUR', 'GBP', 'ILA', 'MXN',
        'NOK', 'RUB', 'USD', 'ZAC'], dtype=object),
 'sector': array(['Communication Services', 'Consumer Discretionary',
        'Consumer Staples', 'Energy', 'Financials', 'Health Care',
        'Industrials', 'Information Technology', 'Materials',
        'Real Estate', 'Utilities'], dtype=object),
 'industry_group': array(['Automobiles & Components', 'Banks', 'Capital Goods',
        'Commercial & Professional Services',
        'Consumer Durables & Apparel', 'Consumer Services',
        'Diversified Financials', 'Energy', 'Food & Staples Retailing',
        'Food, Beverage & Tobacco', 'Health Care Equipment & Services',
        'Household & Personal Products', 'Insurance', 'Materials',
        'Media & Entertainment',
        'Pharmaceuticals, Biotechnology & Life Sciences', 'Real Estate',
        'Retailing', 'Semiconductors & Semiconductor Equipment',
        'Software & Services', 'Technology Hardware & Equipment',
        'Telecommunication Services', 'Transportation', 'Utilities'],
       dtype=object)}
```

Or only showing one specific parameter.

```python
equities.show_options(
    selection='industry',
    sector='Financials',
    country='Netherlands')
```

Which returns:

```text
array(['Banks', 'Capital Markets', 'Consumer Finance',
       'Diversified Financial Services', 'Insurance'], dtype=object)
```

Given this information, it then becomes possible to filter the database based on the parameters you are interested in. For example, if you are interested 'Insurance' companies in the 'Netherlands' you can use the following. Note that I omit the `sector` here, given that the selection I make is on a deeper level and therefore it is a given that the sector is 'Financials'.

```python
equities.select(
    country='Netherlands',
    industry='Insurance',
)
```

This returns a small selection of companies on all exchanges the companies are listed on.


| symbol    | name               | currency   | sector     | industry_group   | industry   | exchange   | market                   | country     |   state | city      | zipcode   | website              | market_cap   | isin         |   cusip | figi         | composite_figi   | shareclass_figi   |
|:----------|:-------------------|:-----------|:-----------|:-----------------|:-----------|:-----------|:-------------------------|:------------|--------:|:----------|:----------|:---------------------|:-------------|:-------------|--------:|:-------------|:-----------------|:------------------|
| A16.F     | ASR Nederland N.V. | EUR        | Financials | Insurance        | Insurance  | FRA        | Frankfurt Stock Exchange | Netherlands |     nan | Utrecht   | 3584 BA   | http://www.asrnl.com | Mid Cap      | NL0011872643 |     nan | BBG00D2VFV96 | BBG00D2VFV78     | BBG00CWZ0HK0      |
| A1EG34.SA | Aegon N.V.         | BRL        | Financials | Insurance        | Insurance  | SAO        | Bovespa Soma             | Netherlands |     nan | The Hague | 2591 TV   | http://www.aegon.com | Mid Cap      | NL0000303709 |     nan | nan          | nan              | nan               |
| AEG       | Aegon N.V.         | USD        | Financials | Insurance        | Insurance  | NYQ        | New York Stock Exchange  | Netherlands |     nan | The Hague | 2591 TV   | http://www.aegon.com | Large Cap    | NL0000303709 |     nan | BBG000CKQTN4 | BBG000CKQSN6     | BBG001S6Y6M8      |
| AEGOF     | Aegon N.V.         | USD        | Financials | Insurance        | Insurance  | PNK        | OTC Bulletin Board       | Netherlands |     nan | The Hague | 2591 TV   | http://www.aegon.com | Mid Cap      | NL0000303709 |     nan | nan          | nan              | nan               |
| AEND.DE   | Aegon N.V.         | EUR        | Financials | Insurance        | Insurance  | GER        | XETRA                    | Netherlands |     nan | The Hague | 2591 TV   | http://www.aegon.com | Mid Cap      | NL0000303709 |     nan | BBG000DJK260 | BBG000DJHZF1     | BBG001S5V8R4      |

You'll see that the same company can appear multiple times. This is because by default all exchanges are shown. There are two methods to focus on one entry:

- Use the `only_primary_listing` parameter. This will only show the primary listing of each company. This is useful mostly if you are looking into the US exchanges.
- Use the `exchange` or `market` parameter. This will allow you to filter on a specific exchange or market. This is useful when you not necessarily looking into US exchanges and are already filtering on a specific country.

For example, filtering on the Netherlands it makes sense to select a Dutch exchange as well. This is for example the exchange "AMS" or the market "Euronext Amsterdam". This will already give you a much smaller selection.

```python
equities.select(
    country='Netherlands',
    industry='Insurance',
    market='Euronext Amsterdam',
)
```

This gives the following three companies (not shortenend):

| symbol   | name               | currency   | sector     | industry_group   | industry   | exchange   | market             | country     |   state | city      | zipcode   | website                 | market_cap   | isin         |   cusip | figi         | composite_figi   | shareclass_figi   |
|:---------|:-------------------|:-----------|:-----------|:-----------------|:-----------|:-----------|:-------------------|:------------|--------:|:----------|:----------|:------------------------|:-------------|:-------------|--------:|:-------------|:-----------------|:------------------|
| AGN.AS   | Aegon N.V.         | EUR        | Financials | Insurance        | Insurance  | AMS        | Euronext Amsterdam | Netherlands |     nan | The Hague | 2591 TV   | http://www.aegon.com    | Mid Cap      | NL0000303709 |     nan | BBG000JN9DM6 | BBG000JN9C93     | BBG001S5V8R4      |
| ASRNL.AS | ASR Nederland N.V. | EUR        | Financials | Insurance        | Insurance  | AMS        | Euronext Amsterdam | Netherlands |     nan | Utrecht   | 3584 BA   | http://www.asrnl.com    | Mid Cap      | NL0011872643 |     nan | BBG00CWZ0HG5 | BBG00CWZ0HF6     | BBG00CWZ0HK0      |
| NN.AS    | NN Group N.V.      | EUR        | Financials | Insurance        | Insurance  | AMS        | Euronext Amsterdam | Netherlands |     nan | The Hague | 2595 AS   | http://www.nn-group.com | Large Cap    | nan          |     nan | nan          | nan              | nan               |

Given that the Netherlands is a relatively small country, it is not uncommon for the list to become small quick. For example, the same selection for the United States is already much larger, also utilizing the `only_primary_listing` parameter.

```python
equities.select(
    country='United States',
    industry='Insurance',
    only_primary_listing=True
)
```

While not immediately obvious in this shortenend output, it returns about 180 different companies.


| symbol   | name                             | currency   | sector     | industry_group   | industry   | exchange   | market                  | country       | state   | city            | zipcode    | website                    | market_cap   | isin         | cusip     | figi         | composite_figi   | shareclass_figi   |
|:---------|:---------------------------------|:-----------|:-----------|:-----------------|:-----------|:-----------|:------------------------|:--------------|:--------|:----------------|:-----------|:---------------------------|:-------------|:-------------|:----------|:-------------|:-----------------|:------------------|
| AFL      | Aflac Incorporated               | USD        | Financials | Insurance        | Insurance  | NYQ        | New York Stock Exchange | United States | GA      | Columbus        | 31999      | http://www.aflac.com       | Large Cap    | US0010551028 | 1055102   | BBG000BBBRC7 | BBG000BBBNC6     | BBG001S5NGJ4      |
| AJG      | Arthur J. Gallagher & Co.        | USD        | Financials | Insurance        | Insurance  | NYQ        | New York Stock Exchange | United States | IL      | Rolling Meadows | 60008-4050 | http://www.ajg.com         | Large Cap    | US3635761097 | 363576109 | BBG000BBHZK4 | BBG000BBHXQ3     | BBG001S5NKC2      |
| AMSF     | AMERISAFE, Inc.                  | USD        | Financials | Insurance        | Insurance  | NMS        | NASDAQ Global Select    | United States | LA      | Deridder        | 70634      | http://www.amerisafe.com   | Small Cap    | US03071H1005 | 03071H100 | BBG000Q0JWB7 | BBG000Q0JJQ0     | BBG001SDH7B2      |
| BRO      | Brown & Brown, Inc.              | USD        | Financials | Insurance        | Insurance  | NYQ        | New York Stock Exchange | United States | FL      | Daytona Beach   | 32114      | http://www.bbinsurance.com | Large Cap    | US1152361010 | 115236101 | BBG000BWSJ77 | BBG000BWSGF4     | BBG001S5XFN0      |
| CINF     | Cincinnati Financial Corporation | USD        | Financials | Insurance        | Insurance  | NMS        | NASDAQ Global Select    | United States | OH      | Fairfield       | 45014-5141 | http://www.cinfin.com      | Large Cap    | US1720621010 | 172062101 | BBG000BFPVV3 | BBG000BFPK65     | BBG001S5PTM0      |

For any of the variables, it is also possible to provide a list instead. Which means that it will return all entries that match any of the variables. As an example, the queries above can be combined into one.

    
```python
equities.select(
    country=['Netherlands', 'United States'],
    industry='Insurance',
    market=['Euronext Amsterdam', 'Nordic Growth Market', 'OTC Bulletin Board',
            'New York Stock Exchange', 'NASDAQ Global Select', 'NYSE MKT',
            'NASDAQ Capital Market']
)
```

This returns a larger selection of companies given the increased number of countries and markets.


| symbol   | name                          | currency   | sector     | industry_group   | industry   | exchange   | market                  | country       | state   | city       | zipcode    | website                  | market_cap   | isin         |   cusip | figi         | composite_figi   | shareclass_figi   |
|:---------|:------------------------------|:-----------|:-----------|:-----------------|:-----------|:-----------|:------------------------|:--------------|:--------|:-----------|:-----------|:-------------------------|:-------------|:-------------|--------:|:-------------|:-----------------|:------------------|
| AAME     | Atlantic American Corporation | USD        | Financials | Insurance        | Insurance  | NGM        | Nordic Growth Market    | United States | GA      | Atlanta    | 30319-3054 | http://www.atlam.com     | Nano Cap     | nan          |     nan | nan          | nan              | nan               |
| ACMT     | ACMAT Corporation             | USD        | Financials | Insurance        | Insurance  | PNK        | OTC Bulletin Board      | United States | CT      | Farmington | 6032       | http://www.acmatcorp.com | Nano Cap     | nan          |     nan | nan          | nan              | nan               |
| ACMTA    | ACMAT Corporation             | USD        | Financials | Insurance        | Insurance  | PNK        | OTC Bulletin Board      | United States | CT      | Farmington | 6032       | http://www.acmatcorp.com | Nano Cap     | nan          |     nan | nan          | nan              | nan               |
| AEG      | Aegon N.V.                    | USD        | Financials | Insurance        | Insurance  | NYQ        | New York Stock Exchange | Netherlands   | nan     | The Hague  | 2591 TV    | http://www.aegon.com     | Large Cap    | NL0000303709 |     nan | BBG000CKQTN4 | BBG000CKQSN6     | BBG001S6Y6M8      |
| AEGOF    | Aegon N.V.                    | USD        | Financials | Insurance        | Insurance  | PNK        | OTC Bulletin Board      | Netherlands   | nan     | The Hague  | 2591 TV    | http://www.aegon.com     | Mid Cap      | NL0000303709 |     nan | nan          | nan              | nan               |


In case the current categorization doesn't lead to the results you are looking for, it is possible to use the `search` parameter. This allows you to filter on any column in the database via a custom string. This means that if the word or sentence you input is found somewhere in the column you select, it will return the result. 

By default the result will not be case sensitive but you can adjust this by setting `case_sensitive=True`. You can also filter the index (`symbol` column) by using `index` as shown below. Just like the `select` function, you can also provide lists here.

```python
equities.search(
    summary=["Robotics", "Education"],
    industry_group="Equipment",
    market='Frankfurt',
    index=".F"
)
```

This returns instruments that are listed on the Frankfurt Stock Exchange, are in an industry group with the word "Equipment" and have either "Robotics" or "Education" in the summary column. The `index` parameter is used to filter on the symbol column, which in this case is ".F". The filtering on the index is an alternative way of finding the exchange or market you are looking for.

| symbol   | name                                                        | currency   | sector                 | industry_group                   | industry                                       | exchange   | market                   | country       | state   | city          | zipcode    | website                        | market_cap   | isin         | cusip     | figi         | composite_figi   | shareclass_figi   |
|:---------|:------------------------------------------------------------|:-----------|:-----------------------|:---------------------------------|:-----------------------------------------------|:-----------|:-------------------------|:--------------|:--------|:--------------|:-----------|:-------------------------------|:-------------|:-------------|:----------|:-------------|:-----------------|:------------------|
| 109.F    | Castlight Health, Inc.                                      | EUR        | Health Care            | Health Care Equipment & Services | Health Care Providers & Services               | FRA        | Frankfurt Stock Exchange | United States | CA      | San Francisco | 94105      | http://www.castlighthealth.com | Small Cap    | nan          | nan       | nan          | nan              | nan               |
| 1KT.F    | Keysight Technologies, Inc.                                 | EUR        | Information Technology | Technology Hardware & Equipment  | Electronic Equipment, Instruments & Components | FRA        | Frankfurt Stock Exchange | United States | CA      | Santa Rosa    | 95403-1738 | http://www.keysight.com        | Large Cap    | US49338L1035 | 49338L103 | BBG007DJZFD2 | BBG007DJZFC3     | BBG0059FN820      |
| 1N1.F    | Nanalysis Scientific Corp.                                  | EUR        | Information Technology | Technology Hardware & Equipment  | Electronic Equipment, Instruments & Components | FRA        | Frankfurt Stock Exchange | Canada        | AB      | Calgary       | T2E 7C3    | http://www.nanalysis.com       | Nano Cap     | nan          | nan       | nan          | nan              | nan               |
| 1YO.F    | Yangtze Optical Fibre And Cable Joint Stock Limited Company | EUR        | Information Technology | Technology Hardware & Equipment  | Communications Equipment                       | FRA        | Frankfurt Stock Exchange | China         | nan     | Wuhan         | 430073     | http://www.yofc.com            | Small Cap    | nan          | nan       | nan          | nan              | nan               |
| 1ZU.F    | The Pennant Group, Inc.                                     | EUR        | Health Care            | Health Care Equipment & Services | Health Care Equipment & Supplies               | FRA        | Frankfurt Stock Exchange | United States | ID      | Eagle         | 83616      | http://pennantgroup.com        | Small Cap    | US70805E1091 | 7.08E+113 | BBG00QJ35K78 | BBG00QJ35K69     | BBG00P33SZ15      |

Lastly, the Finance Database has a direct integration with the [Finance Toolkit](https://github.com/JerBouma/FinanceToolkit) making it possible to do financial analysis on the companies you've found in the Finance Database. Returning to the earlier example of the 3 insurance companies in the Netherlands, it becomes possible to load these into the Finance Toolkit with the `to_toolkit` functionality. 

To be able to get started, you need to obtain an API Key from FinancialModelingPrep. This is used to gain access to 30+ years of financial statement both annually and quarterly. Note that the Free plan is limited to 250 requests each day, 5 years of data and only features companies listed on US exchanges.

___ 

<b><div align="center">Obtain an API Key from FinancialModelingPrep <a href="https://www.jeroenbouma.com/fmp" target="_blank">here</a>.</div></b>
___

Then you can go ahead and run the following code, changing the `API_KEY` to your own API Key.


```python
API_KEY = "FINANCIAL_MODELING_PREP_API_KEY"

dutch_insurance_companies = equities.select(
    country='Netherlands',
    industry='Insurance',
    market='Euronext Amsterdam',
)

toolkit = dutch_insurance_companies.to_toolkit(
    api_key=API_KEY
)
```

With this integration, I can now access some of the most important financial metrics for these companies. Let's start simple with historical data.

```python
toolkit.get_historical_data()
```

Which returns, selecting only "ASRNL.AS" as an example:

| date       |   Open |   High |   Low |   Close |   Adj Close |   Volume |   Dividends |   Return |   Volatility |   Excess Return |   Excess Volatility |   Cumulative Return |
|:-----------|-------:|-------:|------:|--------:|------------:|---------:|------------:|---------:|-------------:|----------------:|--------------------:|--------------------:|
| 2025-03-31 |  52.86 |  52.98 | 52.56 |   52.98 |       52.98 |   547650 |           0 |  -0.0049 |       0.0175 |         -0.0474 |              0.0206 |              4.2726 |
| 2025-04-01 |  53.22 |  53.6  | 52.98 |   53.44 |       53.44 |   486098 |           0 |   0.0087 |       0.0175 |         -0.0329 |              0.0206 |              4.3097 |
| 2025-04-02 |  53.18 |  53.58 | 52.7  |   53.3  |       53.3  |   485768 |           0 |  -0.0026 |       0.0175 |         -0.0446 |              0.0206 |              4.2984 |
| 2025-04-03 |  52.32 |  53.22 | 52.18 |   52.42 |       52.42 |   567242 |           0 |  -0.0165 |       0.0175 |         -0.057  |              0.0206 |              4.2274 |
| 2025-04-04 |  52    |  52.5  | 49.45 |   50.4  |       50.4  |   485024 |           0 |  -0.0385 |       0.0175 |         -0.0775 |              0.0206 |              4.0645 |

And now let's make it more advanced by automatically calculating 60+ financial ratios for each. **This is just a small snippet of what is available within the Finance Toolkit, see for more information the GitHub page of the Finance Toolkit [here](https://github.com/JerBouma/FinanceToolkit) or the example Notebook [here](https://www.jeroenbouma.com/projects/financetoolkit/getting-started).**

```python
toolkit.ratios.collect_all_ratios()
```

Which returns, selecting only "ASRNL.AS" as an example with a few ratios:

|                                 |   2015 |   2016 |   2017 |   2018 |   2019 |   2020 |   2021 |   2022 |   2023 |   2024 |
|:--------------------------------|-------:|-------:|-------:|-------:|-------:|-------:|-------:|-------:|-------:|-------:|
| Interest Coverage Ratio         | 4.0535 | 4.2287 | 6.6142 | 5.152  | 3.2238 | 2.2508 | 3.1188 | 3.0962 | 4.1177 | 0      |
| Income Before Tax Profit Margin | 0.1078 | 0.1265 | 0.1843 | 0.159  | 0.1515 | 0.1104 | 0.1231 | 0.1783 | 0.1089 | 0.0701 |
| Effective Tax Rate              | 0.1923 | 0.2351 | 0.195  | 0.2334 | 0.1983 | 0.2075 | 0.2233 | 0.2196 | 0.2181 | 0.2647 |
| Return on Capital Employed      | 0.0183 | 0.0192 | 0.0235 | 0.0176 | 0.0218 | 0.0145 | 0.0205 | 0.0205 | 0.0283 | 0.0382 |
| Net Income per EBT              | 0.7908 | 0.7603 | 0.7985 | 0.743  | 0.7917 | 0.7798 | 0.768  | 0.7705 | 0.774  | 0.6972 |
| EBT to EBIT Ratio               | 0.7469 | 0.7611 | 0.8472 | 0.801  | 0.7654 | 0.7023 | 0.7628 | 0.6654 | 0.3289 | 0.2389 |
| EBIT to Revenue                 | 0.1327 | 0.163  | 0.2107 | 0.1803 | 0.1885 | 0.1481 | 0.1553 | 0.2564 | 0.3196 | 0.2567 |
| Debt-to-Assets Ratio            | 0.0442 | 0.0605 | 0.0504 | 0.0546 | 0.094  | 0.1172 | 0.0923 | 0.068  | 0.0856 | 0.0771 |

All of these methods are also available for the other asset classes. The only difference is that the class name changes and the available columns. For example, for ETFs you would use `fd.ETFs()` instead of `fd.Equities()` and the `select` option has parameters such as `category_group` and `family` instead.


```python
etfs = fd.ETFs()

etfs.select(
    category_group='Fixed Income'
)
```

This gives you results like the following:

| symbol   | name               | currency   | category_group   | category               | family                    | exchange   |
|:---------|:-------------------|:-----------|:-----------------|:-----------------------|:--------------------------|:-----------|
| ^BND     | VANGUARD BD IDX FD | USD        | Fixed Income     | Investment Grade Bonds | Vanguard Asset Management | NIM        |
| ^BNDX    | VANGUARD CHARLOTTE | USD        | Fixed Income     | Investment Grade Bonds | Vanguard Asset Management | NIM        |
| ^VCIT    | VANGUARD SCOTTSDAL | USD        | Fixed Income     | Corporate Bonds        | Vanguard Asset Management | NIM        |
| ^VCLT    | VANGUARD SCOTTSDAL | USD        | Fixed Income     | Corporate Bonds        | Vanguard Asset Management | NIM        |
| ^VCSH    | VANGUARD SCOTTSDAL | USD        | Fixed Income     | Corporate Bonds        | Vanguard Asset Management | NIM        |

This also translates to the available options, for example let's select `fd.Indices()` instead.

```python
indices = fd.Indices()

indices.show_options()
```
A sample of the output is shown below:

```text
{'category_group': array(['Alternatives', 'Cash', 'Commodities', 'Communication Services',
        'Consumer Discretionary', 'Consumer Staples', 'Currencies',
        'Derivatives', 'Energy', 'Equities', 'Financials', 'Fixed Income',
        'Health Care', 'Industrials', 'Information Technology',
        'Materials', 'Real Estate', 'Utilities'], dtype=object),
 'category': array(['Alternative', 'Blend', 'Bonds', 'Cash', 'Commercial Real Estate',
        'Commodities Broad Basket', 'Communications',
        'Consumer Discretionary', 'Consumer Staples', 'Corporate Bonds',
        'Currencies', 'Derivatives', 'Developed Markets',
        'Emerging Markets', 'Energy', 'Equities', 'Factors', 'Financials',
        'Frontier Markets', 'Government Bonds', 'Growth', 'Health Care',
        'High Yield Bonds', 'Industrials',
        'Inflation-Protected Securities', 'Investment Grade Bonds',
        'Large Cap', 'Materials', 'Micro Cap', 'Mid Cap',
        'Money Market Instruments', 'Municipal Bonds', 'REITs',
        'Real Estate Development', 'Real Estate Services',
        'Residential Real Estate', 'Small Cap', 'Technology', 'Trading',
        'Treasury Bonds', 'Utilities', 'Value'], dtype=object)}
```

And lastly, both the `search` and `to_toolkit` metrics also apply to each of the asset classes, using `fd.Funds()` and `fd.Cryptos()` respectively. For example, let's find the funds that focus around pension plans.

```python
funds = fd.Funds()

funds.search(summary='Pension')
```

A sample of the output is shown below:


| symbol       | name                              | currency   | category_group   | category   | family                           | exchange   |
|:-------------|:----------------------------------|:-----------|:-----------------|:-----------|:---------------------------------|:-----------|
| 0P000017AH.F | OpenBank Renta Variable Europa PP | EUR        | Equities         | Equities   | Santander Asset Management SGIIC | FRA        |
| 0P000017AJ.F | Alcal Futuro Uno PP   | EUR        | Financials       | Allocation | Caser Pensiones EGFP             | FRA        |
| 0P0000189U.F | Caser Julio 2021 PP Acc           | EUR        | Financials       | Bonds      | Caser Pensiones EGFP             | FRA        |
| 0P000018ML.F | Cajamar Renta Variable PP         | EUR        | Equities         | Equities   | Cajamar Vida Se. y Re.           | FRA        |
| 0P000019H0.F | Bestinver Global PP               | EUR        | Financials       | Blend      | Bestinver Pensiones              | FRA        |

And for Cryptos, let's collect the historical data of Ethereum in multiple currencies.

```python
cryptos = fd.Cryptos()

eth_cryptos = cryptos.select(
    cryptocurrency='ETH'
)

cryptos_toolkit = eth_cryptos.to_toolkit(
    api_key=API_KEY,
    start_date='2020-01-01'
)

cryptos_toolkit.get_historical_data(period='quarterly')
```

A sample of the output is shown below, focussig on ETH-BTC:

| Date   |   Open |   High |    Low |   Close |   Adj Close |   Volume |   Dividends |   Return |   Volatility |   Excess Return |   Excess Volatility |   Cumulative Return |
|:-------|-------:|-------:|-------:|--------:|------------:|---------:|------------:|---------:|-------------:|----------------:|--------------------:|--------------------:|
| 2024Q2 | 0.0559 | 0.0558 | 0.0554 |  0.0554 |      0.0554 |   108145 |           0 |   0.0992 |       0.159  |          0.0558 |              0.144  |              2.6763 |
| 2024Q3 | 0.0406 | 0.0407 | 0.0403 |  0.0405 |      0.0405 |   169579 |           0 |  -0.269  |       0.1433 |         -0.307  |              0.1445 |              1.9565 |
| 2024Q4 | 0.0358 | 0.0365 | 0.036  |  0.0362 |      0.0362 |   291317 |           0 |  -0.1062 |       0.1857 |         -0.1519 |              0.1679 |              1.7488 |
| 2025Q1 | 0.0221 | 0.0222 | 0.0217 |  0.0219 |      0.0219 |   119665 |           0 |  -0.395  |       0.1813 |         -0.4375 |              0.1639 |              1.058  |
| 2025Q2 | 0.0218 | 0.0217 | 0.0216 |  0.0216 |      0.0216 |   195229 |           0 |  -0.0137 |       0.1415 |         -0.053  |              0.1361 |              1.0435 |


# Questions & Answers
In this section you can find answers to commonly asked questions. In case the answer to your question is not here, 
consider creating an [Issue](https://github.com/JerBouma/FinanceDatabase/issues).

> **How is the data obtained?**

The data is an aggregation of various publicly available sources. I strictly maintain the rule that all data in this database must be freely accessible to everyone. Data requiring API keys or paid subscriptions is never included. Information that companies charge for is typically owned and maintained by those companies, making public sharing of such data a violation of their Terms of Service (ToS). However, publicly available data can be freely shared (read more about the legality of web scraping [here](https://techcrunch.com/2022/04/18/web-scraping-legal-court/?guccounter=1&guce_referrer=aHR0cHM6Ly93d3cuZ29vZ2xlLmNvbS8&guce_referrer_sig=AQAAAJRZe3F6wCbuO_n8PJ9JtAHpOY4dF2gA_tO0gJF2PhfWUueUcRQataJwNS9FZlp9rH8f8_aiCBfA2v7wlHyXyVLUfMrca4kq0_m6CYSvK7eMk9zuEhnXJOvE0lrHWXSPTtL-lHP8UJD4SyWTpQ2BnCNx-kv3mG7GGn_G_3SGVvhP)). This database will always remain <u>completely free</u>.

> **What categorization method is used?**

The categorization for Equities is based on a loose approximation of GICS (Global Industry Classification Standard). This database attempts to reflect sectors and industries as accurately as possible through manual curation, without collecting any actual data from MSCI's proprietary sources. The official GICS datasets curated by MSCI remain the most up-to-date, paid solution and were not used in developing any part of this database. All other categorizations in the database are independently developed and can be freely modified.

> **How can I contribute?**

Please see the [Contributing Guidelines](https://github.com/JerBouma/FinanceDatabase/blob/main/CONTRIBUTING.md). Thank you!

> **How can I find out which countries, sectors and/or industries exist within the database without needing to check the database manually?**

For this you can use the `show_options` function from the package attached to this database within a specific asset class or on a higher level without requiring any data to be loaded beforehand. See [Usage](#usage) for more information.

> **When I try collect data I notice that not all tickers return output, why is that?**

Some tickers are merely holdings of companies and therefore do not really have any data attached to them. Therefore, it makes sense that not all tickers return data. If you are still in doubt, search the ticker on Google to see if there is really no data available. If you can't find anything about the ticker, consider updating the database by visiting the [Contributing Guidelines](https://github.com/JerBouma/FinanceDatabase/blob/main/CONTRIBUTING.md).

> **How does the database handle changes to companies over time - like symbol/exchange migration, mergers, bankruptcies, or symbols getting reused?**

For American exchanges, the database automatically updates every Sunday using data from [this repository](https://github.com/rreichel3/US-Stock-Symbols). This process includes checks for market cap changes and updates asset classifications accordingly. Delisted tickers are intentionally retained for historical research purposes.

While professional financial data services like Bloomberg charge over $25,000 annually for comprehensive market data maintenance, this database relies on community contributions. When companies outside American exchanges undergo changes (migrations, mergers, bankruptcies), we depend on community members to identify and update these entries.

Most companies don't change so rapidly that the database becomes obsolete - major changes like Facebook's rebrand to META are quickly incorporated. Even when companies go bankrupt, their ticker information remains valuable for historical analysis.

If you notice outdated information, please consider contributing through the [Contributing Guidelines](https://github.com/JerBouma/FinanceDatabase/blob/main/CONTRIBUTING.md).

# Contributions

This section is meant to thank those that contributed to the project. Looking to contribute as well? Have a look [here](https://github.com/JerBouma/FinanceDatabase/blob/main/CONTRIBUTING.md).

| User              | Contribution |
| ----------------- | ------------ | 
| [desaijimmy](https://github.com/desaijimmy)        | Made changes to Equities dataset including the Split of Daimler to Mercedes-Benz and Daimler Trucks |
| [nindogo](https://github.com/nindogo)        | Introduced a variety of new equities from the Nairobi Securities Exchange and introduced the country Kenya into the dataset. |
| [colin99d](https://github.com/colin99d)        | Helped in the conversion of the Finance Database package to Object-Orientated, making the code much more efficient. |

# Contact
If you have any questions about the FinanceDatabase or would like to share with me what you have been working on, feel free to reach out to me via:

- **Website**: https://jeroenbouma.com/
- **LinkedIn:** https://www.linkedin.com/in/boumajeroen/
- **Email:** jer.bouma@gmail.com

f you'd like to support my efforts, either help me out via the [Contributing Guidelines](https://github.com/JerBouma/FinanceDatabase/blob/main/CONTRIBUTING.md) or [Buy me a Coffee](https://www.buymeacoffee.com/jerbouma).

[![Star History Chart](https://api.star-history.com/svg?repos=JerBouma/FinanceDatabase&type=Date)](https://star-history.com/#JerBouma/FinanceDatabase&Date)
