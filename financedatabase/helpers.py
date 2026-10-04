"""Helper Module for the Finance Database package."""

from __future__ import annotations

import re
from io import BytesIO
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import polars as pl
import requests

from .data_loader import from_pandas, load_lazy, string_dtype, to_pandas

file_path = Path(__file__).parent.parent / "compression"
DATA_REPO = (
    "https://raw.githubusercontent.com/JerBouma/FinanceDatabase/main/compression/"
)

# pylint: disable=isinstance-second-argument-not-valid-type

ROW_POSITION = "__financedatabase_row__"

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
    Data is cached locally and queried lazily with Polars (see ``data_loader``); results
    are returned as pandas (``as_pandas=True``, the default) or Polars DataFrames.
    """

    FILE_NAME = ""
    # Selectable columns in select() parameter order: column -> (label, plural) for the
    # "The <label> '<value>' is not available ... the available <plural>" error message.
    FIELDS: dict[str, tuple[str, str]] = {}
    # Whether filter values are validated against listed entries only. None follows the
    # exclude_delisted argument; True always validates against listed entries.
    VALIDATION_EXCLUDES_DELISTED: bool | None = None
    # Name used in the notice printed when only_primary_listing finds no primary listings.
    PLURAL_NAME = ""

    def __init__(
        self,
        base_url: str = DATA_REPO,
        use_local_location: bool = False,
    ):
        """
        Initialize the FinanceDatabase object.

        Loads the database for the asset class from the local cache, downloading it first
        when it isn't cached yet (or when the published file changed; checked at most once
        a day). Queries only read what they need.

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
            self._lazy = load_lazy(
                self.FILE_NAME, base_url, file_path if use_local_location else None
            )
        except requests.exceptions.RequestException as error:
            raise ValueError(
                f"Failed to load data from {the_path}: {str(error)}.\n"
                "Ensure you are able to access the file. "
                "It is possible it fails due to a firewall or other security settings. "
                "Sometimes Google Colab is also the culprit."
            ) from error
        self._data: pd.DataFrame | None = None
        self._options_cache: dict[tuple[str, bool], set[str]] = {}
        self._empty_columns: set[str] | None = None

    # ------------------------------------------------------------------ data access

    @property
    def data(self) -> pd.DataFrame:
        """The full dataset as a pandas DataFrame (built on first access, then kept)."""
        if self._data is None:
            self._data = self._to_pandas(self._lazy.collect())
        return self._data

    @data.setter
    def data(self, frame: pd.DataFrame) -> None:
        # Queries run on a text copy; results are taken from the given frame by row position,
        # so they keep its exact index and dtypes.
        self._data = frame
        self._lazy = (
            from_pandas(frame)
            .with_columns(pl.int_range(pl.len(), dtype=pl.Int64).alias(ROW_POSITION))
            .lazy()
        )
        self._options_cache = {}
        self._empty_columns = None

    def _to_pandas(self, frame: pl.DataFrame) -> pd.DataFrame:
        result = to_pandas(frame)
        # pandas' CSV reader types a column that is empty in the whole file as float64.
        if self._empty_columns is None:
            counts = self._lazy.select(pl.all().is_not_null().sum()).collect().row(0)
            self._empty_columns = {
                name
                for name, count in zip(self._lazy.collect_schema(), counts)
                if not count
            }
        for name in self._empty_columns:
            if name in result.columns:
                result[name] = result[name].astype("float64")
        return result

    def _output(
        self, frame: pl.DataFrame, as_pandas: bool
    ) -> FinanceFrame | pl.DataFrame:
        if ROW_POSITION in frame.columns:  # data was replaced with a pandas frame
            if as_pandas:
                positions = frame.get_column(ROW_POSITION).to_list()
                return FinanceFrame(self._data.iloc[positions])
            return frame.drop(ROW_POSITION)
        return FinanceFrame(self._to_pandas(frame)) if as_pandas else frame

    def _without_delisted(self, exclude_delisted: bool) -> pl.LazyFrame:
        lazy = self._lazy
        if exclude_delisted and "delisted" in lazy.collect_schema():
            lazy = lazy.filter(pl.col("delisted") != "True")
        return lazy

    # ------------------------------------------------------------------ select / options

    def _options_lower(self, field: str, exclude_delisted: bool) -> set[str]:
        key = (field, exclude_delisted)
        if key not in self._options_cache:
            values = (
                self._without_delisted(exclude_delisted)
                .select(pl.col(field).drop_nulls().str.to_lowercase().unique())
                .collect()
                .get_column(field)
            )
            self._options_cache[key] = set(values.to_list())
        return self._options_cache[key]

    def _filtered(
        self,
        filters: dict[str, Any],
        only_primary_listing: bool = False,
        exclude_delisted: bool = False,
    ) -> pl.LazyFrame:
        """Validate the filters (as before: against all values) and apply them lazily."""
        lazy = self._without_delisted(exclude_delisted)
        for field, (label, plural) in self.FIELDS.items():
            value = filters.get(field)
            if not value:
                continue
            values = [value] if isinstance(value, str) else value
            values_lower = [item.lower() for item in values]
            validate_listed = self.VALIDATION_EXCLUDES_DELISTED
            options = self._options_lower(
                field, exclude_delisted if validate_listed is None else validate_listed
            )
            for item_lower, item in zip(values_lower, values):
                if item_lower not in options:
                    raise ValueError(
                        f"The {label} '{item}' is not available in the database. "
                        f"Please check the available {plural} using the 'show_options' method."
                    )
            lazy = lazy.filter(pl.col(field).str.to_lowercase().is_in(values_lower))
        if only_primary_listing:
            symbol = self._lazy.collect_schema().names()[0]
            primary = lazy.filter(~pl.col(symbol).str.contains(".", literal=True))
            # If there are no primary listings, all listings are returned (as before).
            if primary.select(pl.len()).collect().item():
                lazy = primary
            else:
                print(
                    f"No primary listings found. Returning all {self.PLURAL_NAME} "
                    "matching your criteria."
                )
        return lazy

    def _select(
        self,
        filters: dict[str, Any],
        only_primary_listing: bool = False,
        exclude_delisted: bool = False,
        as_pandas: bool = True,
    ) -> FinanceFrame | pl.DataFrame:
        lazy = self._filtered(filters, only_primary_listing, exclude_delisted)
        return self._output(lazy.collect(), as_pandas)

    def _show_options(
        self,
        selection: str | None,
        selection_values: list[str],
        invalid_selection_message: str,
        filters: dict[str, Any],
        exclude_delisted: bool = False,
        as_pandas: bool = True,
    ) -> dict | np.ndarray | pl.Series:
        if selection is not None and selection not in selection_values:
            raise ValueError(invalid_selection_message)
        lazy = self._filtered(filters, False, exclude_delisted)
        columns = selection_values if selection is None else [selection]
        frame = lazy.select(columns).collect()

        def options(column: str) -> np.ndarray | pl.Series:
            values = frame.get_column(column).drop_nulls().unique()
            if not as_pandas:
                return values.sort()
            # Sorted and deduplicated by pandas, exactly as the pandas implementation did.
            return (
                pd.Series(values.to_list(), dtype=string_dtype()).sort_values().unique()
            )

        if selection is None:
            return {column: options(column) for column in selection_values}
        return options(selection)

    # ------------------------------------------------------------------ search

    def search(self, **kwargs: Any) -> pd.DataFrame | pl.DataFrame:
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
            exclude_delisted (bool): Whether to exclude delisted entries (equities and
                ETFs). Defaults to True; pass False to include them.
            as_pandas (bool): Return a pandas DataFrame (True, the default) or a
                Polars DataFrame (False).

        Returns:
            DataFrame with filtered data based on the input criteria.
        """
        as_pandas = kwargs.pop("as_pandas", True) in [True, "True"]
        case_sensitive = kwargs.pop("case_sensitive", False) in [True, "True"]
        exclude_delisted = kwargs.pop("exclude_delisted", True) in [True, "True"]
        lazy = self._without_delisted(exclude_delisted)
        columns = [c for c in lazy.collect_schema().names() if c != ROW_POSITION]
        symbol = columns[0]

        for key, value in kwargs.items():
            if key == "only_primary_listing":
                if value is True:
                    lazy = lazy.filter(~pl.col(symbol).str.contains(".", literal=True))
            elif key == "index":
                if isinstance(value, list | pd.Index | pl.Series):
                    lazy = lazy.filter(pl.col(symbol).is_in(list(value)))
                else:
                    lazy = lazy.filter(_matches(pl.col(symbol), value, True))
            elif key not in columns[1:]:
                print(f"{key} is not a valid column.")
            elif isinstance(value, list):
                if case_sensitive:
                    lazy = lazy.filter(pl.col(key).is_in(value))
                else:
                    lowered = pl.col(key).str.to_lowercase()
                    hits = [
                        lowered.str.contains(v.lower(), literal=True) for v in value
                    ]
                    lazy = lazy.filter(pl.any_horizontal(hits).fill_null(False))
            else:
                lazy = lazy.filter(_matches(pl.col(key), value, case_sensitive))

        return self._output(lazy.collect(), as_pandas)

    def show_options(self) -> pd.Index | dict | np.ndarray:
        """
        Get all available column options for the specific asset class.

        Returns:
            Index containing all available column names for the asset class.
            Subclasses may override this method to return a richer payload
            (e.g. a dict keyed by column name, or a 1-D ndarray of unique
            values for a single column).
        """
        return self.data.columns


def _matches(column: pl.Expr, pattern: str, case_sensitive: bool) -> pl.Expr:
    """``str.contains`` with Python regex semantics, as pandas used before.

    Polars' regex engine is used when it understands the pattern the same way; patterns it
    doesn't support (e.g. look-around or backreferences) fall back to Python's ``re``.
    """
    try:
        re.compile(pattern)
    except re.error as error:
        raise re.error(f"Invalid search pattern {pattern!r}: {error}") from error
    flagged = pattern if case_sensitive else f"(?i){pattern}"
    try:
        pl.select(pl.lit("").str.contains(flagged))
        return column.str.contains(flagged).fill_null(False)
    except pl.exceptions.ComputeError:
        compiled = re.compile(pattern, 0 if case_sensitive else re.IGNORECASE)
        return column.map_elements(
            lambda value: value is not None and bool(compiled.search(value)),
            return_dtype=pl.Boolean,
            skip_nulls=False,
        ).fill_null(False)


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
        enforce_source: str | None = None,
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
            # Lazy import: financetoolkit is an optional dependency.
            from financetoolkit import (  # noqa: PLC0415 # pylint: disable=import-outside-toplevel
                Toolkit,
            )
        except ImportError as exc:
            raise ImportError(
                "To use the 'to_toolkit' functionality, it requires installation of the FinanceToolkit "
                "Please use: \033[1m pip install financetoolkit -U \033[0m"
            ) from exc
        if api_key is None:
            print(
                "The parameter api_key is not set. Therefore, using Yahoo Finance as the source which "
                "is limited to 5 years of fundamental data. Consider obtaining a key with the following "
                "link: https://www.jeroenbouma.com/fmp"
                "\nYou can get 15% off by using the above affiliate link to "
                "get access to 30+ years of (quarterly) data which also supports the project."
            )

        symbols = self[self.index.notna()].index.to_list()

        toolkit = Toolkit(
            tickers=symbols,
            api_key=api_key or "",
            start_date=start_date,
            end_date=end_date,
            quarterly=quarterly,
            use_cached_data=use_cached_data,
            risk_free_rate=risk_free_rate,
            benchmark_ticker=benchmark_ticker,
            enforce_source=enforce_source,
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
            categories_df = pd.read_csv(
                the_path, compression="gzip", index_col=0, low_memory=False
            )
        else:
            response = requests.get(the_path, headers=HEADERS, timeout=60)
            response.raise_for_status()

            categories_df = pd.read_csv(
                BytesIO(response.content),
                compression="gzip",
                index_col=0,
                low_memory=False,
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
