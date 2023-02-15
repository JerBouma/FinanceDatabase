"Cryptos Module"

import pandas as pd

from .helpers import FinanceDatabase


class Cryptos(FinanceDatabase):
    """
    Cryptos Class
    """

    FILE_NAME = "cryptos.csv"

    def select(
        self,
        crypto: str = "",
        capitalize: bool = True,
    ) -> pd.DataFrame:
        """
        Description
        ----
        Returns all cryptos when no input is given and has the option to give
        a specific combination of cryptos based on the crypto defined.


        Input
        ----
        crypto (string, default is None)
            If filled, gives all data for a specific crypto.
        capitalize (boolean, default is True):
            Whether the crypto needs to be capitalized. By default the values
            always are capitalized as that is also how it is represented in the csv files.
        base_url (string, default is GitHub location)
            The possibility to enter your own location if desired.
        use_local_location (string, default False)
            The possibility to select a local location (i.e. based on Windows path)

        Output
        ----
        cryptos_df (pd.DataFrame)
            Returns a dictionary with a selection or all data based on the input.
        """
        cryptos = self.data.copy(deep=True)

        if crypto:
            cryptos = cryptos[
                cryptos["cryptocurrency"].str.contains(
                    crypto.upper() if capitalize else crypto, na=False
                )
            ]

        return cryptos

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
        cryptos = self.select()

        return cryptos["cryptocurrency"].dropna().sort_values().unique()
