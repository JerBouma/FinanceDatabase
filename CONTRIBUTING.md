# CONTRIBUTING
First off all, thank you for taking the time to contribute (or at least read the Contributing Guidelines)! 🚀

The FinanceDatabase serves the role of providing anyone with any type of financial product categorisation entirely for free. To be able to achieve this, the FinanceDatabase relies on involvement from the community to update, edit and remove tickers over time. This is made easy enough that anyone, even with a lack of coding experience can contribute because of the generation of CSV files that can be manually edited.

The following is a set of guidelines for contributing to the FinanceDatabase. They are meant to guide you through how updating of the FinanceDatabase works and how you can contribute with little coding background as well.

1. [Updating the Database](#updating-the-database)
2. [Ways to Help Out](#ways-to-help-out)
3. [Category Definitions](#category-definitions)
4. [Advanced (Developers)](#advanced-developers)
    1. [Working with Git & Pull Requests](#working-with-git--pull-requests)
    2. [Following the Workflow](#following-the-workflow)
    3. [Updating the Package](#updating-the-package)

# Updating the Database
When you are just looking to make edits or know your way around Excel well, I'd recommend downloading the CSV files with the following link:
___

<b><div align="center"><a href="https://download-directory.github.io/?url=https%3A%2F%2Fgithub.com%2FJerBouma%2FFinanceDatabase%2Ftree%2Fmain%2Fdatabase">Download the the CSV files of the FinanceDatabase here</a></div></b>
___

Then, follow these steps to update the CSV files accordingly.

| Download & Update the CSV Files  | Create a Database Update Issue or Pull Request on GitHub |
| ------------- | ------------- |
| You can help out tremendously by updating one of the CSV files. This can be done through Excel and by making use of CTRL + F to find and edit symbols and their data efficiently. <p></p> Note that **Equities, ETFs and Funds** are split into individual files per exchange (e.g. `database/equities/NMS.csv` for NASDAQ, `database/etfs/AMS.csv` for Amsterdam Exchange). The other asset classes (`cryptos`, `currencies`, `indices`, `moneymarkets`) remain single files. <p></p> Carefully go through the cells making sure you're following the descriptions as mentioned [here](#category-definitions). After having saved the files, you're ready to go to the next step. <p></p> |  Once you've made your update, you can go [here](https://github.com/JerBouma/FinanceDatabase/issues/new/choose) and select `Database Update`. Then, within the textbox enter a description of what you changed and then drag and drop your updated CSV files. From here on, I'll make sure to update the Database with your updates which will be visible within the database within minutes.<p></p>Alternatively you can also make a Pull Request as described [here](#advanced-developers). This is mostly meant for Developers that know their way around Git. <p></p> |
| <img width="2500" alt="Updating CSV Files - FinanceDatabase" src="https://user-images.githubusercontent.com/46355364/221357112-aac7bdc4-a605-4ecb-8337-1dd309f2e1a8.png">  | <img width="2500" alt="GitHub Issue - FinanceDatabase" src="https://user-images.githubusercontent.com/46355364/220197736-7453a9bb-d8bb-4569-ab84-b84e456f753e.png"> |

It is also possible to load in the files directly into e.g. a Jupyter Notebook and make the edits how you like by using packages like pandas to search. It could be that certain naming is off that you want to correct automatically for all tickers that match the criteria or perhaps you want to fill sectors and industries automatically.

**Equities, ETFs and Funds** are stored as per-exchange files inside subdirectories. For a single exchange file, load it this way:

- If remote: `pd.read_csv("https://raw.githubusercontent.com/JerBouma/FinanceDatabase/main/database/equities/NMS.csv", index_col=0)`
- If locally: `pd.read_csv("database/equities/NMS.csv", index_col=0)`

For the other asset classes (`cryptos`, `currencies`, `indices`, `moneymarkets`), the files remain single CSVs:

- If remote: `pd.read_csv("https://github.com/JerBouma/FinanceDatabase/blob/main/database/cryptos.csv?raw=true", delimiter=",", index_col=0)`
- If locally: `pd.read_csv("database/cryptos.csv", delimiter=",", index_col=0)`

Change the asset class name to any of the file names as found [here](https://github.com/JerBouma/FinanceDatabase/tree/main/database). Then, once you have made your changes you can use `df.to_csv('database/equities/NMS.csv', sep=',')` to export back to the CSV format (saving back to the correct exchange file). From here on, follow the above steps again or create a Pull Request as described [here](#advanced-developers).

## Validating Identifiers

Developers can audit populated ISIN, CUSIP, FIGI, composite FIGI, and
share-class FIGI fields in the source CSV files:

```bash
uv run python scripts/validate_identifiers.py
```

The command reports the file, line, symbol, value, and validation error for
each invalid identifier without changing any files. Standardized validation is
provided by the development dependency
[`python-stdnum`](https://pypi.org/project/python-stdnum/). It validates the
[ISO 6166](https://www.iso.org/standard/78502.html) ISIN check digit,
[CUSIP check digit](https://www.cusip.com/pdf/news/CUSIP-ACommonLanguageForEfficientMarkets_2022.pdf),
and [FIGI format and check digit](https://www.openfigi.com/docs/figi-check-digit.pdf).
For valid US and Canadian values, it also checks that the ISIN embeds the
accompanying CUSIP. The command exits with status 1 when it finds invalid or
inconsistent values, which also makes it suitable for automated checks.

After reviewing the report, pass `--apply` to repair deterministic formatting
damage and clear other identifiers with invalid formats or checksums.
Canonical values returned by `python-stdnum` are repaired automatically. A
`.0` suffix is removed from any supported identifier when the resulting value
passes that identifier's validation. If leading zeros were also lost from a
CUSIP, it is repaired only when its numeric value matches the CUSIP embedded in
an independently valid US or Canadian ISIN. Instrument rows, valid identifiers,
unrelated fields, quoting, line endings, and row ordering are preserved:

```bash
uv run python scripts/validate_identifiers.py --apply
```

Invalid ISIN and FIGI values without a deterministic repair are cleared.
Unresolved CUSIPs and ISIN-CUSIP inconsistencies between two independently
valid identifiers are not changed automatically because format and checksum
validation cannot determine whether a CUSIP belongs to the stated instrument.
Specific CSV files or directories can be supplied as positional arguments.
These checks detect malformed identifiers and transcription errors; they do
not confirm that an identifier was officially issued or belongs to the stated
instrument.

# Ways to Help Out

There are a variety of ways you can help out, these can be:

| Topic  | Description |
| ------------- | ------------- |
| Adding ISIN, CIK, FIGI, CUSIP, SEDOL and more | Ideally, every single ticker has multiple codes from ISIN, CIK, FIGI, CUSIP and SEDOL and also how platforms like Bloomberg, Factset, Eikon Refinitiv and OpenBB represent their tickers. |
| Testing Symbols |  Understand whether symbols and companies still exist by Googling and if not, removing them from the database. Tickers could stop existing due to name changes (like Facebook to META), going bankrupt or merging with other firms. Indices, ETFs, Funds, Moneymarkets and Cryptocurrencies could be updated in a similar fashion. |
| Updating Categories | If the value for e.g. "Sector" or "Industry" (equities) or "Category" (ETFs and Funds) is missing or seems to be incorrect, figure out what would fit for that ticker and update accordingly. |
| Update Identical Symbols | ASML, ASML.DE and ASML.AS are all the same company but are listed on different exchanges. Do they all contain the same information? If not, feel free to update the information accordingly. Here you can use ASML (the ticker without the dot) as base. |
| Update Naming | If the name doesn't properly represent the company or is inconsistent with other results (e.g. TESLA INC, TESLA CORPORATION, Tesla Inc.)

These are just a few examples but feel free to proceed how you'd like! **Any help is much appreciated!**

## Category Definitions

For Equities, these are the categories. Other asset classes follow a similar lay-out, see [examples](https://github.com/JerBouma/FinanceDatabase/blob/main/examples.ipynb).

- **symbol**: set the symbol of the company.
- **name**: enter the full company name.
- **summary**: enter a brief company description, explaining the purpose of the company.
- **currency**: select the denominated currency of this specific ticker (based on exchange).
- **sector**: select the sector that belongs to the company (follows GICS)
- **industry_group**: select the industry group that belongs to the company (follows GICS).
- **industry**: select the industry that belongs to the company (follows GICS).
- **exchange**: select the exchange the company is listed at.
- **market**: enter which market the company belongs to, this is related to the exchange as well.
- **country**: select the country where the company's headquarters is located.
- **state**: if applicable, select a state in the United States.
- **city**: select the city where the company's headquarters is located.
- **zipcode**: if applicable, enter the zipcode.
- **website**: if applicable, enter the website.
- **market_cap**: based on [market cap categorization](https://www.investopedia.com/investing/market-capitalization-defined/) define the market cap.

If in any case you are not able to acquire data for a specific category, keep the field blank so that it is clear that there is no data available. For any of these options, make sure you use an existing category so that it remains compact. For example, the sectors, industry groups and industries loosely approximate to the [The Global Industry Classification Standard (GICS®)](https://www.msci.com/our-solutions/indexes/gics) as created by MSCI. No actual data is collected from this source and this database merely tries to reflect the sectors and industries as best as possible. This is completely done through manual curation. The actual datasets as curated by MSCI have not been used in the development of any part of this database and remains the most up to date, paid, solution. Other categorizations are entirely developed by the author and can freely be changed.

# Advanced (Developers)
If you know your way around Git and GitHub this is the preferred way of providing updates. In any case, I still provide information regarding how to set up Git.

## Working with Git & Pull Requests

Any new contribution preferably goes via a Pull Request. In essence, all you really need is Git and basic understanding of how a Pull Request works. Find some resources that explain this well here:

- [Finding ways to contribute to open source on GitHub](https://docs.github.com/en/get-started/exploring-projects-on-github/finding-ways-to-contribute-to-open-source-on-github)
- [Set up Git](https://docs.github.com/en/get-started/quickstart/set-up-git)
- [Collaborating with pull requests](https://docs.github.com/en/github/collaborating-with-pull-requests)

On every Pull Request, a couple of linters will run (see [here](https://github.com/JerBouma/FinanceDatabase/blob/main/.github/workflows/) as well as categorization and compression linters). The linters check the code and whether it matches specific coding formatting. This is entirely irrelevant for the database itself but keeps the code of the related package in check as well as any markdown changes. The categorization and compression actions are very relevant for the database as it makes it much easier and faster to read data.

## Following the Workflow

After setting up Git, you can fork and pull the project in.

1. Fork the Project ([more info](https://docs.github.com/en/get-started/quickstart/fork-a-repo))
    - **Using GitHub Desktop:** [Getting started with GitHub Desktop](https://docs.github.com/en/desktop/installing-and-configuring-github-desktop/getting-started-with-github-desktop) will guide you through setting up Desktop. Once Desktop is set up, you can use it to [fork the repo](https://docs.github.com/en/desktop/contributing-and-collaborating-using-github-desktop/cloning-and-forking-repositories-from-github-desktop)!
    - **Using the command line:** [Fork the repo](https://docs.github.com/en/github/getting-started-with-github/fork-a-repo#fork-an-example-repository) so that you can make your changes without affecting the original project until you're ready to merge them.
2. Pull the Repository Locally ([more info](https://github.com/git-guides/git-pull))
2. Create your own branch (`git checkout -b feature/contribution`)
3. Add your changes (`git add .`)
4. Commit your Changes (`git commit -m 'Improve the Database'`)
5. Push to your Branch (`git push origin feature/contribution`)
6. Open a Pull Request

The database files resides in the `Database` folder whereas the files that are loaded with the package are inside the `compression` folder. Refer to the [Updating the Database](#updating-the-database) section what is required to update the data files.

## Updating the Package

The files in the `financedatabase` folder are used to build the related package that allows you to search the database effectively. If you have any suggestions or improvements for this package, feel free to propose this in a Pull Request.
