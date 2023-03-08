"Moneymarkets Module"

import pandas as pd

from .helpers import FinanceDatabase


class Moneymarkets(FinanceDatabase):
    """
    The money market refers to trading in very short-term debt investments.
    At the wholesale level, it involves large-volume trades between institutions
    and traders. At the retail level, it includes money market mutual funds
    bought by individual investors and money market accounts opened
    by bank customers. [Source: Investopedia]

    This class provides information about the moneymarkets available as well as the
    ability to select specific moneymarkets based on the currency.
    """

    FILE_NAME = "moneymarkets.bz2"

    def select(
        self,
        category: str = "",
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
        category (string, default is None)
            If filled, gives all data for a specific category.
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

        if category:
            moneymarkets = moneymarkets[
                moneymarkets["category"].str.contains(
                    category.title() if capitalize else category, na=False
                )
            ]
        if exclude_exchanges:
            moneymarkets = moneymarkets[
                ~moneymarkets.index.str.contains(r"\.", na=False)
            ]

        return moneymarkets

    def options(self, selection: str) -> pd.Series:
        """
        Description
        ----
        Returns all options for the selection provided.

        Input
        ----
        selection (string)
            The selection you want to see the options for. Choose from:
                "category"
                "currency"
                "market"
                "exchange"

        Output
        ----
        options (pd.Series)
            Returns a series with all options for the selection provided.
        """
        selection_values = ["category", "currency", "market", "exchange"]
        if selection not in selection_values:
            raise ValueError(
                f"The selection variable provided is not valid, "
                f"choose from {', '.join(selection_values)}"
            )

        moneymarkets = self.select(exclude_exchanges=False)

        return moneymarkets[selection].dropna().sort_values().unique()
