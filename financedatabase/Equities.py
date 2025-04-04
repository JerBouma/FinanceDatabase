"Equities Module"

import numpy as np
import pandas as pd

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

    def select(
        self,
        country: str | list | None = None,
        sector: str | list | None = None,
        industry_group: str | list | None = None,
        industry: str | list | None = None,
        currency: str | list | None = None,
        exchange: str | list | None = None,
        market: str | list | None = None,
        market_cap: str | list | None = None,
        only_primary_listing: bool = False,
    ) -> pd.DataFrame:
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
            market (str | list | None): Specific market or list of markets to filter equities.
                If not provided, returns data for all markets.
            market_cap (str | list | None): Specific market cap or list of market caps to filter equities.
                If not provided, returns data for all market caps.
            only_primary_listing (bool, optional): Whether to only include the primary listing.
                If False, you will receive data for equities from different exchanges.
                Default is False.
        Raises:
            ValueError: If any of the specified criteria are not available in the database.
                Please check the available options using the 'show_options' method.

        Returns:
            pd.DataFrame:
                A DataFrame containing equity data matching the specified input criteria.
        """
        equities = self.data.copy(deep=True)

        if country:
            countries = [country] if isinstance(country, str) else country
            countries_lower = [country.lower() for country in countries]
            options_lower = [
                option.lower() for option in self.show_options(selection="country")
            ]
            for country_lower, country_actual in zip(countries_lower, countries):
                if country_lower not in options_lower:
                    raise ValueError(
                        f"The country '{country_actual}' is not available in the database. "
                        "Please check the available countries using the 'show_options' method."
                    )
            equities = equities[equities["country"].str.lower().isin(countries_lower)]
        if sector:
            sectors = [sector] if isinstance(sector, str) else sector
            sectors_lower = [sector.lower() for sector in sectors]
            options_lower = [
                option.lower() for option in self.show_options(selection="sector")
            ]
            for sector_lower, sector_actual in zip(sectors_lower, sectors):
                if sector_lower not in options_lower:
                    raise ValueError(
                        f"The sector '{sector_actual}' is not available in the database. "
                        "Please check the available sectors using the 'show_options' method."
                    )
            equities = equities[equities["sector"].str.lower().isin(sectors_lower)]
        if industry_group:
            industry_groups = (
                [industry_group] if isinstance(industry_group, str) else industry_group
            )
            industry_groups_lower = [group.lower() for group in industry_groups]
            options_lower = [
                option.lower()
                for option in self.show_options(selection="industry_group")
            ]
            for group_lower, group_actual in zip(
                industry_groups_lower, industry_groups
            ):
                if group_lower not in options_lower:
                    raise ValueError(
                        f"The industry group '{group_actual}' is not available in the database. "
                        "Please check the available industry groups using the 'show_options' method."
                    )
            equities = equities[
                equities["industry_group"].str.lower().isin(industry_groups_lower)
            ]
        if industry:
            industries = [industry] if isinstance(industry, str) else industry
            industries_lower = [industry.lower() for industry in industries]
            options_lower = [
                option.lower() for option in self.show_options(selection="industry")
            ]
            for industry_lower, industry_actual in zip(industries_lower, industries):
                if industry_lower not in options_lower:
                    raise ValueError(
                        f"The industry '{industry_actual}' is not available in the database. "
                        "Please check the available industries using the 'show_options' method."
                    )
            equities = equities[equities["industry"].str.lower().isin(industries_lower)]
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
            equities = equities[equities["currency"].str.lower().isin(currencies_lower)]
        if exchange:
            exchanges = [exchange] if isinstance(exchange, str) else exchange
            exchanges_lower = [exchange.lower() for exchange in exchanges]
            options_lower = [
                option.lower() for option in self.show_options(selection="exchange")
            ]
            for exchange_lower, exchange_actual in zip(exchanges_lower, exchanges):
                if exchange_lower not in options_lower:
                    raise ValueError(
                        f"The exchange '{exchange_actual}' is not available in the database. "
                        "Please check the available exchanges using the 'show_options' method."
                    )
            equities = equities[equities["exchange"].str.lower().isin(exchanges_lower)]
        if market:
            markets = [market] if isinstance(market, str) else market
            markets_lower = [market.lower() for market in markets]
            options_lower = [
                option.lower() for option in self.show_options(selection="market")
            ]
            for market_lower, market_actual in zip(markets_lower, markets):
                if market_lower not in options_lower:
                    raise ValueError(
                        f"The market '{market_actual}' is not available in the database. "
                        "Please check the available markets using the 'show_options' method."
                    )
            equities = equities[equities["market"].str.lower().isin(markets_lower)]
        if market_cap:
            market_caps = [market_cap] if isinstance(market_cap, str) else market_cap
            market_caps_lower = [cap.lower() for cap in market_caps]
            options_lower = [
                option.lower() for option in self.show_options(selection="market_cap")
            ]
            for cap_lower, cap_actual in zip(market_caps_lower, market_caps):
                if cap_lower not in options_lower:
                    raise ValueError(
                        f"The market cap '{cap_actual}' is not available in the database. "
                        "Please check the available market caps using the 'show_options' method."
                    )
            equities = equities[
                equities["market_cap"].str.lower().isin(market_caps_lower)
            ]

        if only_primary_listing:
            only_primary_listings_equities = equities[
                ~equities.index.str.contains(r"\.", na=False)
            ]

            if only_primary_listings_equities.empty:
                # If no primary listings are found, return all equities
                print(
                    "No primary listings found. Returning all equities matching your criteria."
                )
            else:
                # If primary listings are found, filter the equities DataFrame.
                equities = only_primary_listings_equities

        return FinanceFrame(equities)

    def show_options(
        self,
        selection: str | None = None,
        country: str | list | None = None,
        sector: str | list | None = None,
        industry_group: str | list | None = None,
        industry: str | list | None = None,
        currency: str | list | None = None,
        exchange: str | list | None = None,
        market: str | list | None = None,
        market_cap: str | list | None = None,
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
            "market",
            "country",
            "market_cap",
        ]

        if selection is not None and selection not in selection_values:
            raise ValueError(
                f"The selection variable provided is not valid, "
                f"choose from {', '.join(selection_values)}"
            )

        equities = self.select(
            country=country,
            sector=sector,
            industry_group=industry_group,
            industry=industry,
            currency=currency,
            exchange=exchange,
            market=market,
            market_cap=market_cap,
        )

        return (
            {
                column: equities[column].dropna().sort_values().unique()
                for column in selection_values
            }
            if selection is None
            else equities[selection].dropna().sort_values().unique()
        )
