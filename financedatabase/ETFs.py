"ETFs Module"

import pandas as pd

from .helpers import FinanceDatabase


class ETFs(FinanceDatabase):
    """
    An exchange-traded fund (ETF) is a type of pooled investment
    security that operates much like a mutual fund. Typically, ETFs
    will track a particular index, sector, commodity, or other assets,
    but unlike mutual funds, ETFs can be purchased or sold on a stock
    exchange the same way that a regular stock can. An ETF can be structured
    to track anything from the price of an individual commodity to a large
    and diverse collection of securities. ETFs can even be structured to
    track specific investment strategies. [Source: Investopedia]

    This class provides information about the ETFs available as well as the
    ability to select specific ETFs based on the category and/or family.
    """

    FILE_NAME = "etfs.bz2"

    def select(
        self,
        category_group: str = "",
        category: str = "",
        family: str = "",
        exclude_exchanges: bool = True,
        capitalize: bool = True,
    ) -> pd.DataFrame:
        """
        Description
        ----
        Returns all etfs when no input is given and has the option to give
        a specific set of symbols for the category and/or family provided.

        The data depends on the combination of inputs. For example Category + Family
        gives all symbols for a specific category for a specific family.

        Input
        ----
        category (string, default is None)
            If filled, gives all data for a specific category.
        family (string, default is None)
            If filled, gives all data for a specific family.
        exclude_exchanges (boolean, default is True):
            Whether you want to exclude exchanges from the search. If False,
            you will receive multiple times the product from different exchanges.
        capitalize (boolean, default is True):
            Whether country, sector and industry needs to be capitalized. By default
            the values always are capitalized as that is also how it is represented
            in the csv files.
        base_url (string, default is GitHub location)
            The possibility to enter your own location if desired.
        use_local_location (string, default False)
            The possibility to select a local location (i.e. based on Windows path)

        Output
        ----
        etfs_df (pd.DataFrame)
            Returns a dictionary with a selection or all data based on the input.
        """
        etfs = self.data.copy(deep=True)

        if capitalize:
            category_group, category, family = (
                category_group.title(),
                category.title(),
                family.title(),
            )

        if category_group:
            etfs = etfs[etfs["category_group"] == category_group]
        if category:
            etfs = etfs[etfs["category"] == category]
        if family:
            etfs = etfs[etfs["family"] == family]
        if exclude_exchanges:
            etfs = etfs[~etfs.index.str.contains(r"\.", na=False)]
        return etfs

    def options(
        self, selection: str, category: str = "", family: str = ""
    ) -> pd.Series:
        """
        Description
        ----
        Returns all options for the selection provided.

        Input
        ----
        selection (string)
            The selection you want to see the options for. Choose from:
                "currency"
                "category_group"
                "category"
                "family"
                "exchange"
                "market"
        category (string, default is None)
            If filled, gives all data for a specific category.
        family (string, default is None)
            If filled, gives all data for a specific family.

        Output
        ----
        options (pd.Series)
            Returns a series with all options for the selection provided.
        """
        selection_values = [
            "currency",
            "category_group",
            "category",
            "family",
            "exchange",
            "market",
        ]
        if selection not in selection_values:
            raise ValueError(
                f"The selection variable provided is not valid, "
                f"choose from {', '.join(selection_values)}"
            )

        etfs = self.select(category=category, family=family, exclude_exchanges=False)

        if etfs.empty:
            # Meant for the rare cases where capitalizing is not working as desired.
            etfs = self.select(
                category=category,
                family=family,
                capitalize=False,
                exclude_exchanges=False,
            )

        return etfs[selection].dropna().sort_values().unique()
