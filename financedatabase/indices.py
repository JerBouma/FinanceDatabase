"Indices Module"

import json
import pandas as pd

import requests

from .helpers import FinanceDatabase


class Indices(FinanceDatabase):
    """
    Indices Class
    """

    FILE_NAME = "indices.csv"

    def select(
        self,
        currency: str = "",
        capitalize: bool = True,
        exclude_exchanges: bool = True,
    ) -> pd.DataFrame:
        """
        Description
        ----
        Returns all indices when no input is given and has the option to give
        a specific combination of indices based on the currency defined.

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
        indices = self.data.copy(deep=True)

        if currency:
            indices = indices[indices["currency"].str.contains(
                currency.upper() if capitalize else currency, na=False)]
        if exclude_exchanges:
            indices = indices[~indices["symbol"].str.contains(r"\.", na=False)]
            
        return indices

    def options(
        self
    ) -> pd.Series:
        """
        Description
        ----
        Returns all options for the selection provided.

        Output
        ----
        options (pd.Series)
            Returns a series with all options for the selection provided.
        """
        indices = self.select()

        return indices["currency"].unique()
