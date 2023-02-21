# CONTRIBUTING

First off all, thank you for taking the time to contribute (or at least read the Contributing Guidelines)! 🚀

The FinanceDatabase serves the role of providing anyone with any type of financial product categorisation entirely for free. To be able to achieve this, the FinanceDatabase relies on involvement from the community to update, edit and remove tickers over time. This is made easy enough that anyone, even with a lack of coding experience can contribute because of the generation of CSV files that can be manually edited.

The following is a set of guidelines for contributing to the FinanceDatabase. They are meant to guide you through how updating of the FinanceDatabase works and how you can contribute with little coding background as well. It is divided up into [User](#user) and [Developer](#developer) in which the main difference is the experience with GitHub's Pull Requests and Git in general. 

# User
If you only got as far as the installation process and have little experience with Git, this section is for you. The code files of the database are the ones below.

___

<b><div align="center"><a href="https://download-directory.github.io/?url=https%3A%2F%2Fgithub.com%2FJerBouma%2FFinanceDatabase%2Ftree%2Fmain%2FDatabasDownload">Download the the CSV files of the FinanceDatabase here</a>.</div></b>
___

## Updating the Database

| Download & Update the CSV Files  | Create a Database Update Issue on GitHub |
| ------------- | ------------- |
| You can help out tremendelously by updating one of the CSV files. This can be done through Excel and by making use of CTRL + F (and CTRL + H) to replace cells quickly. <p></p> Carefully go through the cells making sure you're following the descriptions as mentioned [here](#categories). After having saved the files, you're ready to go to the next step. <p></p> |  Once you've made your update, you can go [here](https://github.com/JerBouma/FinanceDatabase/issues/new/choose) and select `Database Update`. Then, within the textbox enter a description of what you changed and then drag and drop your updated CSV files. <p></p> From here on, I'll make sure to update the Database with your updates! <p></p> |
| <img width="1500" alt="Updating CSV Files - FinanceDatabase" src="https://user-images.githubusercontent.com/46355364/220196479-a3581da7-132b-44a4-b44f-90d989e8c807.png">  | <img width="1500" alt="GitHub Issue - FinanceDatabase" src="https://user-images.githubusercontent.com/46355364/220197736-7453a9bb-d8bb-4569-ab84-b84e456f753e.png"> |

## Categories

For Equities, these are the categories. Other asset classes follow a similar lay-out, see [examples](https://github.com/JerBouma/FinanceDatabase/blob/main/examples.ipynb).

- **symbol**: set the symbol of the company.
- **short_name**: enter the short abbreviation of the company name.
- **long_name**: enter the full company name.
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

If in any case you are not able to acquire data for a specific category, keep the field blank so that it is clear that there is no data available. For any of these options, make sure you use an existing category so that it remains compact. For example, the sectors, industry groups and industries adhere to the [GICS categorisation](https://www.msci.com/our-solutions/indexes/gics).

# Developer
If you know your way around Git and GitHub this is the preferred way of providing updates. In any case, I still provide information regarding how to set up Git.

## Working with Git & Pull Requests

Any new contribution preferably goes via a Pull Request. In essence, all you really need is Git and basic understanding of how a Pull Request works. Find some resources that explain this well here:

- [Finding ways to contribute to open source on GitHub](https://docs.github.com/en/get-started/exploring-projects-on-github/finding-ways-to-contribute-to-open-source-on-github)
- [Set up Git](https://docs.github.com/en/get-started/quickstart/set-up-git)
- [Collaborating with pull requests](https://docs.github.com/en/github/collaborating-with-pull-requests)

On every Pull Request, a couple of linters will run (see [here](https://github.com/JerBouma/FinanceDatabase/blob/main/.github/workflows/linting.yml)). These check the code and whether it matches specific coding formatting. This is entirely irrelevant for the database itself but keeps the code of the related package in check as well as any markdown changes.

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

The database itself resides in the `Database` folder. Refer to the [User](#user) section what is required to update the data files.

## Updating the Package

The files in the `financedatabase` folder are used to build the related package that allows you to search the database effectively. If you have any suggestions or improvements for this package, feel free to propose this in a Pull Request.
