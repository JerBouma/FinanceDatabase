"Currencies Module"

import numpy as np

from .helpers import FinanceDatabase, FinanceFrame


class Currencies(FinanceDatabase):
    """
    Currency is a medium of exchange for goods and services. In short,
    it's money, in the form of paper and coins, usually issued by a
    government and generally accepted at its face value as a method of payment.
    Currency is the primary medium of exchange in the modern world, having
    long ago replaced bartering as a means of trading goods and services.

    This class provides information about the currencies available as well as the
    ability to select specific currencies based on the currency.
    """

    FILE_NAME = "currencies.bz2"
    FIELDS = {
        "base_currency": ("base currency", "base currencies"),
        "quote_currency": ("quote currency", "quote currencies"),
    }

    def select(
        self,
        base_currency: str | list | None = None,
        quote_currency: str | list | None = None,
        as_pandas: bool = True,
    ) -> FinanceFrame:
        """
        Retrieve currency data based on specified criteria.

        This method allows you to retrieve data for specific base or quote currencies,
        with the option to customize the capitalization of currency names. If no input
        criteria are provided, it returns data for all currencies.

        Args:
            base_currency (str | list | None, optional): Specific base currency to retrieve data for.
                If not provided, returns data for all base currencies.
            quote_currency (str | list | None, optional): Specific quote currency to retrieve data for.
                If not provided, returns data for all quote currencies.
            as_pandas (bool, optional): Return a pandas DataFrame (True, the default) or a
                Polars DataFrame (False).


        Raises:
            ValueError: If the specified base or quote currency is not available in the database.
                Please check the available base and quote currencies using the 'show_options' method.

        Returns:
            FinanceFrame:
                A DataFrame containing currency data matching the specified input criteria.
        """
        return self._select(
            {"base_currency": base_currency, "quote_currency": quote_currency},
            only_primary_listing=False,
            exclude_delisted=False,
            as_pandas=as_pandas,
        )

    def show_options(
        self,
        selection: str | None = None,
        base_currency: str | list | None = None,
        quote_currency: str | list | None = None,
        as_pandas: bool = True,
    ) -> dict | np.ndarray:
        """
        Retrieve all options for the specified selection.

        This method returns a series containing all available options for the specified
        selection, which can be one of the following: "base_currency", "quote_currency", "exchange", "market".

        Args:
            selection (str. optional): The selection you want to see the options for.
                Choose from: "base_currency" or "quote_currency"
                If not provided, returns data for all base and quote currencies.
            base_currency (str | list | None, optional): Specific base currency to filter options.
                If not provided, returns data for all base currencies.
            quote_currency (str | list | None, optional): Specific quote currency to filter options.
                If not provided, returns data for all quote currencies.
            as_pandas (bool, optional): Return the options as numpy arrays (True, the default)
                or as Polars Series (False).


        Returns:
            dict | np.ndarray:
                A dictionary or array with all options for the specified selection.
                If selection is None, returns a dictionary with unique values for all fields.
                If selection is specified, returns an array of unique values for that field.
        """
        selection_values = ["base_currency", "quote_currency"]
        return self._show_options(
            selection,
            selection_values,
            f"The selection variable ({selection}) provided is not valid, "
            f"choose from {', '.join(selection_values)}",
            {"base_currency": base_currency, "quote_currency": quote_currency},
            exclude_delisted=False,
            as_pandas=as_pandas,
        )
