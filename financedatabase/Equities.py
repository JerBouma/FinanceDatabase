"Equities Module"

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
        country: str | None = None,
        sector: str | None = None,
        industry_group: str | None = None,
        industry: str | None = None,
        currency: str | None = None,
        exchange: str | None = None,
        market: str | None = None,
        market_cap: str | None = None,
        only_primary_listing: bool = False,
    ) -> pd.DataFrame:
        """
        Retrieve equity data based on specified criteria.

        This method allows you to retrieve data for specific equities based on a combination
        of country, sector, industry group, and industry filters. You can also exclude
        exchanges from the search. If no input criteria are provided, it returns data for all equities.

        Args:
            country (str, optional):
                Specific country to retrieve data for. If not provided, returns data for all countries.
            sector (str, optional):
                Specific sector to retrieve data for. If not provided, returns data for all sectors.
            industry_group (str, optional):
                Specific industry group to retrieve data for. If not provided, returns data for all industry groups.
            industry (str, optional):
                Specific industry to retrieve data for. If not provided, returns data for all industries.
            currency (str, optional):
                Specific currency to retrieve data for. If not provided, returns data for all currencies.
            exchange (str, optional):
                Specific exchange to retrieve data for. If not provided, returns data for all exchanges.
            market (str, optional):
                Specific market to retrieve data for. If not provided, returns data for all markets.
            market_cap (str, optional):
                Specific market cap to retrieve data for. If not provided, returns data for all market caps
            only_primary_listing (bool, optional):
                Whether to only include the primary listing. If False, you will receive
                data for equities from different exchanges. Default is False.

        Returns:
            pd.DataFrame:
                A DataFrame containing equity data matching the specified input criteria.
        """
        equities = self.data.copy(deep=True)

        if country:
            country_lower = country.lower()
            options_lower = [
                option.lower() for option in self.show_options(selection="country")
            ]
            if country_lower not in options_lower:
                raise ValueError(
                    f"The country '{country}' is not available in the database. "
                    "Please check the available countries using the 'show_options' method."
                )

            equities = equities[equities["country"].str.lower() == country_lower]
        if sector:
            sector_lower = sector.lower()
            options_lower = [
                option.lower() for option in self.show_options(selection="sector")
            ]
            if sector_lower not in options_lower:
                raise ValueError(
                    f"The sector '{sector}' is not available in the database. "
                    "Please check the available sectors using the 'show_options' method."
                )

            equities = equities[equities["sector"].str.lower() == sector_lower]
        if industry_group:
            industry_group_lower = industry_group.lower()
            options_lower = [
                option.lower()
                for option in self.show_options(selection="industry_group")
            ]
            if industry_group_lower not in options_lower:
                raise ValueError(
                    f"The industry group '{industry_group}' is not available in the database. "
                    "Please check the available industry groups using the 'show_options' method."
                )

            equities = equities[
                equities["industry_group"].str.lower() == industry_group_lower
            ]
        if industry:
            industry_lower = industry.lower()
            options_lower = [
                option.lower() for option in self.show_options(selection="industry")
            ]
            if industry_lower not in options_lower:
                raise ValueError(
                    f"The industry '{industry}' is not available in the database. "
                    "Please check the available industries using the 'show_options' method."
                )

            equities = equities[equities["industry"].str.lower() == industry_lower]
        if currency:
            currency_lower = currency.lower()
            options_lower = [
                option.lower() for option in self.show_options(selection="currency")
            ]
            if currency_lower not in options_lower:
                raise ValueError(
                    f"The currency '{currency}' is not available in the database. "
                    "Please check the available currencies using the 'show_options' method."
                )

            equities = equities[equities["currency"].str.lower() == currency_lower]
        if exchange:
            exchange_lower = exchange.lower()
            options_lower = [
                option.lower() for option in self.show_options(selection="exchange")
            ]
            if exchange_lower not in options_lower:
                raise ValueError(
                    f"The exchange '{exchange}' is not available in the database. "
                    "Please check the available exchanges using the 'show_options' method."
                )

            equities = equities[equities["exchange"].str.lower() == exchange_lower]
        if market:
            market_lower = market.lower()
            options_lower = [
                option.lower() for option in self.show_options(selection="market")
            ]
            if market_lower not in options_lower:
                raise ValueError(
                    f"The market '{market}' is not available in the database. "
                    "Please check the available markets using the 'show_options' method."
                )

            equities = equities[equities["market"].str.lower() == market_lower]
        if market_cap:
            market_cap_lower = market_cap.lower()
            options_lower = [
                option.lower() for option in self.show_options(selection="market_cap")
            ]
            if market_cap_lower not in options_lower:
                raise ValueError(
                    f"The market cap '{market_cap}' is not available in the database. "
                    "Please check the available market caps using the 'show_options' method."
                )

            equities = equities[equities["market_cap"].str.lower() == market_cap_lower]

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
        country: str | None = None,
        sector: str | None = None,
        industry_group: str | None = None,
        industry: str | None = None,
        currency: str | None = None,
        exchange: str | None = None,
        market: str | None = None,
        market_cap: str | None = None,
    ) -> pd.Series:
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
            country (str, optional):
                Specific country to retrieve data for. If not provided, returns data for all countries.
            sector (str, optional):
                Specific sector to retrieve data for. If not provided, returns data for all sectors.
            industry_group (str, optional):
                Specific industry group to retrieve data for. If not provided, returns data for all industry groups.
            industry (str, optional):
                Specific industry to retrieve data for. If not provided, returns data for all industries.
            exchange (str, optional):
                Specific exchange to retrieve data for. If not provided, returns data for all exchanges.
            market (str, optional):
                Specific market to retrieve data for. If not provided, returns data for all markets.
            market_cap (str, optional):
                Specific market cap to retrieve data for. If not provided, returns data for all market caps.

        Returns:
            pd.Series:
                A series with all options for the specified selection, sorted and without duplicates.
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
            only_primary_listing=False,
        )

        return (
            {
                column: equities[column].dropna().sort_values().unique()
                for column in selection_values
            }
            if selection is None
            else equities[selection].dropna().sort_values().unique()
        )
