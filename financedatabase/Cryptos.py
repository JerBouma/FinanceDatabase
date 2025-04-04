"""Cryptos Module"""

import numpy as np
import pandas as pd

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

    def select(
        self,
        cryptocurrency: str | list | None = None,
        currency: str | list | None = None,
    ) -> pd.DataFrame:
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

        Raises:
            ValueError: If the specified cryptocurrency or currency is not available in the database.
                Please check the available cryptocurrencies and currencies using the 'show_options' method.

        Returns:
            A DataFrame containing cryptocurrency data matching the specified input criteria.
        """
        cryptos = self.data.copy(deep=True)

        if cryptocurrency:
            cryptocurrencies = (
                [cryptocurrency] if isinstance(cryptocurrency, str) else cryptocurrency
            )
            cryptocurrencies_lower = [crypto.lower() for crypto in cryptocurrencies]
            options_lower = [
                option.lower()
                for option in self.show_options(selection="cryptocurrency")
            ]

            for cryptocurrency_lower, cryptocurrency_actual in zip(
                cryptocurrencies_lower, cryptocurrencies
            ):
                if cryptocurrency_lower not in options_lower:
                    raise ValueError(
                        f"The cryptocurrency '{cryptocurrency_actual}' is not available in the database. "
                        "Please check the available cryptocurrencies using the 'show_options' method."
                    )
            cryptos = cryptos[
                cryptos["cryptocurrency"].str.lower().isin(cryptocurrencies_lower)
            ]
        if currency:
            currencies = [currency] if isinstance(currency, str) else currency
            currencies_lower = [currency.lower() for currency in currencies]
            options_lower = [
                option.lower() for option in self.show_options(selection="currency")
            ]

            for currency_lower, currency_actual in zip(currencies_lower, currencies):
                if currency_lower not in options_lower:
                    raise ValueError(
                        f"The currency '{currency_actual}' is not available in the database. "
                        "Please check the available currencies using the 'show_options' method."
                    )
            cryptos = cryptos[cryptos["currency"].str.lower().isin(currencies_lower)]

        return FinanceFrame(cryptos)

    def show_options(
        self,
        selection: str | None = None,
        cryptocurrency: str | list | None = None,
        currency: str | list | None = None,
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

        Raises:
            ValueError: If the selection variable provided is not valid.
                Choose from "cryptocurrency" or "currency".

        Returns:
            dict | np.ndarray: A dictionary or array containing the available options
                for the specified selection.
        """
        selection_values = ["cryptocurrency", "currency"]

        if selection is not None and selection not in selection_values:
            raise ValueError(
                f"The selection variable provided is not valid, "
                f"choose from {', '.join(selection_values)}"
            )

        cryptos = self.select(
            cryptocurrency=cryptocurrency,
            currency=currency,
        )

        return (
            {
                column: cryptos[column].dropna().sort_values().unique()
                for column in selection_values
            }
            if selection is None
            else cryptos[selection].dropna().sort_values().unique()
        )
