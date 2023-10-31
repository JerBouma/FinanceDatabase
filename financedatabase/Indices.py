"Indices Module"

import pandas as pd

from .helpers import FinanceDatabase, FinanceFrame


class Indices(FinanceDatabase):
    """
    An index is a method to track the performance of a group of assets in a standardized way.
    Indexes typically measure the performance of a basket of securities intended to
    replicate a certain area of the market. These could be constructed as a broad-based
    index that captures the entire market, such as the Standard & Poor's 500 Index or
    Dow Jones Industrial Average (DJIA), or more specialized such as indexes that
    track a particular industry or segment such as the Russell 2000 Index,
    which tracks only small-cap stocks. [Source: Investopedia]

    This class provides information about the indices available as well as the
    ability to select specific indices based on the currency.
    """

    FILE_NAME = "indices.bz2"

    def select(
        self,
        currency: str = "",
        capitalize: bool = True,
        exclude_exchanges: bool = True,
    ) -> pd.DataFrame:
        """
        Returns all indices when no input is given and has the option to give
        a specific combination of indices based on the currency defined.

        Args:
            currency (str, optional):
                If filled, gives all data for a specific currency.
            capitalize (bool, optional):
                Whether the currency needs to be capitalized. By default, the values
                are always capitalized as that is also how it is represented in the CSV files.
            exclude_exchanges (bool, optional):
                Whether you want to exclude exchanges from the search. If False,
                you will receive multiple instances of the same product from different exchanges.

        Returns:
            indices_df (pd.DataFrame):
                Returns a DataFrame with a selection or all data based on the input.
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

        return FinanceFrame(indices)

    def options(self, selection: str) -> pd.Series:
        """
        Returns all options for the selection provided.

        Args:
            selection (str):
                The selection you want to see the options for. Choose from:
                    "currency"
                    "market"
                    "exchange"
                    "timezone"

        Returns:
            options (pd.Series):
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
