"""Cryptos Module"""

__docformat__ = "google"

import numpy as np
import polars as pl

from financedatabase.database_controller import FinanceDatabase
from financedatabase.frame_model import FinanceFrame


class Cryptos(FinanceDatabase):
    """
    Cryptocurrencies, selectable by cryptocurrency and the currency they are quoted in.
    """

    FILE_NAME = "cryptos.bz2"
    FIELDS = {
        "cryptocurrency": ("cryptocurrency", "cryptocurrencies"),
        "currency": ("currency", "currencies"),
    }

    def select(
        self,
        cryptocurrency: str | list | None = None,
        currency: str | list | None = None,
        as_pandas: bool = True,
    ) -> FinanceFrame | pl.DataFrame:
        """
        Select cryptocurrencies based on the cryptocurrency and the currency it is quoted in.

        Returns all cryptocurrencies when no input is given.

        Args:
            cryptocurrency (str | list, optional): Cryptocurrencies to filter on.
            currency (str | list, optional): Currencies to filter on.
            as_pandas (bool, optional): Return pandas, else Polars. Defaults to True.

        Returns:
            FinanceFrame | pl.DataFrame: The cryptocurrencies matching every filter.

        Raises:
            ValueError: If a filter value is not available, see show_options.

        As an example:

        ```python
        import financedatabase as fd

        cryptos = fd.Cryptos()

        cryptos.select(cryptocurrency="ETH")[["name", "cryptocurrency", "currency", "exchange"]]
        ```
        """
        return self._select_rows(
            {"cryptocurrency": cryptocurrency, "currency": currency},
            only_primary_listing=False,
            exclude_delisted=False,
            as_pandas=as_pandas,
        )

    def show_options(
        self,
        selection: str | None = None,
        cryptocurrency: str | list | None = None,
        currency: str | list | None = None,
        as_pandas: bool = True,
    ) -> dict | np.ndarray | pl.Series:
        """
        Show the available values of the cryptocurrencies filters.

        The options can be narrowed down with the same filters as select().

        Args:
            selection (str | None, optional): The filter to show, None for every filter.
            cryptocurrency (str | list, optional): Cryptocurrencies to filter on.
            currency (str | list, optional): Currencies to filter on.
            as_pandas (bool, optional): Return numpy arrays, else Polars. Defaults to True.

        Returns:
            dict | np.ndarray | pl.Series: The sorted values, a dict for every filter.

        Raises:
            ValueError: If the selection or a filter value is not valid.

        As an example:

        ```python
        import financedatabase as fd

        cryptos = fd.Cryptos()

        cryptos.show_options(selection="currency", cryptocurrency="ETH")
        ```

        Which returns:

        ```
        ['BTC', 'CAD', 'EUR', 'GBP', 'USD']
        ```
        """
        selection_values = ["cryptocurrency", "currency"]
        return self._collect_options(
            selection,
            selection_values,
            f"The selection variable provided is not valid, "
            f"choose from {', '.join(selection_values)}",
            {"cryptocurrency": cryptocurrency, "currency": currency},
            exclude_delisted=False,
            as_pandas=as_pandas,
        )
