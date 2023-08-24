"Helper Module"

from pathlib import Path

import pandas as pd

file_path = Path(__file__).parent.parent / "compression"
DATA_REPO = (
    "https://raw.githubusercontent.com/JerBouma/FinanceDatabase/main/compression/"
)


class FinanceDatabase:
    """
    The FinanceDatabase serves the role of providing anyone with any type of
    financial product categorisation entirely for free. It features 300.000+
    symbols containing Equities, ETFs, Funds, Indices, Currencies, Cryptocurrencies
    and Money Markets. It therefore allows you to obtain a broad overview of
    sectors, industries, types of investments and much more.

    This class is the base controller of all other classes that are named
    after their corresponding asset class.
    """

    FILE_NAME = ""

    def __init__(
        self,
        base_url: str = DATA_REPO,
        use_local_location: bool = False,
    ):
        """
        Description
        ----
        Reads in the database from the csv file corresponding to the
        asset class. This can be locally as well as remotely stored.

        Input
        ----
        base_url (string, default is GitHub location)
            The possibility to enter your own location if desired.
        use_local_location (string, default False)
            The possibility to select a local location (i.e. based on Windows path)
        """
        the_path = str(file_path) + "/" if use_local_location else base_url
        the_path += self.FILE_NAME
        self.data = pd.read_csv(the_path, compression="bz2", index_col=0)

    def search(self, **kwargs: str) -> pd.DataFrame:
        """
        Description
        ----
        Search in the provided dictionary for a specific query.

        Input
        ----
        kwargs: str
            Should contain the column name and query you wish to do.
            This can for example be symbol="TSLA" or sector="Technology".
        case_sensitive (boolean):
            A variable that determines whether the query needs to be case
            sensitive or not. Default is False.

        Output
        ----
        new_df pd.DataFrame
            Returns a dataframe with a selection based on the input.
        """

        data_filter = self.data.copy()

        if "case_sensitive" in kwargs:
            case_sensitive = kwargs["case_sensitive"]
            kwargs = {k: v for k, v in kwargs.items() if k != "case_sensitive"}
        else:
            case_sensitive = False

        for key, value in kwargs.items():
            if key == "exclude_exchanges":
                if value is True:
                    # Filter data if exclude exchanges is set to True
                    data_filter = data_filter[
                        ~data_filter.index.str.contains(r"\.", na=False)
                    ]
            elif key == "index":
                # Look into the index of the DataFrame and search accordingly
                if isinstance(value, (list, pd.Index)):
                    data_filter = data_filter[
                        data_filter.index.isin(value)
                    ]
                else:
                    data_filter = data_filter[
                        data_filter.index.str.contains(value, na=False)
                    ]
            elif key not in data_filter.columns:
                print(f"{key} is not a valid column.")
            else:
                if isinstance(value, list):
                    data_filter = data_filter[
                        data_filter[key].isin(value)
                    ]
                else:
                    data_filter = data_filter[
                        data_filter[key].str.contains(value, case=case_sensitive, na=False)
                    ]

        return data_filter

    def options(self) -> pd.Series:
        """
        Description
        ----
        Returns all options for the specific asset class.

        Output
        ----
        options (pd.Series)
            Returns a series with all options for the specific asset class.
        """
        return self.data.columns


def obtain_options(
    selection: str, base_url: str = DATA_REPO, use_local_location: bool = False
) -> dict:
    """
    Description
    ----
    Obtain a dictionary with all options for the specific asset class. This is
    helpful when needing to understand the available categories without
    initialising the class itself.

    Input
    ----
    selection (string)
        The name of the class you wish to obtain the options for. Choose from:
            "equities"
            "etfs"
            "funds"
            "indices"
            "currencies"
            "cryptos"
            "moneymarkets"
    base_url (string, default is GitHub location)
        The possibility to enter your own location if desired.
    use_local_location (string, default False)
        The possibility to select a local location (i.e. based on Windows path)

    Output
    ----
    categories (dict)
        Returns a dictionary with all options for the specific asset class.
    """
    selection_values = [
        "equities",
        "etfs",
        "funds",
        "indices",
        "currencies",
        "cryptos",
        "moneymarkets",
    ]
    if selection not in selection_values:
        raise ValueError(
            f"The selection variable provided is not valid, "
            f"choose from {', '.join(selection_values)}"
        )

    the_path = str(file_path) + "/" if use_local_location else base_url
    the_path += f"/categories/{selection}_categories.gzip"
    categories_df = pd.read_csv(the_path, index_col=0, compression="gzip")
    categories = {
        index: categories_df.loc[index].dropna().to_numpy()
        for index in categories_df.index
    }

    return categories
