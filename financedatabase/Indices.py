"""Indices Module"""

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
        category_group: str | None = None,
        category: str | None = None,
        currency: str | None = None,
        exchange: str | None = None,
    ) -> pd.DataFrame:
        """
        Select indices based on specified filter criteria.

        Returns all indices when no input is given and has the option to give
        a specific combination of indices based on the filters defined.

        Args:
            category_group (str, optional): Filter by category group.
                If provided, returns only indices matching this category group.
            category (str, optional): Filter by category.
                If provided, returns only indices matching this category.
            currency (str, optional): Filter by currency.
                If provided, returns only indices using this currency.
            exchange (str, optional): Filter by exchange.
                If provided, returns only indices listed on this exchange.

        Returns:
            pd.DataFrame: DataFrame containing indices data matching the specified criteria.

        Raises:
            ValueError: If any of the filter criteria provided are not found in the database.
        """
        indices = self.data.copy(deep=True)

        if category_group:
            category_group = category_group.lower()
            options_lower = [
                option.lower()
                for option in self.show_options(selection="category_group")
            ]
            if category_group not in options_lower:
                raise ValueError(
                    f"The category group '{category_group}' is not available in the database. "
                    "Please check the available category groups using the 'show_options' method."
                )
            indices = indices[indices["category_group"].str.lower() == category_group]
        if category:
            category = category.lower()
            options_lower = [
                option.lower() for option in self.show_options(selection="category")
            ]
            if category not in options_lower:
                raise ValueError(
                    f"The category '{category}' is not available in the database. "
                    "Please check the available categories using the 'show_options' method."
                )
            indices = indices[indices["category"].str.lower() == category]
        if currency:
            currency = currency.lower()
            options_lower = [
                option.lower() for option in self.show_options(selection="currency")
            ]
            if currency not in options_lower:
                raise ValueError(
                    f"The currency '{currency}' is not available in the database. "
                    "Please check the available currencies using the 'show_options' method."
                )
            indices = indices[indices["currency"].str.lower() == currency]
        if exchange:
            exchange = exchange.lower()
            options_lower = [
                option.lower() for option in self.show_options(selection="exchange")
            ]
            if exchange not in options_lower:
                raise ValueError(
                    f"The exchange '{exchange}' is not available in the database. "
                    "Please check the available exchanges using the 'show_options' method."
                )
            indices = indices[indices["exchange"].str.lower() == exchange]

        return FinanceFrame(indices)

    def show_options(
        self,
        selection: str | None = None,
        category_group: str | None = None,
        category: str | None = None,
        currency: str | None = None,
        exchange: str | None = None,
    ) -> pd.Series:
        """
        Show available options for the selection criteria.

        This method retrieves unique values for different selection fields,
        optionally filtered by other criteria.

        Args:
            selection (str, optional): The specific field to show options for.
                Choose from: "category_group", "category", "currency", and "exchange".
                If None, returns options for all fields.
            category_group (str, optional): Filter results by category group.
            category (str, optional): Filter results by category.
            currency (str, optional): Filter results by currency.
            exchange (str, optional): Filter results by exchange.

        Returns:
            pd.Series or dict: If selection is specified, returns a Series with all unique
                values for that field. If selection is None, returns a dictionary with
                Series of unique values for each field.

        Raises:
            ValueError: If the selection value is not one of the valid options.
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
