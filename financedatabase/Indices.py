"""Indices Module"""

import numpy as np

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
    FIELDS = {
        "category_group": ("category group", "category groups"),
        "category": ("category", "categories"),
        "currency": ("currency", "currencies"),
        "exchange": ("exchange", "exchanges"),
        "mic": ("MIC", "MICs"),
    }

    def select(
        self,
        category_group: str | list | None = None,
        category: str | list | None = None,
        currency: str | list | None = None,
        exchange: str | list | None = None,
        mic: str | list | None = None,
        as_pandas: bool = True,
    ) -> FinanceFrame:
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
            mic (str | list, optional): Filter by ISO 10383 MIC code.
                Default is None, which returns all MIC codes.
            as_pandas (bool, optional): Return a pandas DataFrame (True, the default) or a
                Polars DataFrame (False).


        Raises:
            ValueError: If the specified category group, category, currency, or exchange
                is not available in the database.

        Returns:
            FinanceFrame: DataFrame containing indices data matching the specified criteria.
        """
        return self._select(
            {
                "category_group": category_group,
                "category": category,
                "currency": currency,
                "exchange": exchange,
                "mic": mic,
            },
            only_primary_listing=False,
            exclude_delisted=False,
            as_pandas=as_pandas,
        )

    def show_options(
        self,
        selection: str | None = None,
        category_group: str | list | None = None,
        category: str | list | None = None,
        currency: str | list | None = None,
        exchange: str | list | None = None,
        mic: str | list | None = None,
        as_pandas: bool = True,
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
            mic (str | list, optional): Filter by ISO 10383 MIC code.
                Default is None, which returns all MIC codes.
            as_pandas (bool, optional): Return the options as numpy arrays (True, the default)
                or as Polars Series (False).


        Raises:
            ValueError: If the specified selection is not valid or if the specified
                category group, category, currency, or exchange is not available in the database.

        Returns:
            dict | np.ndarray: A dictionary or array with all options for the specified selection.
                If selection is None, returns a dictionary with unique values for all fields.
                If selection is specified, returns an array of unique values for that field.
        """
        selection_values = [
            "category_group",
            "category",
            "currency",
            "exchange",
            "mic",
        ]
        return self._show_options(
            selection,
            selection_values,
            f"The selection variable provided is not valid, "
            f"choose from {', '.join(selection_values)}",
            {
                "category_group": category_group,
                "category": category,
                "currency": currency,
                "exchange": exchange,
                "mic": mic,
            },
            exclude_delisted=False,
            as_pandas=as_pandas,
        )
