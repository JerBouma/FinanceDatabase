"""Indices Module"""

import numpy as np
import pandas as pd

from .helpers import FinanceDatabase, FinanceFrame


class Indices(FinanceDatabase):
    """
    An index is a method to track the performance of a group of assets in a standardized way.
    Indexes typically measure the performance of a basket of securities intended to
    replicate a certain area of the market. These could be constructed as a broad-based
    index that captures the entire market, such as the Standard & Poor's 500 Index or
    Dow Jones Industrial Average (DJIA), or more specialized such as indexes that
    track a particular industry or segment such as the Russell 2000 Index,
    which tracks only small-cap stocks.

    This class provides information about the indices available as well as the
    ability to select specific indices based on various criteria.
    """

    FILE_NAME = "indices.bz2"

    def select(
        self,
        category_group: str | list | None = None,
        category: str | list | None = None,
        currency: str | list | None = None,
        exchange: str | list | None = None,
    ) -> pd.DataFrame:
        """
        Select indices based on specified filter criteria.

        Returns all indices when no input is given and has the option to give
        a specific combination of indices based on the filters defined.

        Args:
            category_group (str | list, optional): Filter by category group.
                Default is None, which returns all category groups.
            category (str | list, optional): Filter by category.
                Default is None, which returns all categories.
            currency (str | list, optional): Filter by currency.
                Default is None, which returns all currencies.
            exchange (str | list, optional): Filter by exchange.
                Default is None, which returns all exchanges.

        Raises:
            ValueError: If the specified category group, category, currency, or exchange
                is not available in the database.

        Returns:
            pd.DataFrame: DataFrame containing indices data matching the specified criteria.
        """
        indices = self.data.copy(deep=True)

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
            indices = indices[
                indices["category_group"].str.lower().isin(category_groups_lower)
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
            indices = indices[indices["category"].str.lower().isin(categories_lower)]
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
            indices = indices[indices["currency"].str.lower().isin(currencies_lower)]
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
            indices = indices[indices["exchange"].str.lower().isin(exchanges_lower)]

        return FinanceFrame(indices)

    def show_options(
        self,
        selection: str | None = None,
        category_group: str | list | None = None,
        category: str | list | None = None,
        currency: str | list | None = None,
        exchange: str | list | None = None,
    ) -> dict | np.ndarray:
        """
        Show available options for the selection criteria.

        This method retrieves unique values for different selection fields,
        optionally filtered by other criteria.

        Args:
            selection (str, optional): The specific field to show options for.
                Choose from: "category_group", "category", "currency", and "exchange".
                If None, returns options for all fields.
            category_group (str | list, optional): Filter by category group.
                Default is None, which returns all category groups.
            category (str | list, optional): Filter by category.
                Default is None, which returns all categories.
            currency (str | list, optional): Filter by currency.
                Default is None, which returns all currencies.
            exchange (str | list, optional): Filter by exchange.
                Default is None, which returns all exchanges.

        Raises:
            ValueError: If the specified selection is not valid or if the specified
                category group, category, currency, or exchange is not available in the database.

        Returns:
            dict | np.ndarray: A dictionary or array with all options for the specified selection.
                If selection is None, returns a dictionary with unique values for all fields.
                If selection is specified, returns an array of unique values for that field.
        """
        selection_values = ["category_group", "category", "currency", "exchange"]

        if selection is not None and selection not in selection_values:
            raise ValueError(
                f"The selection variable provided is not valid, "
                f"choose from {', '.join(selection_values)}"
            )

        indices = self.select(
            category_group=category_group,
            category=category,
            currency=currency,
            exchange=exchange,
        )

        return (
            {
                column: indices[column].dropna().sort_values().unique()
                for column in selection_values
            }
            if selection is None
            else indices[selection].dropna().sort_values().unique()
        )
