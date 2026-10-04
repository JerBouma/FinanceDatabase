"""Cryptos Module"""

import numpy as np

from .helpers import FinanceDatabase, FinanceFrame


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
    ) -> FinanceFrame:
        """
        Obtain cryptocurrency data based on specified criteria.

        This method allows you to retrieve data for specific cryptocurrencies and currencies,
        with the option to customize the capitalization of cryptocurrency names. If no input
        criteria are provided, it returns data for all cryptocurrencies.

        Args:
            cryptocurrency (str | list, optional): Specific cryptocurrency to retrieve data for.
                If not provided, returns data for all cryptocurrencies.
            currency (str | list, optional): Specific currency to retrieve data for.
                If not provided, returns data for all currencies.
            as_pandas (bool, optional): Return a pandas DataFrame (True, the default) or a
                Polars DataFrame (False).


        Raises:
            ValueError: If the specified cryptocurrency or currency is not available in the database.
                Please check the available cryptocurrencies and currencies using the 'show_options' method.

        Returns:
            A DataFrame containing cryptocurrency data matching the specified input criteria.
        """
        return self._select(
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
    ) -> dict | np.ndarray:
        """
        Retrieve all options for a specified selection.

        This method returns a series containing all available options for the specified
        selection, which can be one of the following: "cryptocurrency" or "currency".

        Args:
            selection (str | None): The selection you want to see the options for.
                Choose from "cryptocurrency" or "currency".
            cryptocurrency (str | list | None): Specific cryptocurrency to filter options.
                If not provided, returns data for all cryptocurrencies.
            currency (str | list | None): Specific currency to filter options.
                If not provided, returns data for all currencies.
            as_pandas (bool, optional): Return the options as numpy arrays (True, the default)
                or as Polars Series (False).


        Raises:
            ValueError: If the selection variable provided is not valid.
                Choose from "cryptocurrency" or "currency".

        Returns:
            dict | np.ndarray: A dictionary or array containing the available options
                for the specified selection.
        """
        selection_values = ["cryptocurrency", "currency"]
        return self._show_options(
            selection,
            selection_values,
            f"The selection variable provided is not valid, "
            f"choose from {', '.join(selection_values)}",
            {"cryptocurrency": cryptocurrency, "currency": currency},
            exclude_delisted=False,
            as_pandas=as_pandas,
        )
