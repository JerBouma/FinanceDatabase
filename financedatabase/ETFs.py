"ETFs Module"

import numpy as np

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
    track specific investment strategies.

    This class provides information about the ETFs available as well as the
    ability to select specific ETFs based on the category and/or family.
    """

    FILE_NAME = "etfs.bz2"
    PLURAL_NAME = "etfs"
    FIELDS = {
        "category_group": ("category group", "category groups"),
        "category": ("category", "categories"),
        "family": ("family", "families"),
        "currency": ("currency", "currencies"),
        "exchange": ("exchange", "exchanges"),
        "mic": ("MIC", "MICs"),
    }
    # ETFs validate filter values against listed ETFs only, also when delisted ones are
    # requested (kept as before; equities follow exclude_delisted since #171).
    VALIDATION_EXCLUDES_DELISTED = True

    def select(
        self,
        category_group: str | list | None = None,
        category: str | list | None = None,
        family: str | list | None = None,
        currency: str | list | None = None,
        exchange: str | list | None = None,
        mic: str | list | None = None,
        only_primary_listing: bool = False,
        exclude_delisted: bool = True,
        as_pandas: bool = True,
    ) -> FinanceFrame:
        """
        Retrieve ETF data based on specified criteria.

        This method allows you to retrieve data for specific ETFs based on a combination
        of category group, category, and family filters. You can also exclude
        exchanges from the search. If no input criteria are provided, it returns data for all ETFs.

        Args:
            category_group (str | list, optional): Specific category group to filter ETFs.
                If not provided, returns data for all category groups.
            category (str | list, optional): Specific category to filter ETFs.
                If not provided, returns data for all categories.
            family (str | list, optional): Specific family to filter ETFs.
                If not provided, returns data for all families.
            currency (str | list, optional): Specific currency to filter ETFs.
                If not provided, returns data for all currencies.
            exchange (str | list, optional): Specific exchange to filter ETFs.
                If not provided, returns data for all exchanges.
            mic (str | list | None): Specific ISO 10383 MIC code or list of MIC codes to filter
                ETFs. If not provided, returns data for all MIC codes.
            only_primary_listing (bool, optional): If True, returns only primary listings.
                Default is False, which returns all listings.
            exclude_delisted (bool, optional): Whether to exclude delisted ETFs.
                If True, delisted ETFs will be excluded from the results.
                Default is True.
            as_pandas (bool, optional): Return a pandas DataFrame (True, the default) or a
                Polars DataFrame (False).


        Raises:
            ValueError: If the specified category group, category, family, currency,
                or exchange is not available in the database. Please check the available
                options using the 'show_options' method.

        Returns:
            FinanceFrame:
                A DataFrame containing ETF data matching the specified input criteria.
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
            exclude_delisted=exclude_delisted,
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
        exclude_delisted: bool = True,
        as_pandas: bool = True,
    ) -> dict | np.ndarray:
        """
        Retrieve all options for the specified selection.

        This method returns a series containing all available options for the specified
        selection, which can be one of the following: "currency", "category_group",
        "category", "family", "exchange", "market".

        Args:
            selection (str | None): The selection you want to see the options for.
                Choose from "currency", "category_group", "category", "family", "exchange".
                If not provided, returns all options for all selections.
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
            exclude_delisted (bool, optional): Whether to exclude delisted ETFs.
                Default is True.
            as_pandas (bool, optional): Return the options as numpy arrays (True, the default)
                or as Polars Series (False).


        Raises:
            ValueError: If the selection variable provided is not valid.
                Choose from "currency", "category_group", "category", "family", "exchange".

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
            exclude_delisted=exclude_delisted,
            as_pandas=as_pandas,
        )
