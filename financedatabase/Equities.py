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
        country: str = "",
        sector: str = "",
        industry_group: str = "",
        industry: str = "",
        exclude_exchanges: bool = True,
        capitalize: bool = True,
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
            exclude_exchanges (bool, optional):
                Whether to exclude exchanges from the search. If False, you will receive
                data for equities from different exchanges. Default is True.
            capitalize (bool, optional):
                Indicates whether country, sector, and industry names should be capitalized for matching.
                Default is True.

        Returns:
            pd.DataFrame:
                A DataFrame containing equity data matching the specified input criteria.
        """
        equities = self.data.copy(deep=True)

        if capitalize:
            country, sector, industry_group, industry = (
                country.title(),
                sector.title(),
                industry_group.title(),
                industry.title(),
            )

        if country:
            equities = equities[equities["country"] == country]
        if sector:
            equities = equities[equities["sector"] == sector]
        if industry_group:
            equities = equities[equities["industry_group"] == industry_group]
        if industry:
            equities = equities[equities["industry"] == industry]
        if exclude_exchanges:
            equities = equities[~equities.index.str.contains(r"\.", na=False)]

        return FinanceFrame(equities)

    def options(
        self,
        selection: str,
        country: str = "",
        sector: str = "",
        industry_group: str = "",
        industry: str = "",
    ) -> pd.Series:
        """
        Retrieve all options for the specified selection.

        This method returns a series containing all available options for the specified
        selection, which can be one of the following: "currency", "sector", "industry_group",
        "industry", "exchange", "market", "country", "state", "zip_code", "market_cap".

        Args:
            selection (str):
                The selection you want to see the options for. Choose from:
                - "currency"
                - "sector"
                - "industry_group"
                - "industry"
                - "exchange"
                - "market"
                - "country"
                - "state"
                - "zip_code"
                - "market_cap"
            country (str, optional):
                Specific country to retrieve data for. If not provided, returns data for all countries.
            sector (str, optional):
                Specific sector to retrieve data for. If not provided, returns data for all sectors.
            industry_group (str, optional):
                Specific industry group to retrieve data for. If not provided, returns data for all industry groups.
            industry (str, optional):
                Specific industry to retrieve data for. If not provided, returns data for all industries.

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
            "state",
            "zip_code",
            "market_cap",
        ]
        if selection not in selection_values:
            raise ValueError(
                f"The selection variable provided is not valid, "
                f"choose from {', '.join(selection_values)}"
            )

        equities = self.select(
            country=country,
            sector=sector,
            industry_group=industry_group,
            industry=industry,
            exclude_exchanges=False,
        )

        if equities.empty:
            # Meant for the rare cases where capitalizing is not working as desired.
            equities = self.select(
                country=country,
                sector=sector,
                industry_group=industry_group,
                industry=industry,
                capitalize=False,
                exclude_exchanges=False,
            )

        return equities[selection].dropna().sort_values().unique()
