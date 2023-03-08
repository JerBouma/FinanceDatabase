"Currencies Module"

import pandas as pd

from .helpers import FinanceDatabase


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

    FILE_NAME = "currencies.brotli"

    def select(
        self,
        base_currency: str = "",
        quote_currency: str = "",
        capitalize: bool = True,
    ) -> pd.DataFrame:
        """
        Description
        ----
        Returns all currencies when no input is given and has the option to give
        a specific combination of currencies based on the from or to currency defined.

        Input
        ----
        base_currency (string, default is None)
            If filled, gives all data for the base currency.
        quote_currency
            If filled, gives all data for the quote currency.
        capitalize (boolean, default is True):
            Whether the currency needs to be capitalized. By default the values
            always are capitalized as that is also how it is represented in the csv files.
        base_url (string, default is GitHub location)
            The possibility to enter your own location if desired.
        use_local_location (string, default False)
            The possibility to select a local location (i.e. based on Windows path)

        Output
        ----
        currencies_df (pd.DataFrame)
            Returns a dictionary with a selection or all data based on the input.
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

        return currencies

    def options(self, selection: str) -> pd.Series:
        """
        Description
        ----
        Returns all options for the selection provided.

        Output
        ----
        selection (string)
            The selection you want to see the options for. Choose from:
                "base_currency"
                "quote_currency"
                "exchange"
                "market"
        options (pd.Series)
            Returns a series with all options for the selection provided.
        """
        selection_values = ["base_currency", "quote_currency", "exchange", "market"]
        if selection not in selection_values:
            raise ValueError(
                f"The selection variable provided is not valid, "
                f"choose from {', '.join(selection_values)}"
            )
        currencies = self.select()

        return currencies[selection].dropna().sort_values().unique()
