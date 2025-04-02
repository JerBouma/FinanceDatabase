"""Moneymarkets Module"""

import pandas as pd

from .helpers import FinanceDatabase, FinanceFrame


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

    def select(
        self, currency: str | None = None, family: str | None = None
    ) -> pd.DataFrame:
        """
        Select moneymarkets based on specified criteria.

        Returns all moneymarkets when no input is given and has the option to filter
        based on currency and family.

        Args:
            currency (str, optional): Filter by currency. Default is None.
            family (str, optional): Filter by family. Default is None.

        Returns:
            pd.DataFrame: DataFrame containing the selected moneymarkets data.

        Raises:
            ValueError: If the specified currency or family is not available in the database.
        """
        moneymarkets = self.data.copy(deep=True)

        if currency:
            currency = currency.lower()
            options_lower = [
                option.lower() for option in self.show_options(selection="currency")
            ]
            if currency not in options_lower:
                raise ValueError(
                    f"The currency '{currency}' is not available in the database. "
                    "Please check the available currencies using the 'options' method."
                )
            moneymarkets = moneymarkets[
                moneymarkets["currency"].str.lower() == currency
            ]

        if family:
            family = family.lower()
            options_lower = [
                option.lower() for option in self.show_options(selection="family")
            ]
            if family not in options_lower:
                raise ValueError(
                    f"The family '{family}' is not available in the database. "
                    "Please check the available families using the 'options' method."
                )
            moneymarkets = moneymarkets[moneymarkets["family"].str.lower() == family]

        return FinanceFrame(moneymarkets)

    def show_options(
        self,
        selection: str | None = None,
        currency: str | None = None,
        family: str | None = None,
    ) -> pd.Series:
        """
        Show available options for the specified selection.

        Args:
            selection (str, optional): The category to show options for.
                                      Choose from: "currency" or "family".
                                      Default is None.
            currency (str, optional): Filter by currency. Default is None.
            family (str, optional): Filter by family. Default is None.

        Returns:
            pd.Series: Series containing available options for the specified selection.

        Raises:
            ValueError: If the selection variable provided is not valid.
        """
        selection_values = ["currency", "family"]

        if selection is not None and selection not in selection_values:
            raise ValueError(
                f"The selection variable provided is not valid, "
                f"choose from {', '.join(selection_values)}"
            )

        moneymarkets = self.select(currency=currency, family=family)

        return (
            {
                column: moneymarkets[column].dropna().sort_values().unique()
                for column in selection_values
            }
            if selection is None
            else moneymarkets[selection].dropna().sort_values().unique()
        )
