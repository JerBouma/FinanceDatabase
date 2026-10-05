"""Cryptos Module"""

__docformat__ = "google"

import numpy as np
import polars as pl

from financedatabase.database_controller import FinanceDatabase
from financedatabase.frame_model import FinanceFrame


class Cryptos(FinanceDatabase):
    """
    A cryptocurrency is a digital or virtual currency secured by
    cryptography, which makes it nearly impossible to counterfeit
    or double-spend. Many cryptocurrencies are decentralized networks
    based on blockchain technology—a distributed ledger enforced by
    a disparate network of computers. A defining feature of cryptocurrencies
    is that they are generally not issued by any central authority,
    rendering them theoretically immune to government interference
    or manipulation. This decentralized structure appeals to many
    investors who are looking for an alternative to traditional
    financial systems.

    This class provides information about the cryptocurrencies available as
    well as the ability to select specific cryptocurrencies based on the currency.
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
            cryptocurrency (str | list, optional): Specific cryptocurrency or list of
                cryptocurrencies to filter cryptocurrencies on. Defaults to None (all
                cryptocurrencies).
            currency (str | list, optional): Specific currency or list of currencies to
                filter cryptocurrencies on. Defaults to None (all currencies).
            as_pandas (bool, optional): Whether to return a pandas DataFrame (True) or a
                Polars DataFrame (False). Defaults to True.

        Returns:
            FinanceFrame | pl.DataFrame: The cryptocurrencies matching every filter.

        Raises:
            ValueError: If a filter value is not available in the database. Check the
                available values with the 'show_options' method.

        As an example:

        ```python
        import financedatabase as fd

        cryptos = fd.Cryptos()

        cryptos.select(cryptocurrency="ETH")[["name", "cryptocurrency", "currency", "exchange"]]
        ```

        Which returns:

        | symbol  | name         | cryptocurrency | currency | exchange |
        |:--------|:-------------|:---------------|:---------|:---------|
        | ETH-BTC | Ethereum BTC | ETH            | BTC      | CCC      |
        | ETH-CAD | Ethereum CAD | ETH            | CAD      | CCC      |
        | ETH-EUR | Ethereum EUR | ETH            | EUR      | CCC      |
        | ETH-GBP | Ethereum GBP | ETH            | GBP      | CCC      |
        | ETH-USD | Ethereum USD | ETH            | USD      | CCC      |
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
            selection (str | None, optional): The column to show the options of. Choose
                from: "cryptocurrency", "currency". Defaults to None, which returns the
                options of every column.
            cryptocurrency (str | list, optional): Specific cryptocurrency or list of
                cryptocurrencies to filter the options on. Defaults to None (all
                cryptocurrencies).
            currency (str | list, optional): Specific currency or list of currencies to
                filter the options on. Defaults to None (all currencies).
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
