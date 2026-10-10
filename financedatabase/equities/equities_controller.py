"""Equities Module"""

__docformat__ = "google"

import numpy as np
import polars as pl

from financedatabase.database_controller import FinanceDatabase
from financedatabase.frame_model import FinanceFrame


class Equities(FinanceDatabase):
    """
    Public Equity refers to shares or ownership of a public
    company, i.e., a company that is listed on a public stock
    exchange like the BSE or NYSE. When a company goes public it
    essentially allows the public to buy ownership rights in
    their business.

    This class provides information about the Equities available as well as the
    ability to select specific equities based on the country, sector,
    industry group and industry, adhering to the GICS standard.
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
        Select equities based on the country, sector, industry group, industry and other criteria.

        Filters follow the GICS standard. Returns all equities when no input is given.

        Args:
            country (str | list, optional): Specific country or list of countries to filter
                equities on. Defaults to None (all countries).
            sector (str | list, optional): Specific sector or list of sectors to filter
                equities on. Defaults to None (all sectors).
            industry_group (str | list, optional): Specific industry group or list of
                industry groups to filter equities on. Defaults to None (all industry
                groups).
            industry (str | list, optional): Specific industry or list of industries to
                filter equities on. Defaults to None (all industries).
            currency (str | list, optional): Specific currency or list of currencies to
                filter equities on. Defaults to None (all currencies).
            exchange (str | list, optional): Specific exchange or list of exchanges to
                filter equities on. Defaults to None (all exchanges).
            mic (str | list, optional): Specific MIC or list of MICs to filter equities on.
                Defaults to None (all MICs).
            market (str | list, optional): Specific market or list of markets to filter
                equities on. Defaults to None (all markets).
            market_cap (str | list, optional): Specific market cap or list of market caps to
                filter equities on. Defaults to None (all market caps).
            only_primary_listing (bool, optional): Whether to only include primary listings
                (per instrument its listing on the main exchange of its home market, see
                listings_model). Defaults to False.
            exclude_delisted (bool, optional): Whether to exclude delisted equities.
                Defaults to True.
            as_pandas (bool, optional): Whether to return a pandas DataFrame (True) or a
                Polars DataFrame (False). Defaults to True.

        Returns:
            FinanceFrame | pl.DataFrame: The equities matching every filter.

        Raises:
            ValueError: If a filter value is not available in the database. Check the
                available values with the 'show_options' method.

        As an example:

        ```python
        import financedatabase as fd

        equities = fd.Equities()

        equities.select(country="Netherlands", sector="Financials", only_primary_listing=True)[
            ["name", "currency", "industry", "exchange", "market_cap"]
        ].head()
        ```

        Which returns:

        | symbol   | name                                   | currency | industry         | exchange | market_cap |
        |:---------|:---------------------------------------|:---------|:-----------------|:---------|:-----------|
        | ABN.AS   | ABN AMRO Bank N.V. Depositary receipts | EUR      | Banks            | AMS      | Large Cap  |
        | AGN.AS   | Aegon N.V.                             | EUR      | Insurance        | AMS      | Large Cap  |
        | ASAI.L   | ASA International Group PLC            | GBP      | Consumer Finance | LSE      | Small Cap  |
        | ASRNL.AS | ASR Nederland N.V.                     | EUR      | Insurance        | AMS      | Large Cap  |
        | CNCK     | Coincheck Group N.V. Ordinary Shares   | USD      | Consumer Finance | NMS      | Micro Cap  |
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
            selection (str | None, optional): The column to show the options of. Choose
                from: "country", "sector", "industry_group", "industry", "currency",
                "exchange", "mic", "market", "market_cap". Defaults to None, which returns
                the options of every column.
            country (str | list, optional): Specific country or list of countries to filter
                the options on. Defaults to None (all countries).
            sector (str | list, optional): Specific sector or list of sectors to filter the
                options on. Defaults to None (all sectors).
            industry_group (str | list, optional): Specific industry group or list of
                industry groups to filter the options on. Defaults to None (all industry
                groups).
            industry (str | list, optional): Specific industry or list of industries to
                filter the options on. Defaults to None (all industries).
            currency (str | list, optional): Specific currency or list of currencies to
                filter the options on. Defaults to None (all currencies).
            exchange (str | list, optional): Specific exchange or list of exchanges to
                filter the options on. Defaults to None (all exchanges).
            mic (str | list, optional): Specific MIC or list of MICs to filter the options
                on. Defaults to None (all MICs).
            market (str | list, optional): Specific market or list of markets to filter the
                options on. Defaults to None (all markets).
            market_cap (str | list, optional): Specific market cap or list of market caps to
                filter the options on. Defaults to None (all market caps).
            exclude_delisted (bool, optional): Whether to exclude delisted equities.
                Defaults to True.
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
