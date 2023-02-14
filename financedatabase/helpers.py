from pathlib import Path

import pandas as pd

file_path = Path(__file__).parent.parent / "Database"
data_repo = (
    "https://raw.githubusercontent.com/JerBouma/FinanceDatabase/master/Database/"
)


class FinanceDatabase:
    FILE_NAME = ""

    def __init__(
        self,
        base_url: str = data_repo,
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
        self.df = pd.read_csv(the_path, on_bad_lines="skip", sep=";")

    def search(
        self, query: str, search: str = "summary", case_sensitive: bool = False
    ) -> pd.DataFrame:
        """
        Description
        ----
        Search in the provided dictionary for a specific query. By default
        it searches in the 'summary' key which can be found in equities, etfs and funds.

        Input
        ----
        query (string)
            The search term that is used to search in the dictionary.
        search (string):
            The column you wish to search in. The default is 'summary'.
        case_sensitive (boolean):
            A variable that determines whether the query needs to be case
            sensitive or not. Default is False.

        Output
        ----
        new_df pd.DataFrame
            Returns a dataframe with a selection based on the input.
        """
        if search not in self.df.columns:
            raise ValueError("Invalid search column selected")
        return self.df[
            self.df[search].str.contains(query, case=case_sensitive, na=False)
        ]
