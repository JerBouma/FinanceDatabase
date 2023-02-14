import pandas as pd

from .helpers import file_path


class Equities:
    def __init__(
        self,
        base_url: str = "https://raw.githubusercontent.com/JerBouma/FinanceDatabase/master/Database/equities.csv.zip",
        use_local_location: bool = False,
    ):
        """
        Description
        ----
        Creates a dataframe with all equities from the database.

        Input
        ----
        base_url (string, default is GitHub location)
            The possibility to enter your own location if desired.
        use_local_location (string, default False)
            The possibility to select a local location (i.e. based on Windows path)
        """
        the_path = file_path / "equities.csv.zip" if use_local_location else base_url
        self.equities = pd.read_csv(
            the_path, compression="zip", on_bad_lines="skip", sep=";", index_col=0
        )

    def select(
        self,
        country: str = "",
        sector: str = "",
        industry: str = "",
        exclude_exchanges: bool = True,
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
            you will receive multiple times i.e. Tesla from different exchanges.
        base_url (string, default is GitHub location)
            The possibility to enter your own location if desired.
        use_local_location (string, default False)
            The possibility to select a local location (i.e. based on Windows path)

        Output
        ----
        equities_df (pd.DataFrame)
            Returns a dictionary with a selection or all data based on the input.
        """
        equities = self.equities.copy(deep=True)
        if country:
            equities = equities[equities["country"] == country]
        if sector:
            equities = equities[equities["sector"] == sector]
        if industry:
            equities = equities[equities["industry"] == industry]
        if exclude_exchanges:
            equities = equities[equities.index.str.contains(".", na=False)]
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

        Output
        ----
        options (pd.Series)
            Returns a series with all options for the selection provided.
        """
        if selection not in ["country", "sector", "industry"]:
            raise ValueError("The selection provided is not valid.")

        equities = self.select(country=country, sector=sector, industry=industry)
        return equities[selection].unique()
