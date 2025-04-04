"""Moneymarkets Module"""

import numpy as np
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
        self, currency: str | list | None = None, family: str | list | None = None
    ) -> pd.DataFrame:
        """
        Select moneymarkets based on specified criteria.

        Returns all moneymarkets when no input is given and has the option to filter
        based on currency and family.

        Args:
            currency (str | list, optional): Filter by currency.
                Default is None, which returns all currencies.
            family (str | list, optional): Filter by family.
                Default is None, which returns all families.

        Raises:
            ValueError: If the specified currency or family is not available in the database.
                Please check the available currencies and families using the 'show_options' method.

        Returns:
            pd.DataFrame: DataFrame containing the selected moneymarkets data.
        """
        moneymarkets = self.data.copy(deep=True)

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
            moneymarkets = moneymarkets[
                moneymarkets["currency"].str.lower().isin(currencies_lower)
            ]
        if family:
            families = [family] if isinstance(family, str) else family
            families_lower = [family.lower() for family in families]
            options_lower = [
                option.lower() for option in self.show_options(selection="family")
            ]
            for family_lower, family_actual in zip(families_lower, families):
                if family_lower not in options_lower:
                    raise ValueError(
                        f"The family '{family_actual}' is not available in the database. "
                        "Please check the available families using the 'show_options' method."
                    )
            moneymarkets = moneymarkets[
                moneymarkets["family"].str.lower().isin(families_lower)
            ]

        return FinanceFrame(moneymarkets)

    def show_options(
        self,
        selection: str | None = None,
        currency: str | list | None = None,
        family: str | list | None = None,
    ) -> dict | np.ndarray:
        """
        Show available options for the specified selection.

        Args:
            selection (str, optional): The category to show options for.
                Choose from: "currency" or "family". Default is None.
            currency (str | list, optional): Filter by currency.
                Default is None, which returns all currencies.
            family (str | list, optional): Filter by family.
                Default is None, which returns all families.

        Raises:
            ValueError: If the specified selection is not valid.
                Choose from: "currency" or "family".

        Returns:
            dict | np.ndarray: A dictionary containing the available options for the specified selection.
                If selection is None, returns all available options for both currency and family.
                If selection is "currency" or "family", returns the unique values for that selection.
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
