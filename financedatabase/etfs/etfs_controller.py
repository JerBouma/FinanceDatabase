"""ETFs Module"""

__docformat__ = "google"

import numpy as np
import polars as pl

from financedatabase.database_controller import FinanceDatabase
from financedatabase.frame_model import FinanceFrame


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
    HAS_LISTINGS = True
    PLURAL_NAME = "etfs"
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
        exclude_delisted: bool = True,
        as_pandas: bool = True,
    ) -> FinanceFrame | pl.DataFrame:
        """
        Select ETFs based on the category group, category, family and other criteria.

        Returns all ETFs when no input is given.

        Args:
            category_group (str | list, optional): Specific category group or list of
                category groups to filter ETFs on. Defaults to None (all category groups).
            category (str | list, optional): Specific category or list of categories to
                filter ETFs on. Defaults to None (all categories).
            family (str | list, optional): Specific family or list of families to filter
                ETFs on. Defaults to None (all families).
            currency (str | list, optional): Specific currency or list of currencies to
                filter ETFs on. Defaults to None (all currencies).
            exchange (str | list, optional): Specific exchange or list of exchanges to
                filter ETFs on. Defaults to None (all exchanges).
            mic (str | list, optional): Specific MIC or list of MICs to filter ETFs on.
                Defaults to None (all MICs).
            only_primary_listing (bool, optional): Whether to only include primary listings
                (per instrument its listing on the main exchange of its home market, see
                listings_model). Defaults to False.
            exclude_delisted (bool, optional): Whether to exclude delisted ETFs. Defaults to
                True.
            as_pandas (bool, optional): Whether to return a pandas DataFrame (True) or a
                Polars DataFrame (False). Defaults to True.

        Returns:
            FinanceFrame | pl.DataFrame: The ETFs matching every filter.

        Raises:
            ValueError: If a filter value is not available in the database. Check the
                available values with the 'show_options' method.

        As an example:

        ```python
        import financedatabase as fd

        etfs = fd.ETFs()

        etfs.select(
            category_group="Equities",
            category="Large Cap",
            family="BlackRock Asset Management",
            only_primary_listing=True,
        )[["name", "currency", "category", "exchange"]].head()
        ```

        Which returns:

        | symbol  | name                           | currency | category  | exchange |
        |:--------|:-------------------------------|:---------|:----------|:---------|
        | 1329.T  | iShares Core Nikkei 225 ETF    | JPY      | Large Cap | JPX      |
        | 1475.T  | iShares Core TOPIX ETF         | JPY      | Large Cap | JPX      |
        | 1655.T  | iShares S&P 500 ETF            | JPY      | Large Cap | JPX      |
        | 2563.T  | iShares S&P 500 JPY Hedged ETF | JPY      | Large Cap | JPX      |
        | 2834.HK | ISHARES NASDAQ 100 ETF-HKD     | HKD      | Large Cap | HKG      |
        """
        return self._select_rows(
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
    ) -> dict | np.ndarray | pl.Series:
        """
        Show the available values of the ETFs filters.

        The options can be narrowed down with the same filters as select().

        Args:
            selection (str | None, optional): The column to show the options of. Choose
                from: "category_group", "category", "family", "currency", "exchange", "mic".
                Defaults to None, which returns the options of every column.
            category_group (str | list, optional): Specific category group or list of
                category groups to filter the options on. Defaults to None (all category
                groups).
            category (str | list, optional): Specific category or list of categories to
                filter the options on. Defaults to None (all categories).
            family (str | list, optional): Specific family or list of families to filter the
                options on. Defaults to None (all families).
            currency (str | list, optional): Specific currency or list of currencies to
                filter the options on. Defaults to None (all currencies).
            exchange (str | list, optional): Specific exchange or list of exchanges to
                filter the options on. Defaults to None (all exchanges).
            mic (str | list, optional): Specific MIC or list of MICs to filter the options
                on. Defaults to None (all MICs).
            exclude_delisted (bool, optional): Whether to exclude delisted ETFs. Defaults to
                True.
            as_pandas (bool, optional): Whether to return the options as numpy arrays (True)
                or as Polars Series (False). Defaults to True.

        Returns:
            dict | np.ndarray | pl.Series: The sorted unique values of the selected column,
                or a dictionary with the values of every column if no selection is given.

        Raises:
            ValueError: If the selection or a filter value is not valid.

        As an example:

        ```python
        import financedatabase as fd

        etfs = fd.ETFs()

        etfs.show_options(selection="category", category_group="Fixed Income")
        ```

        Which returns:

        ```
        ['Blend', 'Bonds', 'Cash', 'Commercial Real Estate', 'Corporate Bonds',
         'Developed Markets', 'Emerging Markets', 'Factors', 'Frontier Markets',
         'Government Bonds', 'Growth', 'High Yield Bonds', 'Inflation-Protected Securities',
         'Investment Grade Bonds', 'Large Cap', 'Mid Cap', 'Money Market Instruments',
         'Municipal Bonds', 'Small Cap', 'Treasury Bonds', 'Value']
        ```
        """
        selection_values = [
            "currency",
            "category_group",
            "category",
            "family",
            "exchange",
            "mic",
        ]
        return self._collect_options(
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
