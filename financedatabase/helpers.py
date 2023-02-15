"Helper Module"

from pathlib import Path

import pandas as pd

file_path = Path(__file__).parent.parent / "Database"
DATA_REPO = (
    "https://raw.githubusercontent.com/colin99d/FinanceDatabase/new_equities/Database/"
)


class FinanceDatabase:
    """
    Helpers Class
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
        Creates a dataframe with all equities from the database.

        Input
        ----
        base_url (string, default is GitHub location)
            The possibility to enter your own location if desired.
        use_local_location (string, default False)
            The possibility to select a local location (i.e. based on Windows path)
        """
        the_path = str(file_path) + "/" if use_local_location else base_url
        the_path += self.FILE_NAME
        self.data = pd.read_csv(the_path, on_bad_lines="skip", sep=";")

    def search(self, **kwargs: str) -> pd.DataFrame:
        """
        Description
        ----
        Search in the provided dictionary for a specific query. By default
        it searches in the 'summary' key which can be found in equities, etfs and funds.

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
            if key not in data_filter.columns:
                print(f"{key} is not a valid column.")
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
