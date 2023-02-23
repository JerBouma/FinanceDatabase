"Funds Module"

import pandas as pd

from .helpers import FinanceDatabase


class Funds(FinanceDatabase):
    """
    A Mutual Fund is a financial vehicle that pools assets from shareholders to
    invest in securities like stocks, bonds, money market instruments, and
    other assets. Mutual funds are operated by professional money managers, who
    allocate the fund's assets and attempt to produce capital gains or income for
    the fund's investors. A mutual fund's portfolio is structured and maintained
    to match the investment objectives stated in its prospectus. [Source: Investopedia]

    This class provides a information about the funds available as well as the
    ability to select specific funds based on the category and/or family.
    """

    FILE_NAME = "funds.pkl"

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
        Returns all funds when no input is given and has the option to give
        a specific set of symbols for the category and/or family provided.

        The data depends on the combination of inputs. For example Category + Family
        gives all symbols for a specific category for a specific family.

        Input
        ----
        category_group (string, default is None)
            If filled, gives all data for a specific category group.
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
        funds_df (pd.DataFrame)
            Returns a dictionary with a selection or all data based on the input.
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
        return funds

    def options(
        self,
        selection: str,
        category_group: str = "",
        category: str = "",
        family: str = "",
    ) -> pd.Series:
        """
        Description
        ----
        Returns all options for the selection provided.

        Input
        ----
        selection (string)
            The selection you want to see the options for. Can be:
            - category_group
            - category
            - family
        category (string, default is None)
            If filled, gives all data for a specific category.
        family (string, default is None)
            If filled, gives all data for a specific family.

        Output
        ----
        options (pd.Series)
            Returns a series with all options for the selection provided.
        """
        selection_values = ["category_group", "category", "family"]
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
