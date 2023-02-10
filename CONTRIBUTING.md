# CONTRIBUTING

First off all, thank you for taking the time to contribute (or at least read the Contributing Guidelines)! 🚀

The following is a set of guidelines for contributing to the FinanceDatabase. They are meant to guide you through how updating of the FinanceDatabase works and how you can contribute with little coding background as well.

## Working with Git & Pull Requests

Any new contribution will require a Pull Request to be made. In essence, all you really need is Git and basic understanding of how a Pull Request works. Find some resources that explain this well here:

- [Finding ways to contribute to open source on GitHub](https://docs.github.com/en/get-started/exploring-projects-on-github/finding-ways-to-contribute-to-open-source-on-github)
- [Set up Git](https://docs.github.com/en/get-started/quickstart/set-up-git)
- [Collaborating with pull requests](https://docs.github.com/en/github/collaborating-with-pull-requests)

It is important you have some sort of Code Editor (like VS Code) installed so that you can more easily browse the repository as well as have editing tools available to make changes to the Database as you see fit.

On every Pull Request, a couple of linters will run (see [here](https://github.com/JerBouma/FinanceDatabase/blob/main/.github/workflows/linting.yml)). These check the code and whether it matches specific coding formatting. This is entirely irrelevant for the database itself but keeps the code of the related package in check as well as any markdown changes.

Every now and then a JSON linter can also be ran with `npm i -g json-sort-cli` and then `sortjson Database`. This is lengthy and it is fine this doesn't happen on every Pull Request or merge. The purpose is to keep things consistent.

## Following the Workflow

After setting up Git, you can fork and pull the project in. Note that is bulky given the large collection of files.

1. Fork the Project ([more info](https://docs.github.com/en/get-started/quickstart/fork-a-repo))
    - **Using GitHub Desktop:** [Getting started with GitHub Desktop](https://docs.github.com/en/desktop/installing-and-configuring-github-desktop/getting-started-with-github-desktop) will guide you through setting up Desktop. Once Desktop is set up, you can use it to [fork the repo](https://docs.github.com/en/desktop/contributing-and-collaborating-using-github-desktop/cloning-and-forking-repositories-from-github-desktop)!
    - **Using the command line:** [Fork the repo](https://docs.github.com/en/github/getting-started-with-github/fork-a-repo#fork-an-example-repository) so that you can make your changes without affecting the original project until you're ready to merge them.
2. Pull the Repository Locally ([more info](https://github.com/git-guides/git-pull))
2. Create your own branch (`git checkout -b Contribution`)
3. Add your changes (`git add .`)
4. Commit your Changes (`git commit -m 'Improve the Database'`)
5. Push to your Branch (`git push origin Contribution`)
6. Open a Pull Request

## What can you do?

For much of the efforts, you do not need a background in programming and it just requires careful editing.

## Changing or Removing Tickers

In essence, all you really have to know is how to use `CTRL + F` (search) and `CTRL + H` (replace). Find a ticker that you think either needs updating or needs to be removed and then ensure that all entries are taken care of. As an example find the company Tesla below.

I start with finding all entries that include `"TSLA`. This results in the following hinting at all companies of Tesla from all different exchanges.

<img width="800" alt="Screenshot 2023-02-10 at 13 54 09" src="https://user-images.githubusercontent.com/46355364/218102302-d5d97956-7673-4616-92f9-ad8278327ba2.png">

Then I notice that the naming is sometimes off, in some cases it is referred to as `"TESLA INC"` whereas in others it is referred to as `"Tesla, Inc."`.

<img width="800" alt="Screenshot 2023-02-10 at 13 55 27" src="https://user-images.githubusercontent.com/46355364/218102391-a4213ca9-2baf-4269-a66f-9aa9300c64f9.png">

I decide to make the change to the code so that everything has the same naming, `"Tesla, Inc."`.

<img width="800" alt="Screenshot 2023-02-10 at 13 55 42" src="https://user-images.githubusercontent.com/46355364/218102418-5a7ecfac-535c-4709-ba71-846c628da6d2.png">

This is a mere example but it shows the ease of contribution whereas these small changes can already make a huge difference!

## Adding Tickers

For any additional tickers to the FinanceDatabase please always include the following template:

```json
"TSLA": {
  "city": "Palo Alto",
  "country": "United States",
  "currency": "USD",
  "exchange": "NMS",
  "industry": "Auto Manufacturers",
  "long_name": "Tesla, Inc.",
  "market": "us_market",
  "market_cap": "Mega Cap",
  "sector": "Consumer Cyclical",
  "short_name": "Tesla, Inc.",
  "state": "CA",
  "summary": "Tesla, Inc. designs, develops, manufactures, leases, and sells electric vehicles, and energy generation and storage systems in the United States, China, and internationally. The company operates in two segments, Automotive, and Energy Generation and Storage. The Automotive segment offers electric vehicles, as well as sells automotive regulatory credits. It provides sedans and sport utility vehicles through direct and used vehicle sales, a network of Tesla Superchargers, and in-app upgrades; and purchase financing and leasing services. This segment is also involved in the provision of non-warranty after-sales vehicle services, sale of used vehicles, retail merchandise, and vehicle insurance, as well as sale of products through its subsidiaries to third party customers; services for electric vehicles through its company-owned service locations, and Tesla mobile service technicians; and vehicle limited warranties and extended service plans. The Energy Generation and Storage segment engages in the design, manufacture, installation, sale, and leasing of solar energy generation and energy storage products, and related services to residential, commercial, and industrial customers and utilities through its website, stores, and galleries, as well as through a network of channel partners. This segment also offers service and repairs to its energy product customers, including under warranty; and various financing options to its solar customers. The company was formerly known as Tesla Motors, Inc. and changed its name to Tesla, Inc. in February 2017. Tesla, Inc. was founded in 2003 and is headquartered in Palo Alto, California.",
  "website": "http://www.tesla.com",
  "zipcode": "94304"
},
```

If in any case you are not able to acquire data for a specific category, enter `null` so that it is clear that there is no data available. Furthermore, make sure that you include the tickers as well in:

- The correct "Country", "Sector" and "Industry" including their total lists (e.g. "United States.json" or "_Healthcare.json")
- The total list of Equities ("Equities List.json", "Equities Part 1.json" and "Equities Part 2.json")

Find an example below where I added "New Company, Inc" to the "Equities Part 2.json"

<img width="800" alt="image" src="https://user-images.githubusercontent.com/46355364/218105400-10ba3178-d1ce-440e-b5c4-c66580a5b6ef.png">

To find more information about each category:

- "city": select the city where the company's headquarters is located.
- "country": select the country where the company's headquarters is located.
- "currency": select the denominated currency of this specific ticker (based on exchange). See currency options [here](https://github.com/JerBouma/FinanceDatabase/blob/main/Database/Categories/currencies_options.json)
- "exchange": select the exchange the company is listed at.
- "industry": select the industry that belongs to the company. Pick an option from [this list](https://github.com/JerBouma/FinanceDatabase/blob/main/Database/Categories/equities_industries.json)
- "long_name": enter the full company name.
- "market": enter which market the company belongs to, this is related to the exchange as well.
- "market_cap": based on [market cap categorization](https://www.investopedia.com/investing/market-capitalization-defined/) define the market cap.
- "sector" select the sector that belongs to the company. Pick an option from [this list](https://github.com/JerBouma/FinanceDatabase/blob/main/Database/Categories/equities_sectors.json)
- "short_name": enter the short abbrevation of the company name.
- "state": if applicable, select a state in the United States.
- "summary": enter a brief company description, explaining the purpose of the company.
- "zipcode": if applicable, enter the zipcode.

This sometimes differs between asset classes but should be self explanatory. **There is room for improvement in automization for some of this. Feel free to leave suggestions about this as well.**

## Updating the Package

The files in the `financedatabase` folder are used to build the related package that allows you to search the database effectively. If you have any suggestions or improvements for this package, feel free to propose this in a Pull Request.
