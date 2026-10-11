"""Currencies Module"""

__docformat__ = "google"

import numpy as np
import polars as pl

from financedatabase.database_controller import FinanceDatabase
from financedatabase.frame_model import FinanceFrame


class Currencies(FinanceDatabase):
    """
    Currency pairs, selectable by base and quote currency.
    """

    FILE_NAME = "currencies.bz2"
    FIELDS = {
        "base_currency": ("base currency", "base currencies"),
        "quote_currency": ("quote currency", "quote currencies"),
    }

    def select(
        self,
        base_currency: str | list | None = None,
        quote_currency: str | list | None = None,
        as_pandas: bool = True,
    ) -> FinanceFrame | pl.DataFrame:
        """
        Select currency pairs based on the base and quote currency.

        Returns all currency pairs when no input is given.

        Args:
            base_currency (str | list, optional): Base currencies to filter on.
            quote_currency (str | list, optional): Quote currencies to filter on.
            as_pandas (bool, optional): Return pandas, else Polars. Defaults to True.

        Returns:
            FinanceFrame | pl.DataFrame: The currencies matching every filter.

        Raises:
            ValueError: If a filter value is not available, see show_options.

        As an example:

        ```python
        import financedatabase as fd

        currencies = fd.Currencies()

        currencies.select(base_currency="EUR")[
            ["name", "base_currency", "quote_currency", "exchange"]
        ].head()
        ```
        """
        return self._select_rows(
            {"base_currency": base_currency, "quote_currency": quote_currency},
            only_primary_listing=False,
            exclude_delisted=False,
            as_pandas=as_pandas,
        )

    def show_options(
        self,
        selection: str | None = None,
        base_currency: str | list | None = None,
        quote_currency: str | list | None = None,
        as_pandas: bool = True,
    ) -> dict | np.ndarray | pl.Series:
        """
        Show the available values of the currencies filters.

        The options can be narrowed down with the same filters as select().

        Args:
            selection (str | None, optional): The filter to show, None for every filter.
            base_currency (str | list, optional): Base currencies to filter on.
            quote_currency (str | list, optional): Quote currencies to filter on.
            as_pandas (bool, optional): Return numpy arrays, else Polars. Defaults to True.

        Returns:
            dict | np.ndarray | pl.Series: The sorted values, a dict for every filter.

        Raises:
            ValueError: If the selection or a filter value is not valid.

        As an example:

        ```python
        import financedatabase as fd

        currencies = fd.Currencies()

        currencies.show_options(selection="quote_currency", base_currency="EUR")[:5]
        ```

        Which returns:

        ```
        ['AED', 'AFN', 'ALL', 'AMD', 'ANG']
        ```
        """
        selection_values = ["base_currency", "quote_currency"]
        return self._collect_options(
            selection,
            selection_values,
            f"The selection variable ({selection}) provided is not valid, "
            f"choose from {', '.join(selection_values)}",
            {"base_currency": base_currency, "quote_currency": quote_currency},
            exclude_delisted=False,
            as_pandas=as_pandas,
        )
