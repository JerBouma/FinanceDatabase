"Moneymarkets Module"

import pandas as pd

from .helpers import FinanceDatabase


class Moneymarkets(FinanceDatabase):
    """
    Moneymarkets Class
    """

    FILE_NAME = "moneymarkets.csv"

    def select(
        self,
        currency: str = "",
        capitalize: bool = True,
        exclude_exchanges: bool = True,
    ) -> pd.DataFrame:
        """
        Description
        ----
        Returns all moneymarkets when no input is given and has the option to give
        a specific combination of moneymarkets based on the currency defined.

        Input
        ----
        currency (string, default is None)
            If filled, gives all data for a specific currency.
        capitalize (boolean, default is True):
            Whether the currency needs to be capitalized. By default the values
            always are capitalized as that is also how it is represented in the csv files.
        exclude_exchanges (boolean, default is True):
            Whether you want to exclude exchanges from the search. If False,
            you will receive multiple times the product from different exchanges.
        base_url (string, default is GitHub location)
            The possibility to enter your own location if desired.
        use_local_location (string, default False)
            The possibility to select a local location (i.e. based on Windows path)

        Output
        ----
        indices_df (pd.DataFrame)
            Returns a dictionary with a selection or all data based on the input.
        """
        moneymarkets = self.data.copy(deep=True)

        if currency:
            moneymarkets = moneymarkets[
                moneymarkets["currency"].str.contains(
                    currency.upper() if capitalize else currency, na=False
                )
            ]
        if exclude_exchanges:
            moneymarkets = moneymarkets[
                ~moneymarkets["symbol"].str.contains(r"\.", na=False)
            ]

        return moneymarkets

    def options(self) -> pd.Series:
        """
        Description
        ----
        Returns all options for the selection provided.

        Output
        ----
        options (pd.Series)
            Returns a series with all options for the selection provided.
        """
        moneymarkets = self.select()

        return moneymarkets["currency"].dropna().sort_values().unique()
