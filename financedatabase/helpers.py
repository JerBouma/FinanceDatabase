"Helper Module"

from pathlib import Path

import pandas as pd
from financetoolkit import Toolkit

file_path = Path(__file__).parent.parent / "compression"
DATA_REPO = (
    "https://raw.githubusercontent.com/JerBouma/FinanceDatabase/main/compression/"
)

# pylint: disable=isinstance-second-argument-not-valid-type


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
        Initialize the FinanceFrame object.

        This constructor reads the database from the CSV file corresponding to the
        asset class, which can be located remotely or locally.

        Args:
            base_url (str, optional):
                The URL or local path to the CSV file. Defaults to the GitHub location.
            use_local_location (bool, optional):
                Set to True if using a local file path. Defaults to False.
        """
        the_path = str(file_path) + "/" if use_local_location else base_url
        the_path += self.FILE_NAME
        self.data = pd.read_csv(the_path, compression="bz2", index_col=0)

    def search(self, **kwargs: str) -> pd.DataFrame:
        """
        Search for specific data based on the provided criteria.

        This method allows you to search for data in the FinanceFrame based on
        the provided column name and query. You can also specify whether the search
        should be case-sensitive or not.

        Args:
            **kwargs (str):
                Should contain the column name and query you wish to perform.
                For example, symbol="TSLA" or sector="Technology".
            case_sensitive (bool, optional):
                Determines whether the query should be case-sensitive. Defaults to False.

        Returns:
            pd.DataFrame:
                A DataFrame with a selection of data based on the input criteria.
        """
        data_filter = self.data.copy()

        if "case_sensitive" in kwargs:
            case_sensitive = bool(kwargs["case_sensitive"] in [True, "True"])
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
                if isinstance(value, list | pd.Index):
                    data_filter = data_filter[data_filter.index.isin(value)]
                else:
                    data_filter = data_filter[
                        data_filter.index.str.contains(value, na=False)
                    ]
            elif key not in data_filter.columns:
                print(f"{key} is not a valid column.")
            elif isinstance(value, list):
                data_filter = data_filter[data_filter[key].isin(value)]
            else:
                data_filter = data_filter[
                    data_filter[key].str.contains(value, case=case_sensitive, na=False)
                ]

        return FinanceFrame(data_filter)

    def options(self) -> pd.Series:
        """
        Get all available options for the specific asset class.

        Returns:
            pd.Series:
                A series containing all available options for the specific asset class.
        """
        return self.data.columns


class FinanceFrame(pd.DataFrame):
    """
    The FinanceFrame is a helper class that adds in additional
    functionality on top of the DataFrame object where applicable. For
    the most part this is done to be able to connect to the Finance
    Toolkit with ease using the tickers as obtained from the
    Finance Database.
    """

    def to_toolkit(
        self,
        api_key: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        quarterly: bool = False,
        risk_free_rate: str = "10y",
        benchmark_ticker: str | None = "SPY",
        rounding: int | None = 4,
        remove_invalid_tickers: bool = False,
        sleep_timer: bool | None = None,
        progress_bar: bool = True,
    ) -> Toolkit:
        """
        Convert the FinanceFrame to a Finance Toolkit object.

        This method allows you to convert the FinanceFrame to a Finance Toolkit object,
        providing access to 30+ years of fundamental and historical data, 180+ ratios,
        performance and risk metrics, models, and technical indicators.

        Args:
            api_key (str): An API key from FinancialModelingPrep. Obtain one here: https://www.jeroenbouma.com/fmp
            start_date (str): A string containing the start date of the data. This needs to be formatted as YYYY-MM-DD.
                The default is today minus 10 years which can be freely changed to extend the period.
            end_date (str): A string containing the end date of the data. This needs to be formatted as YYYY-MM-DD.
                The default is today which can be freely changed to extend the period.
            quarterly (bool): A boolean indicating whether to collect quarterly data. This defaults to False and thus
            collects yearly financial statements. Note that historical data can still be collected for
            any period and interval.
            risk_free_rate (str): A string containing the risk free rate. This can be 13w, 5y, 10y or 30y. This is
            based on the US Treasury Yields and is used to calculate various ratios and Excess Returns.
            benchmark_ticker (str): A string containing the benchmark ticker. Defaults to SPY (S&P 500). This is
            meant to calculate ratios and indicators such as the CAPM and Jensen's Alpha but also serves as purpose to
            give insights in the performance of a stock compared to a benchmark.
            rounding (int): An integer indicating the number of decimals to round the results to.
            remove_invalid_tickers (bool): A boolean indicating whether to remove invalid tickers. Defaults to False.
            sleep_timer (bool): Whether to set a sleep timer when the rate limit is reached. Note that this only works
            if you have a Premium subscription (Starter or higher) from FinancialModelingPrep. Defaults to None which
            means it is determined by the model (Free plan = False, Premium plan = True).
            progress_bar (bool): Whether to enable the progress bar when ticker amount is over 10. Defaults to True.

        Returns:
            Toolkit:
                A Finance Toolkit object.
        """
        if api_key is None:
            print(
                "The parameter api_key is not set. Therefore, only historical data and "
                "indicators are available. Consider obtaining a key with the following "
                "link: https://www.jeroenbouma.com/fmp"
                "\nThe free plan allows for 250 requests per day, a limit of 5 years and has no "
                "quarterly data. You can get 15% off by using the above affiliate link to "
                "get access to 30+ years of (quarterly) data which also supports the project."
            )
        symbols = self[self.index.notna()].index.to_list()

        toolkit = Toolkit(
            tickers=symbols,
            api_key=api_key,
            start_date=start_date,
            end_date=end_date,
            quarterly=quarterly,
            risk_free_rate=risk_free_rate,
            benchmark_ticker=benchmark_ticker,
            rounding=rounding,
            remove_invalid_tickers=remove_invalid_tickers,
            sleep_timer=sleep_timer,
            progress_bar=progress_bar,
        )

        return toolkit


def obtain_options(
    selection: str, base_url: str = DATA_REPO, use_local_location: bool = False
) -> dict:
    """
    Obtain a dictionary with all options for the specific asset class.

    This method provides a dictionary with all available options for the specified
    asset class, which can be helpful for understanding available categories without
    initializing the class itself.

    Args:
        selection (str):
            The name of the class you wish to obtain the options for. Choose from:
                "equities"
                "etfs"
                "funds"
                "indices"
                "currencies"
                "cryptos"
                "moneymarkets"
        base_url (str, optional):
            The possibility to enter your own location if desired. Defaults to the
            GitHub location.
        use_local_location (bool, optional):
            The possibility to select a local location (i.e., based on a Windows path).
            Defaults to False.

    Returns:
        categories (dict):
            A dictionary with all options for the specific asset class.
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
