"""Moneymarkets Module"""

__docformat__ = "google"

import numpy as np
import polars as pl

from financedatabase.database_controller import FinanceDatabase
from financedatabase.frame_model import FinanceFrame


class Moneymarkets(FinanceDatabase):
    """
    Money market funds, selectable by currency and family.
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
            currency (str | list, optional): Currencies to filter on.
            family (str | list, optional): Families to filter on.
            as_pandas (bool, optional): Return pandas, else Polars. Defaults to True.

        Returns:
            FinanceFrame | pl.DataFrame: The money markets matching every filter.

        Raises:
            ValueError: If a filter value is not available, see show_options.

        As an example:

        ```python
        import financedatabase as fd

        moneymarkets = fd.Moneymarkets()

        moneymarkets.select(family="BlackRock Liquidity Funds")[
            ["name", "currency", "family"]
        ].head()
        ```
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
            selection (str | None, optional): The filter to show, None for every filter.
            currency (str | list, optional): Currencies to filter on.
            family (str | list, optional): Families to filter on.
            as_pandas (bool, optional): Return numpy arrays, else Polars. Defaults to True.

        Returns:
            dict | np.ndarray | pl.Series: The sorted values, a dict for every filter.

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
