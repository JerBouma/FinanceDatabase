"Cryptos Module"

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
    or manipulation. [Source: Investopedia]

    This class provides information about the cryptocurrencies available as
    well as the ability to select specific cryptocurrencies based on the currency.
    """

    FILE_NAME = "cryptos.bz2"

    def select(
        self,
        crypto: str = "",
        currency: str = "",
        capitalize: bool = True,
    ) -> pd.DataFrame:
        """
        Obtain cryptocurrency data based on specified criteria.

        This method allows you to retrieve data for specific cryptocurrencies and currencies,
        with the option to customize the capitalization of cryptocurrency names. If no input
        criteria are provided, it returns data for all cryptocurrencies.

        Args:
            crypto (str, optional):
                Specific cryptocurrency to retrieve data for. If not provided, returns data for all cryptocurrencies.
            currency (str, optional):
                Specific currency to filter by. If not provided, no currency filtering is applied.
            capitalize (bool, optional):
                Indicates whether the cryptocurrency names should be capitalized for matching. Default is True.

        Returns:
            pd.DataFrame:
                A DataFrame containing cryptocurrency data matching the specified input criteria.
        """
        cryptos = self.data.copy(deep=True)

        if crypto:
            cryptos = cryptos[
                cryptos["cryptocurrency"].str.contains(
                    crypto.upper() if capitalize else crypto, na=False
                )
            ]
        if currency:
            cryptos = cryptos[
                cryptos["currency"].str.contains(
                    currency.upper() if capitalize else currency, na=False
                )
            ]

        return FinanceFrame(cryptos)

    def options(self, selection: str) -> pd.Series:
        """
        Retrieve all options for a specified selection.

        This method returns a series containing all available options for the specified
        selection, which can be one of the following: "cryptocurrency", "currency", "exchange", "market".

        Args:
            selection (str):
                The selection you want to see the options for. Choose from:
                - "cryptocurrency"
                - "currency"
                - "exchange"
                - "market"

        Returns:
            pd.Series:
                A series with all options for the specified selection.
        """
        selection_values = ["cryptocurrency", "currency", "exchange", "market"]
        if selection not in selection_values:
            raise ValueError(
                f"The selection variable provided is not valid, "
                f"choose from {', '.join(selection_values)}"
            )
        cryptos = self.select()

        return cryptos[selection].dropna().unique()
