"""Indices Module"""

__docformat__ = "google"

import numpy as np
import polars as pl

from financedatabase.database_controller import FinanceDatabase
from financedatabase.frame_controller import FinanceFrame


class Indices(FinanceDatabase):
    """
    An index is a method to track the performance of a group of assets in a standardized way.
    Indexes typically measure the performance of a basket of securities intended to
    replicate a certain area of the market. These could be constructed as a broad-based
    index that captures the entire market, such as the Standard & Poor's 500 Index or
    Dow Jones Industrial Average (DJIA), or more specialized such as indexes that
    track a particular industry or segment such as the Russell 2000 Index,
    which tracks only small-cap stocks.

    This class provides information about the indices available as well as the
    ability to select specific indices based on various criteria.
    """

    FILE_NAME = "indices.bz2"
    FIELDS = {
        "category_group": ("category group", "category groups"),
        "category": ("category", "categories"),
        "currency": ("currency", "currencies"),
        "exchange": ("exchange", "exchanges"),
        "mic": ("MIC", "MICs"),
    }

    def select(
        self,
        category_group: str | list | None = None,
        category: str | list | None = None,
        currency: str | list | None = None,
        exchange: str | list | None = None,
        mic: str | list | None = None,
        as_pandas: bool = True,
    ) -> FinanceFrame | pl.DataFrame:
        """
        Select indices based on the category group, category, currency and other criteria.

        Returns all indices when no input is given.

        Args:
            category_group (str | list, optional): Specific category group or list of
                category groups to filter indices on. Defaults to None (all category
                groups).
            category (str | list, optional): Specific category or list of categories to
                filter indices on. Defaults to None (all categories).
            currency (str | list, optional): Specific currency or list of currencies to
                filter indices on. Defaults to None (all currencies).
            exchange (str | list, optional): Specific exchange or list of exchanges to
                filter indices on. Defaults to None (all exchanges).
            mic (str | list, optional): Specific MIC or list of MICs to filter indices on.
                Defaults to None (all MICs).
            as_pandas (bool, optional): Whether to return a pandas DataFrame (True) or a
                Polars DataFrame (False). Defaults to True.

        Returns:
            FinanceFrame | pl.DataFrame: The indices matching every filter.

        Raises:
            ValueError: If a filter value is not available in the database. Check the
                available values with the 'show_options' method.

        As an example:

        ```python
        import financedatabase as fd

        indices = fd.Indices()

        indices.select(category_group="Equities", category="Large Cap", currency="EUR")[
            ["name", "currency", "category", "exchange"]
        ].head()
        ```

        Which returns:

        | symbol | name              | currency | category  | exchange |
        |:-------|:------------------|:---------|:----------|:---------|
        | 0020.Z | ESTX LRB50 NR EUR | EUR      | Large Cap | ZRH      |
        | 0022.Z | ESTX LRB50 PR EUR | EUR      | Large Cap | ZRH      |
        | 002A.Z | ESTX LR50 NR EUR  | EUR      | Large Cap | ZRH      |
        | 002C.Z | ESTX LR50 PR EUR  | EUR      | Large Cap | ZRH      |
        | 002G.Z | ESTX LR100 NR EUR | EUR      | Large Cap | ZRH      |
        """
        return self._select_rows(
            {
                "category_group": category_group,
                "category": category,
                "currency": currency,
                "exchange": exchange,
                "mic": mic,
            },
            only_primary_listing=False,
            exclude_delisted=False,
            as_pandas=as_pandas,
        )

    def show_options(
        self,
        selection: str | None = None,
        category_group: str | list | None = None,
        category: str | list | None = None,
        currency: str | list | None = None,
        exchange: str | list | None = None,
        mic: str | list | None = None,
        as_pandas: bool = True,
    ) -> dict | np.ndarray | pl.Series:
        """
        Show the available values of the indices filters.

        The options can be narrowed down with the same filters as select().

        Args:
            selection (str | None, optional): The column to show the options of. Choose
                from: "category_group", "category", "currency", "exchange", "mic". Defaults
                to None, which returns the options of every column.
            category_group (str | list, optional): Specific category group or list of
                category groups to filter the options on. Defaults to None (all category
                groups).
            category (str | list, optional): Specific category or list of categories to
                filter the options on. Defaults to None (all categories).
            currency (str | list, optional): Specific currency or list of currencies to
                filter the options on. Defaults to None (all currencies).
            exchange (str | list, optional): Specific exchange or list of exchanges to
                filter the options on. Defaults to None (all exchanges).
            mic (str | list, optional): Specific MIC or list of MICs to filter the options
                on. Defaults to None (all MICs).
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

        indices = fd.Indices()

        indices.show_options(selection="category_group")
        ```

        Which returns:

        ```
        ['Alternatives', 'Cash', 'Commodities', 'Communication Services',
         'Consumer Discretionary', 'Consumer Staples', 'Currencies', 'Derivatives', 'Energy',
         'Equities', 'Financials', 'Fixed Income', 'Health Care', 'Industrials',
         'Information Technology', 'Materials', 'Real Estate', 'Utilities']
        ```
        """
        selection_values = [
            "category_group",
            "category",
            "currency",
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
                "currency": currency,
                "exchange": exchange,
                "mic": mic,
            },
            exclude_delisted=False,
            as_pandas=as_pandas,
        )
