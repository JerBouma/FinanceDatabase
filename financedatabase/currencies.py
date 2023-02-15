"Currencies Module"

import pandas as pd

from .helpers import FinanceDatabase


class Currencies(FinanceDatabase):
    """
    Currencies Class
    """

    FILE_NAME = "currencies.csv"

    def select(
        self,
        currency: str = "",
        capitalize: bool = True,
    ) -> pd.DataFrame:
        """
        Description
        ----
        Returns all currencies when no input is given and has the option to give
        a specific combination of currencies based on the currency defined.

        Input
        ----
        currency (string, default is None)
            If filled, gives all data for a specific currency.
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

        if currency:
            currencies = currencies[
                currencies["currency"].str.contains(
                    currency.upper() if capitalize else currency, na=False
                )
            ]

        return currencies

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
        currencies = self.select()

        return currencies["currency"].dropna().sort_values().unique()
