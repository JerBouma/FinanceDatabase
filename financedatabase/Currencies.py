"Currencies Module"

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
        base_currency: str = "",
        quote_currency: str = "",
        capitalize: bool = True,
    ) -> pd.DataFrame:
        """
        Retrieve currency data based on specified criteria.

        This method allows you to retrieve data for specific base or quote currencies,
        with the option to customize the capitalization of currency names. If no input
        criteria are provided, it returns data for all currencies.

        Args:
            base_currency (str, optional):
                Specific base currency to retrieve data for. If not provided, returns data for all base currencies.
            quote_currency (str, optional):
                Specific quote currency to retrieve data for. If not provided, returns data for all quote currencies.
            capitalize (bool, optional):
                Indicates whether the currency names should be capitalized for matching. Default is True.

        Returns:
            pd.DataFrame:
                A DataFrame containing currency data matching the specified input criteria.
        """
        currencies = self.data.copy(deep=True)

        if base_currency:
            currencies = currencies[
                currencies["base_currency"].str.contains(
                    base_currency.upper() if capitalize else base_currency, na=False
                )
            ]
        if quote_currency:
            currencies = currencies[
                currencies["quote_currency"].str.contains(
                    quote_currency.upper() if capitalize else quote_currency, na=False
                )
            ]

        return FinanceFrame(currencies)

    def options(self, selection: str) -> pd.Series:
        """
        Retrieve all options for the specified selection.

        This method returns a series containing all available options for the specified
        selection, which can be one of the following: "base_currency", "quote_currency", "exchange", "market".

        Args:
            selection (str):
                The selection you want to see the options for. Choose from:
                - "base_currency"
                - "quote_currency"
                - "exchange"
                - "market"

        Returns:
            pd.Series:
                A series with all options for the specified selection, sorted and without duplicates.
        """
        selection_values = ["base_currency", "quote_currency", "exchange", "market"]
        if selection not in selection_values:
            raise ValueError(
                f"The selection variable provided is not valid, "
                f"choose from {', '.join(selection_values)}"
            )
        currencies = self.select()

        return currencies[selection].dropna().sort_values().unique()
