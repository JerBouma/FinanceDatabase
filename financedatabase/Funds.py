"Funds Module"

import numpy as np
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
        category_group: str | list | None = None,
        category: str | list | None = None,
        family: str | list | None = None,
        currency: str | list | None = None,
        exchange: str | list | None = None,
        only_primary_listing: bool = False,
    ) -> pd.DataFrame:
        """
        Retrieve fund data based on specified criteria.

        This method allows you to retrieve data for specific funds based on a combination
        of category group, category, and family filters. You can also exclude
        exchanges from the search. If no input criteria are provided, it returns data for all funds.

        Args:
            category_group (str | list, optional): Specific category group to filter funds.
                If not provided, returns data for all category groups.
            category (str | list, optional): Specific category to filter funds.
                If not provided, returns data for all categories.
            family (str | list, optional): Specific family to filter funds.
                If not provided, returns data for all families.
            currency (str | list, optional): Specific currency to filter funds.
                If not provided, returns data for all currencies.
            exchange (str | list, optional): Specific exchange to filter funds.
                If not provided, returns data for all exchanges.
            only_primary_listing (bool, optional): Whether to return only primary listings.
                Default is False, which returns all funds.

        Returns:
            pd.DataFrame:
                A DataFrame containing fund data matching the specified input criteria.
        """
        funds = self.data.copy(deep=True)

        if category_group:
            category_groups = (
                [category_group] if isinstance(category_group, str) else category_group
            )
            category_groups_lower = [
                category_group.lower() for category_group in category_groups
            ]
            options_lower = [
                option.lower()
                for option in self.show_options(selection="category_group")
            ]
            for category_group_lower, category_group_actual in zip(
                category_groups_lower, category_groups
            ):
                if category_group_lower not in options_lower:
                    raise ValueError(
                        f"The category group '{category_group_actual}' is not available in the database. "
                        "Please check the available category groups using the 'show_options' method."
                    )
            funds = funds[
                funds["category_group"].str.lower().isin(category_groups_lower)
            ]
        if category:
            categories = [category] if isinstance(category, str) else category
            categories_lower = [category.lower() for category in categories]
            options_lower = [
                option.lower() for option in self.show_options(selection="category")
            ]
            for category_lower, category_actual in zip(categories_lower, categories):
                if category_lower not in options_lower:
                    raise ValueError(
                        f"The category '{category_actual}' is not available in the database. "
                        "Please check the available categories using the 'show_options' method."
                    )
            funds = funds[funds["category"].str.lower().isin(categories_lower)]
        if family:
            families = [family] if isinstance(family, str) else family
            families_lower = [family.lower() for family in families]
            options_lower = [
                option.lower() for option in self.show_options(selection="family")
            ]
            for family_lower, family_actual in zip(families_lower, families):
                if family_lower not in options_lower:
                    raise ValueError(
                        f"The family '{family_actual}' is not available in the database. "
                        "Please check the available families using the 'show_options' method."
                    )
            funds = funds[funds["family"].str.lower().isin(families_lower)]
        if currency:
            currencies = [currency] if isinstance(currency, str) else currency
            currencies_lower = [currency.lower() for currency in currencies]
            options_lower = [
                option.lower() for option in self.show_options(selection="currency")
            ]
            for currency_lower, currency_actual in zip(currencies_lower, currencies):
                if currency_lower not in options_lower:
                    raise ValueError(
                        f"The currency '{currency_actual}' is not available in the database. "
                        "Please check the available currencies using the 'show_options' method."
                    )
            funds = funds[funds["currency"].str.lower().isin(currencies_lower)]
        if exchange:
            exchanges = [exchange] if isinstance(exchange, str) else exchange
            exchanges_lower = [exchange.lower() for exchange in exchanges]
            options_lower = [
                option.lower() for option in self.show_options(selection="exchange")
            ]
            for exchange_lower, exchange_actual in zip(exchanges_lower, exchanges):
                if exchange_lower not in options_lower:
                    raise ValueError(
                        f"The exchange '{exchange_actual}' is not available in the database. "
                        "Please check the available exchanges using the 'show_options' method."
                    )
            funds = funds[funds["exchange"].str.lower().isin(exchanges_lower)]

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
        category_group: str | list | None = None,
        category: str | list | None = None,
        family: str | list | None = None,
        currency: str | list | None = None,
        exchange: str | list | None = None,
    ) -> dict | np.ndarray:
        """
        Retrieve all options for the specified selection.

        This method returns a series containing all available options for the specified
        selection, which can be one of the following: "currency", "category_group",
        "category", "family", "exchange".

        Args:
            selection (str | None): The selection you want to see the options for.
                Choose from "currency", "category_group", "category", "family", or "exchange".
                If None, returns all options for all categories.
            category_group (str | list | None): Specific category group to filter options.
                If not provided, returns data for all category groups.
            category (str | list | None): Specific category to filter options.
                If not provided, returns data for all categories.
            family (str | list | None): Specific family to filter options.
                If not provided, returns data for all families.
            currency (str | list | None): Specific currency to filter options.
                If not provided, returns data for all currencies.
            exchange (str | list | None): Specific exchange to filter options.
                If not provided, returns data for all exchanges.

        Raises:
            ValueError: If the selection variable provided is not valid. Choose from:
                "currency", "category_group", "category", "family", or "exchange".

        Returns:
            dict | np.ndarray: A dictionary or array with all options for the specified selection.
                If selection is None, returns a dictionary with unique values for all fields.
                If selection is specified, returns an array of unique values for that field.
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
