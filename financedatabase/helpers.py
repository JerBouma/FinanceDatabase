"""Helper Module for the Finance Database package."""

from pathlib import Path

import pandas as pd
import requests

file_path = Path(__file__).parent.parent / "compression"
DATA_REPO = (
    "https://raw.githubusercontent.com/JerBouma/FinanceDatabase/main/compression/"
)

# pylint: disable=isinstance-second-argument-not-valid-type

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/58.0.3029.110 Safari/537.3"
}


class FinanceDatabase:
    """
    Financial product categorization database.

    The FinanceDatabase provides free categorization of all types of financial products.
    It features over 300,000 symbols containing Equities, ETFs, Funds, Indices,
    Currencies, Cryptocurrencies, and Money Markets, offering a comprehensive overview
    of sectors, industries, investment types, and more.

    This class serves as the base controller for all asset-class specific subclasses.
    """

    FILE_NAME = ""

    def __init__(
        self,
        base_url: str = DATA_REPO,
        use_local_location: bool = False,
    ):
        """
        Initialize the FinanceDatabase object.

        Reads the database from a CSV file corresponding to the asset class,
        which can be located either remotely or locally.

        Args:
            base_url: The URL or local path to the CSV file.
                Defaults to the GitHub repository location.
            use_local_location: Whether to use a local file path instead of URL.
                Defaults to False.

        Raises:
            Exception: If unable to load data from the specified location.
        """
        the_path = str(file_path) + "/" if use_local_location else base_url
        the_path += self.FILE_NAME
        try:
            if use_local_location:
                self.data = pd.read_csv(the_path, compression="bz2", index_col=0)
            else:
                response = requests.get(the_path, headers=HEADERS, timeout=60)
                response.raise_for_status()

                self.data = pd.read_csv(
                    pd.io.common.BytesIO(response.content),
                    compression="bz2",
                    index_col=0,
                )
        except requests.exceptions.RequestException as error:
            raise ValueError(
                f"Failed to load data from {the_path}: {str(error)}.\n"
                "Ensure you are able to access the file. "
                "It is possible it fails due to a firewall or other security settings. "
                "Sometimes Google Colab is also the culprit."
            ) from error

    def search(self, **kwargs: str) -> pd.DataFrame:
        """
        Search for specific data based on provided criteria.

        Allows searching the database based on column names and queries,
        with optional case sensitivity.

        Args:
            **kwargs: Column names and search queries.
                For example, symbol="TSLA" or sector="Technology".
            case_sensitive (bool): Whether the search should be case-sensitive.
                Defaults to False.
            only_primary_listing (bool): Whether to exclude secondary listings.
                Defaults to False.
            index (str): Search within the DataFrame index.
                Defaults to None.

        Returns:
            DataFrame with filtered data based on the input criteria.
        """
        data_filter = self.data.copy()

        if "case_sensitive" in kwargs:
            case_sensitive = bool(kwargs["case_sensitive"] in [True, "True"])
            kwargs = {k: v for k, v in kwargs.items() if k != "case_sensitive"}
        else:
            case_sensitive = False

        for key, value in kwargs.items():
            if key == "only_primary_listing":
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
                if case_sensitive:
                    # For case-sensitive search, use string comparison that preserves case
                    data_filter = data_filter[data_filter[key].isin(value)]
                else:
                    # For case-insensitive search, convert both sides to lowercase
                    # Create a mask that matches if any value in the list is found in the column
                    mask = (
                        data_filter[key]
                        .str.lower()
                        .apply(
                            lambda x, vals=value: (
                                any(val.lower() in str(x).lower() for val in vals)
                                if pd.notna(x)
                                else False
                            )
                        )
                    )
                    data_filter = data_filter[mask]
            else:
                data_filter = data_filter[
                    data_filter[key].str.contains(value, case=case_sensitive, na=False)
                ]

        return FinanceFrame(data_filter)

    def show_options(self) -> pd.Series:
        """
        Get all available column options for the specific asset class.

        Returns:
            Series containing all available column names for the asset class.
        """
        return self.data.columns


