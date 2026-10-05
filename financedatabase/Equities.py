"Equities Module"

import numpy as np

from .helpers import FinanceDatabase, FinanceFrame


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
    ) -> FinanceFrame:
        """
        Retrieve equity data based on specified criteria.

        This method allows you to retrieve data for specific equities based on a combination
        of country, sector, industry group, and industry filters. You can also exclude
        exchanges from the search. If no input criteria are provided, it returns data for all equities.

        Args:
            country (str | list | None): Specific country or list of countries to filter equities.
                If not provided, returns data for all countries.
            sector (str | list | None): Specific sector or list of sectors to filter equities.
                If not provided, returns data for all sectors.
            industry_group (str | list | None): Specific industry group or list of industry groups
                to filter equities. If not provided, returns data for all industry groups.
            industry (str | list | None): Specific industry or list of industries to filter equities.
                If not provided, returns data for all industries.
            currency (str | list | None): Specific currency or list of currencies to filter equities.
                If not provided, returns data for all currencies.
            exchange (str | list | None): Specific exchange or list of exchanges to filter equities.
                If not provided, returns data for all exchanges.
            mic (str | list | None): Specific ISO 10383 MIC code or list of MIC codes to filter
                equities. If not provided, returns data for all MIC codes.
            market (str | list | None): Specific market or list of markets to filter equities.
                If not provided, returns data for all markets.
            market_cap (str | list | None): Specific market cap or list of market caps to filter equities.
                If not provided, returns data for all market caps.
            only_primary_listing (bool, optional): Whether to only include the primary listing.
                If False, you will receive data for equities from different exchanges.
                Default is False.
            exclude_delisted (bool, optional): Whether to exclude delisted equities.
                If True, delisted equities will be excluded from the results.
                Default is True.
            as_pandas (bool, optional): Return a pandas DataFrame (True, the default) or a
                Polars DataFrame (False).

        Raises:
            ValueError: If any of the specified criteria are not available in the database.
                Please check the available options using the 'show_options' method.

        Returns:
            FinanceFrame:
                A DataFrame containing equity data matching the specified input criteria.
        """
        return self._select(
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
    ) -> dict | np.ndarray:
        """
        Retrieve all options for the specified selection.

        This method returns a series containing all available options for the specified
        selection, which can be one of the following: "currency", "sector", "industry_group",
        "industry", "exchange", "market", "country", "market_cap".

        Args:
            selection (str):
                The selection you want to see the options for. Choose from:
                "currency", "sector", "industry_group", "industry", "exchange",
                "market", "country", "state", "zip_code", "market_cap".
                If None, returns all options for the specified country, sector, industry group
                and industry.
            country (str | list | None): Specific country or list of countries to filter options.
                If not provided, returns data for all countries.
            sector (str | list | None): Specific sector or list of sectors to filter options.
                If not provided, returns data for all sectors.
            industry_group (str | list | None): Specific industry group or list of industry groups
                to filter options. If not provided, returns data for all industry groups.
            industry (str | list | None): Specific industry or list of industries to filter options.
                If not provided, returns data for all industries.
            currency (str | list | None): Specific currency or list of currencies to filter options.
                If not provided, returns data for all currencies.
            exchange (str | list | None): Specific exchange or list of exchanges to filter options.
                If not provided, returns data for all exchanges.
            market (str | list | None): Specific market or list of markets to filter options.
                If not provided, returns data for all markets.
            market_cap (str | list | None): Specific market cap or list of market caps to filter options.
                If not provided, returns data for all market caps.
            as_pandas (bool, optional): Return the options as numpy arrays (True, the default)
                or as Polars Series (False).


        Raises:
            ValueError: If the selection variable provided is not valid.
                Please check the available options using the 'show_options' method.

        Returns:
            dict | np.ndarray: A dictionary or array with all options for the specified selection.
                If selection is None, returns a dictionary with unique values for all fields.
                If selection is specified, returns an array of unique values for that field.
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
        return self._show_options(
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
