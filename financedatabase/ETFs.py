"ETFs Module"

import pandas as pd

from .helpers import FinanceDatabase, FinanceFrame


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
        Retrieve ETF data based on specified criteria.

        This method allows you to retrieve data for specific ETFs based on a combination
        of category group, category, and family filters. You can also exclude
        exchanges from the search. If no input criteria are provided, it returns data for all ETFs.

        Args:
            category_group (str, optional):
                Specific category group to retrieve data for. If not provided, returns data for all category groups.
            category (str, optional):
                Specific category to retrieve data for. If not provided, returns data for all categories.
            family (str, optional):
                Specific family to retrieve data for. If not provided, returns data for all families.
            exclude_exchanges (bool, optional):
                Whether to exclude exchanges from the search. If False, you will receive
                data for ETFs from different exchanges. Default is True.
            capitalize (bool, optional):
                Indicates whether category group, category, and family names should be capitalized for matching.
                Default is True.

        Returns:
            pd.DataFrame:
                A DataFrame containing ETF data matching the specified input criteria.
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

        return FinanceFrame(etfs)

    def options(
        self, selection: str, category: str = "", family: str = ""
    ) -> pd.Series:
        """
        Retrieve all options for the specified selection.

        This method returns a series containing all available options for the specified
        selection, which can be one of the following: "currency", "category_group",
        "category", "family", "exchange", "market".

        Args:
            selection (str):
                The selection you want to see the options for. Choose from:
                - "currency"
                - "category_group"
                - "category"
                - "family"
                - "exchange"
                - "market"
            category (str, optional):
                Specific category to retrieve data for. If not provided, returns data for all categories.
            family (str, optional):
                Specific family to retrieve data for. If not provided, returns data for all families.

        Returns:
            pd.Series:
                A series with all options for the specified selection, sorted and without duplicates.
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
