"Indices Module"

import pandas as pd

from .helpers import FinanceDatabase


class Indices(FinanceDatabase):
    """
    An index is a method to track the performance of a group of assets in a standardized way.
    Indexes typically measure the performance of a basket of securities intended to
    eplicate a certain area of the market. These could be constructed as a broad-based
    index that captures the entire market, such as the Standard & Poor's 500 Index or
    Dow Jones Industrial Average (DJIA), or more specialized such as indexes that
    track a particular industry or segment such as the Russell 2000 Index,
    which tracks only small-cap stocks. [Source: Investopedia]

    This class provides information about the indices available as well as the
    ability to select specific indices based on the currency.
    """

    FILE_NAME = "indices.pkl"

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
            indices = indices[
                indices["currency"].str.contains(
                    currency.upper() if capitalize else currency, na=False
                )
            ]
        if exclude_exchanges:
            indices = indices[~indices.index.str.contains(r"\.", na=False)]

        return indices

    def options(self, selection: str) -> pd.Series:
        """
        Description
        ----
        Returns all options for the selection provided.

        Input
        ----
        selection (string)
            The selection you want to see the options for. Choose from:
                "currency"
                "market"
                "exchange"
                "timezone"

        Output
        ----
        options (pd.Series)
            Returns a series with all options for the selection provided.
        """
        selection_values = ["currency", "market", "exchange", "timezone"]
        if selection not in selection_values:
            raise ValueError(
                f"The selection variable provided is not valid, "
                f"choose from {', '.join(selection_values)}"
            )

        indices = self.select(exclude_exchanges=False)

        return indices[selection].dropna().sort_values().unique()
