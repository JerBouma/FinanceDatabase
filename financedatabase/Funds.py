"Funds Module"

import numpy as np

from .helpers import FinanceDatabase, FinanceFrame


class Funds(FinanceDatabase):
    """
    A Mutual Fund is a financial vehicle that pools assets from shareholders to
    invest in securities like stocks, bonds, money market instruments, and
    other assets. Mutual funds are operated by professional money managers, who
    allocate the fund's assets and attempt to produce capital gains or income for
    the fund's investors. A mutual fund's portfolio is structured and maintained
    to match the investment objectives stated in its prospectus.

    This class provides information about the funds available as well as the
    ability to select specific funds based on the category and/or family.
    """

    FILE_NAME = "funds.bz2"
    PLURAL_NAME = "funds"
    FIELDS = {
        "category_group": ("category group", "category groups"),
        "category": ("category", "categories"),
        "family": ("family", "families"),
        "currency": ("currency", "currencies"),
        "exchange": ("exchange", "exchanges"),
        "mic": ("MIC", "MICs"),
    }

    def select(
        self,
        category_group: str | list | None = None,
        category: str | list | None = None,
        family: str | list | None = None,
        currency: str | list | None = None,
        exchange: str | list | None = None,
        mic: str | list | None = None,
        only_primary_listing: bool = False,
        as_pandas: bool = True,
    ) -> FinanceFrame:
        """
        Retrieve fund data based on specified criteria.

        This method allows you to retrieve data for specific funds based on a combination
        of category group, category, and family filters. You can also exclude
        exchanges from the search. If no input criteria are provided, it returns data for all funds.

        Args:
            category_group (str | list, optional): Specific category group to filter funds.
                If not provided, returns data for all category groups.
            category (str | list, optional): Specific category to filter funds.
                If not provided, returns data for all categories.
            family (str | list, optional): Specific family to filter funds.
                If not provided, returns data for all families.
            currency (str | list, optional): Specific currency to filter funds.
                If not provided, returns data for all currencies.
            exchange (str | list, optional): Specific exchange to filter funds.
                If not provided, returns data for all exchanges.
            mic (str | list | None): Specific ISO 10383 MIC code or list of MIC codes to filter
                funds. If not provided, returns data for all MIC codes.
            only_primary_listing (bool, optional): Whether to return only primary listings.
                Default is False, which returns all funds.
            as_pandas (bool, optional): Return a pandas DataFrame (True, the default) or a
                Polars DataFrame (False).


        Returns:
            FinanceFrame:
                A DataFrame containing fund data matching the specified input criteria.
        """
        return self._select(
            {
                "category_group": category_group,
                "category": category,
                "family": family,
                "currency": currency,
                "exchange": exchange,
                "mic": mic,
            },
            only_primary_listing=only_primary_listing,
            exclude_delisted=False,
            as_pandas=as_pandas,
        )

    def show_options(
        self,
        selection: str | None = None,
        category_group: str | list | None = None,
        category: str | list | None = None,
        family: str | list | None = None,
        currency: str | list | None = None,
        exchange: str | list | None = None,
        mic: str | list | None = None,
        as_pandas: bool = True,
    ) -> dict | np.ndarray:
        """
        Retrieve all options for the specified selection.

        This method returns a series containing all available options for the specified
        selection, which can be one of the following: "currency", "category_group",
        "category", "family", "exchange".

        Args:
            selection (str | None): The selection you want to see the options for.
                Choose from "currency", "category_group", "category", "family", or "exchange".
                If None, returns all options for all categories.
            category_group (str | list | None): Specific category group to filter options.
                If not provided, returns data for all category groups.
            category (str | list | None): Specific category to filter options.
                If not provided, returns data for all categories.
            family (str | list | None): Specific family to filter options.
                If not provided, returns data for all families.
            currency (str | list | None): Specific currency to filter options.
                If not provided, returns data for all currencies.
            exchange (str | list | None): Specific exchange to filter options.
                If not provided, returns data for all exchanges.
            mic (str | list | None): Specific ISO 10383 MIC code to filter options.
                If not provided, returns data for all MIC codes.
            as_pandas (bool, optional): Return the options as numpy arrays (True, the default)
                or as Polars Series (False).


        Raises:
            ValueError: If the selection variable provided is not valid. Choose from:
                "currency", "category_group", "category", "family", or "exchange".

        Returns:
            dict | np.ndarray: A dictionary or array with all options for the specified selection.
                If selection is None, returns a dictionary with unique values for all fields.
                If selection is specified, returns an array of unique values for that field.
        """
        selection_values = [
            "currency",
            "category_group",
            "category",
            "family",
            "exchange",
            "mic",
        ]
        return self._show_options(
            selection,
            selection_values,
            f"The selection variable provided is not valid, "
            f"choose from {', '.join(selection_values)}",
            {
                "category_group": category_group,
                "category": category,
                "family": family,
                "currency": currency,
                "exchange": exchange,
                "mic": mic,
            },
            exclude_delisted=False,
            as_pandas=as_pandas,
        )
