"Funds Module"

import pandas as pd

from .helpers import FinanceDatabase, FinanceFrame


class Funds(FinanceDatabase):
    """
    A Mutual Fund is a financial vehicle that pools assets from shareholders to
    invest in securities like stocks, bonds, money market instruments, and
    other assets. Mutual funds are operated by professional money managers, who
    allocate the fund's assets and attempt to produce capital gains or income for
    the fund's investors. A mutual fund's portfolio is structured and maintained
    to match the investment objectives stated in its prospectus. [Source: Investopedia]

    This class provides information about the funds available as well as the
    ability to select specific funds based on the category and/or family.
    """

    FILE_NAME = "funds.bz2"

    def select(
        self,
        category_group: str = "",
        category: str = "",
        family: str = "",
        exclude_exchanges: bool = True,
        capitalize: bool = True,
    ) -> pd.DataFrame:
        """
        Retrieve fund data based on specified criteria.

        This method allows you to retrieve data for specific funds based on a combination
        of category group, category, and family filters. You can also exclude
        exchanges from the search. If no input criteria are provided, it returns data for all funds.

        Args:
            category_group (str, optional):
                Specific category group to retrieve data for. If not provided, returns data for all category groups.
            category (str, optional):
                Specific category to retrieve data for. If not provided, returns data for all categories.
            family (str, optional):
                Specific family to retrieve data for. If not provided, returns data for all families.
            exclude_exchanges (bool, optional):
                Whether to exclude exchanges from the search. If False, you will receive
                data for funds from different exchanges. Default is True.
            capitalize (bool, optional):
                Indicates whether category group, category, and family names should be capitalized for matching.
                Default is True.

        Returns:
            pd.DataFrame:
                A DataFrame containing fund data matching the specified input criteria.
        """
        funds = self.data.copy(deep=True)

        if capitalize:
            category_group, category, family = (
                category_group.title(),
                category.title(),
                family.title(),
            )

        if category_group:
            funds = funds[funds["category_group"] == category_group]
        if category:
            funds = funds[funds["category"] == category]
        if family:
            funds = funds[funds["family"] == family]
        if exclude_exchanges:
            funds = funds[~funds.index.str.contains(r"\.", na=False)]

        return FinanceFrame(funds)

    def options(
        self,
        selection: str,
        category_group: str = "",
        category: str = "",
        family: str = "",
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
            category_group (str, optional):
                Specific category group to retrieve data for. If not provided, returns data for all category groups.
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

        funds = self.select(
            category_group=category_group,
            category=category,
            family=family,
            exclude_exchanges=False,
        )

        if funds.empty:
            # Meant for the rare cases where capitalizing is not working as desired.
            funds = self.select(
                category_group=category_group,
                category=category,
                family=family,
                capitalize=False,
                exclude_exchanges=False,
            )

        return funds[selection].dropna().sort_values().unique()
