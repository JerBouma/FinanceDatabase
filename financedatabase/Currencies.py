"Currencies Module"

import numpy as np
import pandas as pd

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

    def select(
        self,
        base_currency: str | list | None = None,
        quote_currency: str | list | None = None,
    ) -> pd.DataFrame:
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

        Raises:
            ValueError: If the specified base or quote currency is not available in the database.
                Please check the available base and quote currencies using the 'show_options' method.

        Returns:
            pd.DataFrame:
                A DataFrame containing currency data matching the specified input criteria.
        """
        currencies = self.data.copy(deep=True)

        if base_currency:
            base_currencies = (
                [base_currency] if isinstance(base_currency, str) else base_currency
            )
            base_currencies_lower = [currency.lower() for currency in base_currencies]
            options_lower = [
                option.lower()
                for option in self.show_options(selection="base_currency")
            ]

            for base_currency_lower, base_currency_actual in zip(
                base_currencies_lower, base_currencies
            ):
                if base_currency_lower not in options_lower:
                    raise ValueError(
                        f"The base currency '{base_currency_actual}' is not available in the database. "
                        "Please check the available base currencies using the 'show_options' method."
                    )

            currencies = currencies[
                currencies["base_currency"].str.lower().isin(base_currencies_lower)
            ]

        if quote_currency:
            quote_currencies = (
                [quote_currency] if isinstance(quote_currency, str) else quote_currency
            )
            quote_currencies_lower = [currency.lower() for currency in quote_currencies]
            options_lower = [
                option.lower()
                for option in self.show_options(selection="quote_currency")
            ]
            for quote_currency_lower, quote_currency_actual in zip(
                quote_currencies_lower, quote_currencies
            ):
                if quote_currency_lower not in options_lower:
                    raise ValueError(
                        f"The quote currency '{quote_currency_actual}' is not available in the database. "
                        "Please check the available quote currencies using the 'show_options' method."
                    )
            currencies = currencies[
                currencies["quote_currency"].str.lower().isin(quote_currencies_lower)
            ]

        return FinanceFrame(currencies)

    def show_options(
        self,
        selection: str | None = None,
        base_currency: str | list | None = None,
        quote_currency: str | list | None = None,
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

        Returns:
            dict | np.ndarray:
                A dictionary or array with all options for the specified selection.
                If selection is None, returns a dictionary with unique values for all fields.
                If selection is specified, returns an array of unique values for that field.
        """
        selection_values = ["base_currency", "quote_currency"]

        if selection is not None and selection not in selection_values:
            raise ValueError(
                f"The selection variable ({selection}) provided is not valid, "
                f"choose from {', '.join(selection_values)}"
            )

        currencies = self.select(
            base_currency=base_currency,
            quote_currency=quote_currency,
        )

        return (
            {
                column: currencies[column].dropna().sort_values().unique()
                for column in selection_values
            }
            if selection is None
            else currencies[selection].dropna().sort_values().unique()
        )
