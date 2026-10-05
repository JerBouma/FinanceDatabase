"""Currencies Module"""

__docformat__ = "google"

import numpy as np
import polars as pl

from financedatabase.database_controller import FinanceDatabase
from financedatabase.frame_model import FinanceFrame


class Currencies(FinanceDatabase):
    """
    Currency is a medium of exchange for goods and services. In short,
    it's money, in the form of paper and coins, usually issued by a
    government and generally accepted at its face value as a method of payment.
    Currency is the primary medium of exchange in the modern world, having
    long ago replaced bartering as a means of trading goods and services.

    This class provides information about the currencies available as well as the
    ability to select specific currencies based on the currency.
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
            base_currency (str | list, optional): Specific base currency or list of base
                currencies to filter currencies on. Defaults to None (all base currencies).
            quote_currency (str | list, optional): Specific quote currency or list of quote
                currencies to filter currencies on. Defaults to None (all quote currencies).
            as_pandas (bool, optional): Whether to return a pandas DataFrame (True) or a
                Polars DataFrame (False). Defaults to True.

        Returns:
            FinanceFrame | pl.DataFrame: The currencies matching every filter.

        Raises:
            ValueError: If a filter value is not available in the database. Check the
                available values with the 'show_options' method.

        As an example:

        ```python
        import financedatabase as fd

        currencies = fd.Currencies()

        currencies.select(base_currency="EUR")[
            ["name", "base_currency", "quote_currency", "exchange"]
        ].head()
        ```

        Which returns:

        | symbol   | name    | base_currency | quote_currency | exchange |
        |:---------|:--------|:--------------|:---------------|:---------|
        | EURAED=X | EUR/AED | EUR           | AED            | CCY      |
        | EURAFN=X | EUR/AFN | EUR           | AFN            | CCY      |
        | EURALL=X | EUR/ALL | EUR           | ALL            | CCY      |
        | EURAMD=X | EUR/AMD | EUR           | AMD            | CCY      |
        | EURANG=X | EUR/ANG | EUR           | ANG            | CCY      |
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
            selection (str | None, optional): The column to show the options of. Choose
                from: "base_currency", "quote_currency". Defaults to None, which returns the
                options of every column.
            base_currency (str | list, optional): Specific base currency or list of base
                currencies to filter the options on. Defaults to None (all base currencies).
            quote_currency (str | list, optional): Specific quote currency or list of quote
                currencies to filter the options on. Defaults to None (all quote
                currencies).
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
