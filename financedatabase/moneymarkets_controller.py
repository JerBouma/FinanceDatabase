"""Moneymarkets Module"""

__docformat__ = "google"

import numpy as np
import polars as pl

from financedatabase.database_controller import FinanceDatabase
from financedatabase.frame_controller import FinanceFrame


class Moneymarkets(FinanceDatabase):
    """
    The money market refers to trading in very short-term debt investments.
    At the wholesale level, it involves large-volume trades between institutions
    and traders. At the retail level, it includes money market mutual funds
    bought by individual investors and money market accounts opened
    by bank customers.

    This class provides information about the moneymarkets available as well as the
    ability to select specific moneymarkets based on the currency and family.
    """

    FILE_NAME = "moneymarkets.bz2"
    FIELDS = {
        "currency": ("currency", "currencies"),
        "family": ("family", "families"),
    }

    def select(
        self,
        currency: str | list | None = None,
        family: str | list | None = None,
        as_pandas: bool = True,
    ) -> FinanceFrame | pl.DataFrame:
        """
        Select money markets based on the currency and family.

        Returns all money markets when no input is given.

        Args:
            currency (str | list, optional): Specific currency or list of currencies to
                filter money markets on. Defaults to None (all currencies).
            family (str | list, optional): Specific family or list of families to filter
                money markets on. Defaults to None (all families).
            as_pandas (bool, optional): Whether to return a pandas DataFrame (True) or a
                Polars DataFrame (False). Defaults to True.

        Returns:
            FinanceFrame | pl.DataFrame: The money markets matching every filter.

        Raises:
            ValueError: If a filter value is not available in the database. Check the
                available values with the 'show_options' method.

        As an example:

        ```python
        import financedatabase as fd

        moneymarkets = fd.Moneymarkets()

        moneymarkets.select(family="BlackRock Liquidity Funds")[
            ["name", "currency", "family"]
        ].head()
        ```

        Which returns:

        | symbol | name               | currency | family                    |
        |:-------|:-------------------|:---------|:--------------------------|
        | BCHXX  | T-Fund             | USD      | BlackRock Liquidity Funds |
        | BEMXX  | T-Fund             | USD      | BlackRock Liquidity Funds |
        | BFBXX  | FedFund            | USD      | BlackRock Liquidity Funds |
        | BFCXX  | FedFund            | USD      | BlackRock Liquidity Funds |
        | BFDXX  | Federal Trust Fund | USD      | BlackRock Liquidity Funds |
        """
        return self._select_rows(
            {"currency": currency, "family": family},
            only_primary_listing=False,
            exclude_delisted=False,
            as_pandas=as_pandas,
        )

    def show_options(
        self,
        selection: str | None = None,
        currency: str | list | None = None,
        family: str | list | None = None,
        as_pandas: bool = True,
    ) -> dict | np.ndarray | pl.Series:
        """
        Show the available values of the money markets filters.

        The options can be narrowed down with the same filters as select().

        Args:
            selection (str | None, optional): The column to show the options of. Choose
                from: "currency", "family". Defaults to None, which returns the options of
                every column.
            currency (str | list, optional): Specific currency or list of currencies to
                filter the options on. Defaults to None (all currencies).
            family (str | list, optional): Specific family or list of families to filter the
                options on. Defaults to None (all families).
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

        moneymarkets = fd.Moneymarkets()

        moneymarkets.show_options(selection="currency")
        ```

        Which returns:

        ```
        ['CHF', 'USD']
        ```
        """
        selection_values = ["currency", "family"]
        return self._collect_options(
            selection,
            selection_values,
            f"The selection variable provided is not valid, "
            f"choose from {', '.join(selection_values)}",
            {"currency": currency, "family": family},
            exclude_delisted=False,
            as_pandas=as_pandas,
        )
