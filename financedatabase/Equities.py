"Equities Module"

import pandas as pd

from .helpers import FinanceDatabase


class Equities(FinanceDatabase):
    """
    Public Equity refers to shares or ownershis of a public
    company, i.e., a company that is listed on a public stock
    exchange like the BSE or NYSE. When a company goes public it
    essentially allows the public to buy ownership rights in
    their business.

    This class provides information about the Equities available as well as the
    ability to select specific equities based on the country, sector,
    industry group and industry, adhering to the GICS standard.
    """

    FILE_NAME = "equities.brotli"

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
        Description
        ----
        Returns all equities when no input is given and has the option to give
        a specific set of symbols for the country, sector and/or industry provided.

        The data depends on the combination of inputs. For example Country + Sector
        gives all symbols for a specific sector in a specific country.

        Input
        ----
        country (string, default is None)
            If filled, gives all data for a specific country.
        sector (string, default is None)
            If filled, gives all data for a specific sector.
        industry_group (string, default is None)
            If filled, gives all data for a specific industry group.
        industry (string, default is None)
            If filled, gives all data for a specific industry.
        exclude_exchanges (boolean, default is True):
            Whether you want to exclude exchanges from the search. If False,
            you will receive multiple times the product from different exchanges.
        capitalize (boolean, default is True):
            Whether country, sector and industry needs to be capitalized. By default
            the values always are capitalized as that is also how it is represented
            in the csv files.
        base_url (string, default is GitHub location)
            The possibility to enter your own location if desired.
        use_local_location (string, default False)
            The possibility to select a local location (i.e. based on Windows path)

        Output
        ----
        equities_df (pd.DataFrame)
            Returns a dictionary with a selection or all data based on the input.
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
        return equities

    def options(
        self,
        selection: str,
        country: str = "",
        sector: str = "",
        industry_group: str = "",
        industry: str = "",
    ) -> pd.Series:
        """
        Description
        ----
        Returns all options for the selection provided.

        Input
        ----
        selection (string)
            The selection you want to see the options for. Choose from:
                "currency"
                "sector"
                "industry_group"
                "industry"
                "exchange"
                "market"
                "country"
                "state"
                "zip_code"
                "market_cap"
        country (string, default is None)
            If filled, gives all data for a specific country.
        sector (string, default is None)
            If filled, gives all data for a specific sector.
        industry_group (string, default is None)
            If filled, gives all data for a specific industry group.
        industry (string, default is None)
            If filled, gives all data for a specific industry.
        Output
        ----
        options (pd.Series)
            Returns a series with all options for the selection provided.
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
