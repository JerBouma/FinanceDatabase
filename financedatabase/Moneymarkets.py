"""Moneymarkets Module"""

import numpy as np

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
    FIELDS = {
        "currency": ("currency", "currencies"),
        "family": ("family", "families"),
    }

    def select(
        self,
        currency: str | list | None = None,
        family: str | list | None = None,
        as_pandas: bool = True,
    ) -> FinanceFrame:
        """
        Select moneymarkets based on specified criteria.

        Returns all moneymarkets when no input is given and has the option to filter
        based on currency and family.

        Args:
            currency (str | list, optional): Filter by currency.
                Default is None, which returns all currencies.
            family (str | list, optional): Filter by family.
                Default is None, which returns all families.
            as_pandas (bool, optional): Return a pandas DataFrame (True, the default) or a
                Polars DataFrame (False).


        Raises:
            ValueError: If the specified currency or family is not available in the database.
                Please check the available currencies and families using the 'show_options' method.

        Returns:
            FinanceFrame: DataFrame containing the selected moneymarkets data.
        """
        return self._select(
            {"currency": currency, "family": family},
            only_primary_listing=False,
            exclude_delisted=False,
            as_pandas=as_pandas,
        )

    def show_options(
        self,
        selection: str | None = None,
        currency: str | list | None = None,
        family: str | list | None = None,
        as_pandas: bool = True,
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
            as_pandas (bool, optional): Return the options as numpy arrays (True, the default)
                or as Polars Series (False).


        Raises:
            ValueError: If the specified selection is not valid.
                Choose from: "currency" or "family".

        Returns:
            dict | np.ndarray: A dictionary containing the available options for the specified selection.
                If selection is None, returns all available options for both currency and family.
                If selection is "currency" or "family", returns the unique values for that selection.
        """
        selection_values = ["currency", "family"]
        return self._show_options(
            selection,
            selection_values,
            f"The selection variable provided is not valid, "
            f"choose from {', '.join(selection_values)}",
            {"currency": currency, "family": family},
            exclude_delisted=False,
            as_pandas=as_pandas,
        )
