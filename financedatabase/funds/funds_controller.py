"""Funds Module"""

__docformat__ = "google"

import numpy as np
import polars as pl

from financedatabase.database_controller import FinanceDatabase
from financedatabase.frame_model import FinanceFrame


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
    HAS_LISTINGS = True
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
    ) -> FinanceFrame | pl.DataFrame:
        """
        Select funds based on the category group, category, family and other criteria.

        Returns all funds when no input is given.

        Args:
            category_group (str | list, optional): Specific category group or list of
                category groups to filter funds on. Defaults to None (all category groups).
            category (str | list, optional): Specific category or list of categories to
                filter funds on. Defaults to None (all categories).
            family (str | list, optional): Specific family or list of families to filter
                funds on. Defaults to None (all families).
            currency (str | list, optional): Specific currency or list of currencies to
                filter funds on. Defaults to None (all currencies).
            exchange (str | list, optional): Specific exchange or list of exchanges to
                filter funds on. Defaults to None (all exchanges).
            mic (str | list, optional): Specific MIC or list of MICs to filter funds on.
                Defaults to None (all MICs).
            only_primary_listing (bool, optional): Whether to only include primary listings
                (per instrument its listing on the main exchange of its home market, see
                listings_model). Defaults to False.
            as_pandas (bool, optional): Whether to return a pandas DataFrame (True) or a
                Polars DataFrame (False). Defaults to True.

        Returns:
            FinanceFrame | pl.DataFrame: The funds matching every filter.

        Raises:
            ValueError: If a filter value is not available in the database. Check the
                available values with the 'show_options' method.

        As an example:

        ```python
        import financedatabase as fd

        funds = fd.Funds()

        funds.select(category_group="Equities", category="Growth", family="Fidelity Investments")[
            ["name", "currency", "category", "exchange"]
        ].head()
        ```

        Which returns:

        | symbol        | name                                        | currency | category | exchange |
        |:--------------|:--------------------------------------------|:---------|:---------|:---------|
        | 0P00019F32.TO | Fidelity Global Growth Class Portfolio E2T5 | CAD      | Growth   | TOR      |
        | 0P0001DBVH.TO | Fidelity Global Innovators Class E2T5       | CAD      | Growth   | TOR      |
        | 0P0001DBVR.TO | Fidelity Special Situations Class E3T5      | CAD      | Growth   | TOR      |
        | 0P0001EESI.TO | Fidelity Global Innovators Class E4T5       | CAD      | Growth   | TOR      |
        | 0P0001EESJ.TO | Fidelity Global Innovators Class E5T5       | CAD      | Growth   | TOR      |
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
    ) -> dict | np.ndarray | pl.Series:
        """
        Show the available values of the funds filters.

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

        funds = fd.Funds()

        funds.show_options(selection="category_group")
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
            exclude_delisted=False,
            as_pandas=as_pandas,
        )