class FinanceFrame(pd.DataFrame):
    """
    Enhanced DataFrame with financial data integration capabilities.

    Extends the pandas DataFrame with additional functionality for
    financial analysis, particularly for connecting with the Finance
    Toolkit using tickers obtained from the Finance Database.
    """

    def to_toolkit(
        self,
        api_key: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        quarterly: bool = False,
        use_cached_data: bool | str = False,
        risk_free_rate: str = "10y",
        benchmark_ticker: str | None = "SPY",
        historical_source: str | None = None,
        convert_currency: bool | None = None,
        intraday_period: str | None = None,
        rounding: int | None = 4,
        remove_invalid_tickers: bool = False,
        sleep_timer: bool | None = None,
        progress_bar: bool = True,
    ):
        """
        Convert the FinanceFrame to a Finance Toolkit object.

        Creates a Finance Toolkit object using the tickers in this DataFrame,
        providing access to fundamental and historical data, ratios, metrics,
        models, and technical indicators.

        Args:
            api_key: API key from FinancialModelingPrep.
                Obtain one at: https://www.jeroenbouma.com/fmp
            start_date: Start date for data collection (YYYY-MM-DD).
                Defaults to 10 years before current date.
            end_date: End date for data collection (YYYY-MM-DD).
                Defaults to current date.
            quarterly: Whether to collect quarterly financial statements.
                Defaults to False (yearly statements).
            use_cached_data: Whether to use previously cached data.
                Can be a boolean or a string path. Defaults to False.
            risk_free_rate: Risk-free rate to use (13w, 5y, 10y, 30y).
                Based on US Treasury Yields. Defaults to "10y".
            benchmark_ticker: Ticker for benchmark comparisons.
                Defaults to "SPY" (S&P 500).
            historical_source: Source for historical data ("FinancialModelingPrep"
                or "YahooFinance"). Defaults to FinancialModelingPrep.
            convert_currency: Whether to convert financial statement currencies
                to match historical data. Defaults to None (auto-determined).
            intraday_period: Time period for intraday data (1min, 5min, 15min,
                30min, 1hour). Defaults to None.
            rounding: Number of decimal places for results. Defaults to 4.
            remove_invalid_tickers: Whether to remove invalid tickers.
                Defaults to False.
            sleep_timer: Whether to use a sleep timer when rate limit is reached.
                Defaults to None (auto-determined).
            progress_bar: Whether to show progress bar for 10+ tickers.
                Defaults to True.

        Returns:
            Finance Toolkit object with data for the tickers in this DataFrame.

        Raises:
            ImportError: If FinanceToolkit is not installed.
        """
        try:
            from financetoolkit import (  # pylint: disable=import-outside-toplevel
                Toolkit,
            )
        except ImportError as exc:
            raise ImportError(
                "To use the 'to_toolkit' functionality, it requires installation of the FinanceToolkit "
                "Please use: \033[1m pip install financetoolkit \033[0m"
            ) from exc
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
            use_cached_data=use_cached_data,
            risk_free_rate=risk_free_rate,
            benchmark_ticker=benchmark_ticker,
            historical_source=historical_source,
            convert_currency=convert_currency,
            intraday_period=intraday_period,
            rounding=rounding,
            remove_invalid_tickers=remove_invalid_tickers,
            sleep_timer=sleep_timer,
            progress_bar=progress_bar,
        )

        return toolkit


def show_options(
    selection: str | None = None,
    base_url: str = DATA_REPO,
    use_local_location: bool = False,
) -> dict:
    """
    Get available category options for a specific asset class.

    Provides a dictionary of all available categories for the specified
    asset class without requiring class initialization.

    Args:
        selection: Asset class to get options for. Can be one of:
            'equities', 'etfs', 'funds', 'indices', 'currencies',
            'cryptos', 'moneymarkets'.
        base_url: Custom URL or file path location.
            Defaults to the GitHub repository.
        use_local_location: Whether to use a local file path.
            Defaults to False.

    Returns:
        Dictionary mapping category names to their possible values.

    Raises:
        ValueError: If selection is None or invalid.
        Exception: If unable to load data from the specified location.
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
    if selection is None:
        raise ValueError(
            "The 'selection' variable is not set. Please provide a valid selection.\n"
            f"The available options are: {', '.join(selection_values)}"
        )
    if selection not in selection_values:
        raise ValueError(
            f"The selection variable provided is not valid, "
            f"choose from {', '.join(selection_values)}"
        )

    the_path = str(file_path) + "/" if use_local_location else base_url
    the_path += f"/categories/{selection}_categories.gzip"

    try:
        if use_local_location:
            categories_df = pd.read_csv(the_path, compression="gzip", index_col=0)
        else:
            response = requests.get(the_path, headers=HEADERS, timeout=60)
            response.raise_for_status()

            categories_df = pd.read_csv(
                pd.io.common.BytesIO(response.content), compression="gzip", index_col=0
            )
    except requests.exceptions.RequestException as error:
        raise ValueError(
            f"Failed to load data from {the_path}: {str(error)}.\n"
            "Ensure you are able to access the file. "
            "It is possible it fails due to a firewall or other security settings. "
            "Sometimes Google Colab is also the culprit."
        ) from error

    categories = {
        index: categories_df.loc[index].dropna().to_numpy()
        for index in categories_df.index
    }

    return categories
