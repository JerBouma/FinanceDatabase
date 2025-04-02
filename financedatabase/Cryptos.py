"""Cryptos Module"""

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
        cryptocurrency: str | None = None,
        currency: str | None = None,
    ) -> pd.DataFrame:
        """
        Obtain cryptocurrency data based on specified criteria.

        This method allows you to retrieve data for specific cryptocurrencies and currencies,
        with the option to customize the capitalization of cryptocurrency names. If no input
        criteria are provided, it returns data for all cryptocurrencies.

        Args:
            cryptocurrency: Specific cryptocurrency to retrieve data for.
                If not provided, returns data for all cryptocurrencies.
            currency: Specific currency to retrieve data for.
                If not provided, returns data for all currencies.

        Returns:
            A DataFrame containing cryptocurrency data matching the specified input criteria.

        Raises:
            ValueError: If the specified cryptocurrency or currency is not available in the database.
        """
        cryptos = self.data.copy(deep=True)

        if cryptocurrency:
            cryptocurrency = cryptocurrency.lower()
            options_lower = [
                option.lower()
                for option in self.show_options(selection="cryptocurrency")
            ]
            if cryptocurrency not in options_lower:
                raise ValueError(
                    f"The cryptocurrency '{cryptocurrency}' is not available in the database. "
                    "Please check the available cryptocurrencies using the 'show_options' method."
                )

            cryptos = cryptos[cryptos["cryptocurrency"].str.lower() == cryptocurrency]
        if currency:
            currency = currency.lower()
            options_lower = [
                option.lower() for option in self.show_options(selection="currency")
            ]
            if currency not in options_lower:
                raise ValueError(
                    f"The currency '{currency}' is not available in the database. "
                    "Please check the available currencies using the 'show_options' method."
                )

            cryptos = cryptos[cryptos["currency"].str.lower() == currency]

        return FinanceFrame(cryptos)

    def show_options(
        self,
        selection: str | None = None,
        cryptocurrency: str | None = None,
        currency: str | None = None,
    ) -> pd.Series:
        """
        Retrieve all options for a specified selection.

        This method returns a series containing all available options for the specified
        selection, which can be one of the following: "cryptocurrency" or "currency".

        Args:
            selection: The selection variable to retrieve options for.
                Valid options are "cryptocurrency" or "currency".
            cryptocurrency: Specific cryptocurrency to filter options.
                If not provided, returns data for all cryptocurrencies.
            currency: Specific currency to filter options.
                If not provided, returns data for all currencies.

        Returns:
            A series with all options for the specified selection.

        Raises:
            ValueError: If the specified selection is not valid.
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
