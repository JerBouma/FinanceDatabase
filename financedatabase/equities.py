"Equities Module"

import pandas as pd

from .helpers import FinanceDatabase


class Equities(FinanceDatabase):
    """
    "Equities Class
    """

    FILE_NAME = "equities.csv"

    def select(
        self,
        country: str = "",
        sector: str = "",
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
            country, sector, industry = (
                country.title(),
                sector.title(),
                industry.title(),
            )

        if country:
            equities = equities[equities["country"] == country]
        if sector:
            equities = equities[equities["sector"] == sector]
        if industry:
            equities = equities[equities["industry"] == industry]
        if exclude_exchanges:
            equities = equities[~equities.index.str.contains(r"\.", na=False)]
        return equities

    def options(
        self, selection: str, country: str = "", sector: str = "", industry: str = ""
    ) -> pd.Series:
        """
        Description
        ----
        Returns all options for the selection provided.

        Input
        ----
        selection (string)
            The selection you want to see the options for. Can be:
            - country
            - sector
            - industry
        country (string, default is None)
            If filled, gives all data for a specific country.
        sector (string, default is None)
            If filled, gives all data for a specific sector.
        industry (string, default is None)
            If filled, gives all data for a specific industry.
        Output
        ----
        options (pd.Series)
            Returns a series with all options for the selection provided.
        """
        if selection not in ["country", "sector", "industry"]:
            raise ValueError("The selection provided is not valid.")

        equities = self.select(country=country, sector=sector, industry=industry, exclude_exchanges=False)

        if equities.empty:
            # Meant for the rare cases where capitalizing is not working as desired.
            equities = self.select(
                country=country, sector=sector, industry=industry, capitalize=False, exclude_exchanges=False
            )

        return equities[selection].dropna().sort_values().unique()
