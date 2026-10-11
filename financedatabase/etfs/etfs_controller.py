"""ETFs Module"""

__docformat__ = "google"

import numpy as np
import polars as pl

from financedatabase.database_controller import FinanceDatabase
from financedatabase.frame_model import FinanceFrame


class ETFs(FinanceDatabase):
    """
    Exchange-traded funds, selectable by category group, category, family and more.
    """

    FILE_NAME = "etfs.bz2"
    HAS_LISTINGS = True
    PLURAL_NAME = "etfs"
    FIELDS = {
        "category_group": ("category group", "category groups"),
        "category": ("category", "categories"),
        "family": ("family", "families"),
        "currency": ("currency", "currencies"),
        "exchange": ("exchange", "exchanges"),
        "mic": ("MIC", "MICs"),
    }

    def select(
        self,
        category_group: str | list | None = None,
        category: str | list | None = None,
        family: str | list | None = None,
        currency: str | list | None = None,
        exchange: str | list | None = None,
        mic: str | list | None = None,
        only_primary_listing: bool = False,
        exclude_delisted: bool = True,
        as_pandas: bool = True,
    ) -> FinanceFrame | pl.DataFrame:
        """
        Select ETFs based on the category group, category, family and other criteria.

        Returns all ETFs when no input is given.

        Args:
            category_group (str | list, optional): Category groups to filter on.
            category (str | list, optional): Categories to filter on.
            family (str | list, optional): Families to filter on.
            currency (str | list, optional): Currencies to filter on.
            exchange (str | list, optional): Exchanges to filter on.
            mic (str | list, optional): MICs to filter on.
            only_primary_listing (bool, optional): Only primary listings. Defaults to False.
            exclude_delisted (bool, optional): Exclude delisted ETFs. Defaults to True.
            as_pandas (bool, optional): Return pandas, else Polars. Defaults to True.

        Returns:
            FinanceFrame | pl.DataFrame: The ETFs matching every filter.

        Raises:
            ValueError: If a filter value is not available, see show_options.

        As an example:

        ```python
        import financedatabase as fd

        etfs = fd.ETFs()

        etfs.select(
            category_group="Equities",
            category="Large Cap",
            family="BlackRock Asset Management",
            only_primary_listing=True,
        )[["name", "currency", "category", "exchange"]].head()
        ```
        """
        return self._select_rows(
            {
                "category_group": category_group,
                "category": category,
                "family": family,
                "currency": currency,
                "exchange": exchange,
                "mic": mic,
            },
            only_primary_listing=only_primary_listing,
            exclude_delisted=exclude_delisted,
            as_pandas=as_pandas,
        )

    def show_options(
        self,
        selection: str | None = None,
        category_group: str | list | None = None,
        category: str | list | None = None,
        family: str | list | None = None,
        currency: str | list | None = None,
        exchange: str | list | None = None,
        mic: str | list | None = None,
        exclude_delisted: bool = True,
        as_pandas: bool = True,
    ) -> dict | np.ndarray | pl.Series:
        """
        Show the available values of the ETFs filters.

        The options can be narrowed down with the same filters as select().

        Args:
            selection (str | None, optional): The filter to show, None for every filter.
            category_group (str | list, optional): Category groups to filter on.
            category (str | list, optional): Categories to filter on.
            family (str | list, optional): Families to filter on.
            currency (str | list, optional): Currencies to filter on.
            exchange (str | list, optional): Exchanges to filter on.
            mic (str | list, optional): MICs to filter on.
            exclude_delisted (bool, optional): Exclude delisted ETFs. Defaults to True.
            as_pandas (bool, optional): Return numpy arrays, else Polars. Defaults to True.

        Returns:
            dict | np.ndarray | pl.Series: The sorted values, a dict for every filter.

        Raises:
            ValueError: If the selection or a filter value is not valid.

        As an example:

        ```python
        import financedatabase as fd

        etfs = fd.ETFs()

        etfs.show_options(selection="category", category_group="Fixed Income")
        ```
        """
        selection_values = [
            "currency",
            "category_group",
            "category",
            "family",
            "exchange",
            "mic",
        ]
        return self._collect_options(
            selection,
            selection_values,
            f"The selection variable provided is not valid, "
            f"choose from {', '.join(selection_values)}",
            {
                "category_group": category_group,
                "category": category,
                "family": family,
                "currency": currency,
                "exchange": exchange,
                "mic": mic,
            },
            exclude_delisted=exclude_delisted,
            as_pandas=as_pandas,
        )
