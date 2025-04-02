"Funds Module"

import pandas as pd

from .helpers import FinanceDatabase, FinanceFrame


class Funds(FinanceDatabase):
    """
    A Mutual Fund is a financial vehicle that pools assets from shareholders to
    invest in securities like stocks, bonds, money market instruments, and
    other assets. Mutual funds are operated by professional money managers, who
    allocate the fund's assets and attempt to produce capital gains or income for
    the fund's investors. A mutual fund's portfolio is structured and maintained
    to match the investment objectives stated in its prospectus.

    This class provides information about the funds available as well as the
    ability to select specific funds based on the category and/or family.
    """

    FILE_NAME = "funds.bz2"

    def select(
        self,
        category_group: str | None = None,
        category: str | None = None,
        family: str | None = None,
        currency: str | None = None,
        exchange: str | None = None,
        only_primary_listing: bool = False,
    ) -> pd.DataFrame:
        """
        Retrieve fund data based on specified criteria.

        This method allows you to retrieve data for specific funds based on a combination
        of category group, category, and family filters. You can also exclude
        exchanges from the search. If no input criteria are provided, it returns data for all funds.

        Args:
            category_group (str, optional):
                Specific category group to retrieve data for. If not provided, returns data for all category groups.
            category (str, optional):
                Specific category to retrieve data for. If not provided, returns data for all categories.
            family (str, optional):
                Specific family to retrieve data for. If not provided, returns data for all families.
            currency (str, optional):
                Specific currency to retrieve data for. If not provided, returns data for all currencies.
            exchange (str, optional):
                Specific exchange to retrieve data for. If not provided, returns data for all exchanges.
            only_primary_listing (bool, optional):
                Whether to only include the primary listing. If False, you will receive
                data for equities from different exchanges. Default is False.

        Returns:
            pd.DataFrame:
                A DataFrame containing fund data matching the specified input criteria.
        """
        funds = self.data.copy(deep=True)

        if category_group:
            category_group_lower = category_group.lower()
            options_lower = [
                option.lower()
                for option in self.show_options(selection="category_group")
            ]
            if category_group_lower not in options_lower:
                raise ValueError(
                    f"The category group '{category_group}' is not available in the database. "
                    "Please check the available category groups using the 'show_options' method."
                )
            funds = funds[funds["category_group"].str.lower() == category_group_lower]
        if category:
            category_lower = category.lower()
            options_lower = [
                option.lower() for option in self.show_options(selection="category")
            ]
            if category_lower not in options_lower:
                raise ValueError(
                    f"The category '{category}' is not available in the database. "
                    "Please check the available categories using the 'show_options' method."
                )
            funds = funds[funds["category"].str.lower() == category_lower]
        if family:
            family_lower = family.lower()
            options_lower = [
                option.lower() for option in self.show_options(selection="family")
            ]
            if family_lower not in options_lower:
                raise ValueError(
                    f"The family '{family}' is not available in the database. "
                    "Please check the available families using the 'show_options' method."
                )
            funds = funds[funds["family"].str.lower() == family_lower]
        if currency:
            currency_lower = currency.lower()
            options_lower = [
                option.lower() for option in self.show_options(selection="currency")
            ]
            if currency_lower not in options_lower:
                raise ValueError(
                    f"The currency '{currency}' is not available in the database. "
                    "Please check the available currencies using the 'show_options' method."
                )
            funds = funds[funds["currency"].str.lower() == currency_lower]
        if exchange:
            exchange_lower = exchange.lower()
            options_lower = [
                option.lower() for option in self.show_options(selection="exchange")
            ]
            if exchange_lower not in options_lower:
                raise ValueError(
                    f"The exchange '{exchange}' is not available in the database. "
                    "Please check the available exchanges using the 'show_options' method."
                )
            funds = funds[funds["exchange"].str.lower() == exchange_lower]
        if only_primary_listing:
            only_primary_listings_funds = funds[
                ~funds.index.str.contains(r"\.", na=False)
            ]
            if only_primary_listings_funds.empty:
                # If no primary listings are found, return all equities
                print(
                    "No primary listings found. Returning all funds matching your criteria."
                )
            else:
                # If primary listings are found, filter the equities DataFrame.
                funds = only_primary_listings_funds

        return FinanceFrame(funds)

    def show_options(
        self,
        selection: str | None = None,
        category_group: str | None = None,
        category: str | None = None,
        family: str | None = None,
        currency: str | None = None,
        exchange: str | None = None,
    ) -> pd.Series:
        """
        Retrieve all options for the specified selection.

        This method returns a series containing all available options for the specified
        selection, which can be one of the following: "currency", "category_group",
        "category", "family", "exchange".

        Args:
            selection (str):
                The selection you want to see the options for. Choose from:
                "currency", "category_group", "category", "family", "exchange".
            category_group (str, optional):
                Specific category group to retrieve data for. If not provided, returns data for all category groups.
            category (str, optional):
                Specific category to retrieve data for. If not provided, returns data for all categories.
            currency (str, optional):
                Specific currency to retrieve data for. If not provided, returns data for all currencies.
            exchange (str, optional):
                Specific exchange to retrieve data for. If not provided, returns data for all exchanges.

        Returns:
            pd.Series:
                A series with all options for the specified selection, sorted and without duplicates.
        """
        selection_values = [
            "currency",
            "category_group",
            "category",
            "family",
            "exchange",
        ]
        if selection is not None and selection not in selection_values:
            raise ValueError(
                f"The selection variable provided is not valid, "
                f"choose from {', '.join(selection_values)}"
            )

        funds = self.select(
            category_group=category_group,
            category=category,
            family=family,
            currency=currency,
            exchange=exchange,
            only_primary_listing=False,
        )

        return (
            {
                column: funds[column].dropna().sort_values().unique()
                for column in selection_values
            }
            if selection is None
            else funds[selection].dropna().sort_values().unique()
        )
