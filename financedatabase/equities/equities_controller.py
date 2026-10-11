"""Equities Module"""

__docformat__ = "google"

import numpy as np
import polars as pl

from financedatabase.database_controller import FinanceDatabase
from financedatabase.frame_model import FinanceFrame


class Equities(FinanceDatabase):
    """
    Company shares, selectable by country, sector, industry, exchange and more.
    """

    FILE_NAME = "equities.bz2"
    HAS_LISTINGS = True
    PLURAL_NAME = "equities"
    FIELDS = {
        "country": ("country", "countries"),
        "sector": ("sector", "sectors"),
        "industry_group": ("industry group", "industry groups"),
        "industry": ("industry", "industries"),
        "currency": ("currency", "currencies"),
        "exchange": ("exchange", "exchanges"),
        "mic": ("MIC", "MICs"),
        "market": ("market", "markets"),
        "market_cap": ("market cap", "market caps"),
    }

    def select(
        self,
        country: str | list | None = None,
        sector: str | list | None = None,
        industry_group: str | list | None = None,
        industry: str | list | None = None,
        currency: str | list | None = None,
        exchange: str | list | None = None,
        mic: str | list | None = None,
        market: str | list | None = None,
        market_cap: str | list | None = None,
        only_primary_listing: bool = False,
        exclude_delisted: bool = True,
        as_pandas: bool = True,
    ) -> FinanceFrame | pl.DataFrame:
        """
        Select equities by country, sector, industry group, industry and more.

        Returns all equities when no input is given.

        Args:
            country (str | list, optional): Countries to filter on.
            sector (str | list, optional): Sectors to filter on.
            industry_group (str | list, optional): Industry groups to filter on.
            industry (str | list, optional): Industries to filter on.
            currency (str | list, optional): Currencies to filter on.
            exchange (str | list, optional): Exchanges to filter on.
            mic (str | list, optional): MICs to filter on.
            market (str | list, optional): Markets to filter on.
            market_cap (str | list, optional): Market caps to filter on.
            only_primary_listing (bool, optional): Only primary listings. Defaults to False.
            exclude_delisted (bool, optional): Exclude delisted equities. Defaults to True.
            as_pandas (bool, optional): Return pandas, else Polars. Defaults to True.

        Returns:
            FinanceFrame | pl.DataFrame: The equities matching every filter.

        Raises:
            ValueError: If a filter value is not available, see show_options.

        As an example:

        ```python
        import financedatabase as fd

        equities = fd.Equities()

        equities.select(country="Netherlands", sector="Financials", only_primary_listing=True)[
            ["name", "currency", "industry", "exchange", "market_cap"]
        ].head()
        ```
        """
        return self._select_rows(
            {
                "country": country,
                "sector": sector,
                "industry_group": industry_group,
                "industry": industry,
                "currency": currency,
                "exchange": exchange,
                "mic": mic,
                "market": market,
                "market_cap": market_cap,
            },
            only_primary_listing=only_primary_listing,
            exclude_delisted=exclude_delisted,
            as_pandas=as_pandas,
        )

    def show_options(
        self,
        selection: str | None = None,
        country: str | list | None = None,
        sector: str | list | None = None,
        industry_group: str | list | None = None,
        industry: str | list | None = None,
        currency: str | list | None = None,
        exchange: str | list | None = None,
        mic: str | list | None = None,
        market: str | list | None = None,
        market_cap: str | list | None = None,
        exclude_delisted: bool = True,
        as_pandas: bool = True,
    ) -> dict | np.ndarray | pl.Series:
        """
        Show the available values of the equities filters.

        The options can be narrowed down with the same filters as select().

        Args:
            selection (str | None, optional): The filter to show, None for every filter.
            country (str | list, optional): Countries to filter on.
            sector (str | list, optional): Sectors to filter on.
            industry_group (str | list, optional): Industry groups to filter on.
            industry (str | list, optional): Industries to filter on.
            currency (str | list, optional): Currencies to filter on.
            exchange (str | list, optional): Exchanges to filter on.
            mic (str | list, optional): MICs to filter on.
            market (str | list, optional): Markets to filter on.
            market_cap (str | list, optional): Market caps to filter on.
            exclude_delisted (bool, optional): Exclude delisted equities. Defaults to True.
            as_pandas (bool, optional): Return numpy arrays, else Polars. Defaults to True.

        Returns:
            dict | np.ndarray | pl.Series: The sorted values, a dict for every filter.

        Raises:
            ValueError: If the selection or a filter value is not valid.

        As an example:

        ```python
        import financedatabase as fd

        equities = fd.Equities()

        equities.show_options(selection="market_cap", country="Netherlands")
        ```

        Which returns:

        ```
        ['Large Cap', 'Mega Cap', 'Micro Cap', 'Mid Cap', 'Nano Cap', 'Small Cap']
        ```
        """
        selection_values = [
            "currency",
            "sector",
            "industry_group",
            "industry",
            "exchange",
            "mic",
            "market",
            "country",
            "market_cap",
        ]
        return self._collect_options(
            selection,
            selection_values,
            f"The selection variable provided is not valid, "
            f"choose from {', '.join(selection_values)}",
            {
                "country": country,
                "sector": sector,
                "industry_group": industry_group,
                "industry": industry,
                "currency": currency,
                "exchange": exchange,
                "mic": mic,
                "market": market,
                "market_cap": market_cap,
            },
            exclude_delisted=exclude_delisted,
            as_pandas=as_pandas,
        )
