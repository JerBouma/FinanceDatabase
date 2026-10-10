"""Database Module"""

__docformat__ = "google"

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import polars as pl
import requests

from financedatabase import categories_model, listings_model, query_model
from financedatabase.cache_model import load_lazy_frame
from financedatabase.frame_model import FinanceFrame
from financedatabase.helpers import convert_to_list
from financedatabase.utilities import logger_model
from financedatabase.utilities.dataframe_model import (
    convert_from_pandas,
    convert_to_pandas,
)

logger_model.setup_logger()
logger = logger_model.get_logger()

COMPRESSION_PATH = Path(__file__).parent.parent / "compression"
DATA_REPO = (
    "https://raw.githubusercontent.com/JerBouma/FinanceDatabase/main/compression/"
)
ROW_POSITION = "__financedatabase_row__"
EQUITIES_FILE_NAME = "equities.bz2"
ASSET_CLASSES = [
    "equities",
    "etfs",
    "funds",
    "indices",
    "currencies",
    "cryptos",
    "moneymarkets",
]
LOAD_ERROR_HINT = (
    "Ensure you are able to access the file. "
    "It is possible it fails due to a firewall or other security settings. "
    "Sometimes Google Colab is also the culprit."
)


class FinanceDatabase:
    """
    The FinanceDatabase provides free categorization of all types of financial products.
    It features over 300,000 symbols containing Equities, ETFs, Funds, Indices,
    Currencies, Cryptocurrencies, and Money Markets, offering a comprehensive overview
    of sectors, industries, investment types, and more.

    This class is the base controller of the asset classes. The data is cached locally
    and queried lazily with Polars; results are returned as pandas (as_pandas=True,
    the default) or Polars DataFrames.
    """

    FILE_NAME = ""
    # Whether instruments are listed on several exchanges, with one primary listing.
    HAS_LISTINGS = False
    # Selectable columns in select() order: column -> (label, plural) for error messages.
    FIELDS: dict[str, tuple[str, str]] = {}
    PLURAL_NAME = ""

    def __init__(
        self,
        base_url: str = DATA_REPO,
        use_local_location: bool = False,
    ) -> None:
        """
        Initialize the FinanceDatabase object.

        Loads the asset class from the local cache, downloading it first when it isn't
        cached yet or when the published file changed (checked at most once a day).

        Args:
            base_url (str, optional): The URL of the compressed files.
                Defaults to the GitHub repository location.
            use_local_location (bool, optional): Whether to use the compressed files of a
                local copy of the repository. Defaults to False.

        Raises:
            ValueError: If the data can't be loaded from the specified location.

        As an example:

        ```python
        import financedatabase as fd

        equities = fd.Equities()
        ```
        """
        location = str(COMPRESSION_PATH) + "/" if use_local_location else base_url
        self._source = (base_url, COMPRESSION_PATH if use_local_location else None)
        try:
            self._lazy = load_lazy_frame(
                self.FILE_NAME,
                base_url,
                COMPRESSION_PATH if use_local_location else None,
            )
        except requests.exceptions.RequestException as error:
            raise ValueError(
                f"Failed to load data from {location}{self.FILE_NAME}: {str(error)}.\n"
                f"{LOAD_ERROR_HINT}"
            ) from error
        self._data: pd.DataFrame | None = None
        self._options: dict[tuple[str, bool], set[str]] = {}
        self._listing_ranks: pl.DataFrame | None = None

    @property
    def data(self) -> pd.DataFrame:
        """
        Get the full dataset as a pandas DataFrame, built on first access.

        Returns:
            pd.DataFrame: Every row of the asset class, indexed by symbol.
        """
        if self._data is None:
            self._data = self._convert_to_pandas(self._lazy.collect())
        return self._data

    @data.setter
    def data(self, frame: pd.DataFrame) -> None:
        """
        Set the dataset, for example to a filtered or modified copy.

        Queries run on a text copy and take their results from the given frame by
        row position, so they keep its exact index and dtypes.

        Args:
            frame (pd.DataFrame): The dataset to query from now on.
        """
        self._data = frame
        self._lazy = (
            convert_from_pandas(frame)
            .with_columns(pl.int_range(pl.len(), dtype=pl.Int64).alias(ROW_POSITION))
            .lazy()
        )
        self._options = {}
        self._listing_ranks = None

    def get_columns(self) -> list[str]:
        """
        Get the columns of the dataset, the symbol column first.

        Returns:
            list[str]: The column names.
        """
        names = self._lazy.collect_schema().names()
        return [name for name in names if name != ROW_POSITION]

    def get_lazy_frame(self, exclude_delisted: bool = False) -> pl.LazyFrame:
        """
        Get the dataset as a lazy Polars frame with every column as text.

        Args:
            exclude_delisted (bool, optional): Whether to exclude delisted entries.
                Defaults to False.

        Returns:
            pl.LazyFrame: The lazy dataset.
        """
        return query_model.exclude_delisted_rows(self._lazy, exclude_delisted)

    def get_listing_ranks(self) -> pl.DataFrame | None:
        """
        Get the rank of every listing and whether it is the primary listing of its
        instrument, computed once (see listings_model).

        Returns:
            pl.DataFrame | None: The symbol column, "listing_rank" and
                "primary_listing", or None for an asset class without listings.
        """
        if not self.HAS_LISTINGS or "exchange" not in self.get_columns():
            return None
        if self._listing_ranks is None:
            self._listing_ranks = listings_model.get_listing_ranks(
                self._lazy, self.get_main_venues()
            )
        return self._listing_ranks

    def get_main_venues(self) -> list[str]:
        """
        Get the exchanges that are main venues (see listings_model), measured on this
        asset class and, for one without countries, also on the equities.

        Returns:
            list[str]: The exchanges.
        """
        venues = listings_model.get_main_venues(self._lazy)
        if "country" not in self.get_columns():
            equities = load_lazy_frame(EQUITIES_FILE_NAME, *self._source)
            venues = sorted(
                {
                    *venues,
                    *listings_model.get_main_venues(
                        equities.select("exchange", "country")
                    ),
                }
            )
        return venues

    def get_primary_symbols(self) -> pl.Series | None:
        """
        Get the symbols of the primary listings: per instrument the listing on the
        main exchange of its home market, or the best listing abroad without one.

        Returns:
            pl.Series | None: The symbols, or None for an asset class without
                listings, whose primary listings are the symbols without a suffix.
        """
        ranks = self.get_listing_ranks()
        if ranks is None:
            return None
        return ranks.filter("primary_listing").get_column(ranks.columns[0])

    def get_lowercase_options(self, field: str, exclude_delisted: bool) -> set[str]:
        """
        Get the lowercase values of a column that filters are validated against.

        Args:
            field (str): The column name.
            exclude_delisted (bool): Whether to leave out values of delisted entries.

        Returns:
            set[str]: The unique lowercase values of the column.
        """
        key = (field, exclude_delisted)
        if key not in self._options:
            self._options[key] = query_model.get_lowercase_options(
                self.get_lazy_frame(exclude_delisted), field
            )
        return self._options[key]

    def filter_lazy_frame(
        self,
        filters: dict[str, Any],
        only_primary_listing: bool = False,
        exclude_delisted: bool = False,
    ) -> pl.LazyFrame:
        """
        Filter the dataset lazily after validating the filter values.

        If only_primary_listing finds no primary listings, all matching listings are
        kept and a notice is logged.

        Args:
            filters (dict[str, Any]): Column names mapped to a value or list of values.
            only_primary_listing (bool, optional): Whether to only keep primary listings.
                Defaults to False.
            exclude_delisted (bool, optional): Whether to exclude delisted entries.
                Defaults to False.

        Returns:
            pl.LazyFrame: The filtered lazy dataset.

        Raises:
            ValueError: If a filter value is not available in the database.
        """
        lazy = self.get_lazy_frame(exclude_delisted)
        for field, (label, plural) in self.FIELDS.items():
            if not filters.get(field):
                continue
            values = convert_to_list(filters[field])
            query_model.validate_filter_values(
                values,
                self.get_lowercase_options(field, exclude_delisted),
                label,
                plural,
            )
            lazy = query_model.filter_rows(lazy, field, values)

        if only_primary_listing:
            primary = query_model.filter_primary_listings(
                lazy, self.get_columns()[0], self.get_primary_symbols()
            )
            if query_model.count_rows(primary):
                lazy = primary
            else:
                logger.info(
                    "No primary listings found. Returning all %s matching your criteria.",
                    self.PLURAL_NAME,
                )
        return lazy

    def _convert_to_pandas(self, frame: pl.DataFrame) -> pd.DataFrame:
        """
        Convert collected rows to the pandas frame the package returns.

        The dataset already holds the final types (a column that is empty in the whole
        dataset is Float64, as pandas' CSV reader types it).

        Args:
            frame (pl.DataFrame): The collected rows.

        Returns:
            pd.DataFrame: The rows indexed by symbol.
        """
        return convert_to_pandas(frame)

    def _convert_output(
        self, frame: pl.DataFrame, as_pandas: bool
    ) -> FinanceFrame | pl.DataFrame:
        """
        Convert collected rows to the requested output format.

        Args:
            frame (pl.DataFrame): The collected rows.
            as_pandas (bool): Whether to return a FinanceFrame or a Polars DataFrame.

        Returns:
            FinanceFrame | pl.DataFrame: The rows in the requested format.
        """
        if ROW_POSITION in frame.columns:
            if as_pandas:
                positions = frame.get_column(ROW_POSITION).to_list()
                return FinanceFrame(self._data.iloc[positions])
            return frame.drop(ROW_POSITION)
        return FinanceFrame(self._convert_to_pandas(frame)) if as_pandas else frame

    def _select_rows(
        self,
        filters: dict[str, Any],
        only_primary_listing: bool = False,
        exclude_delisted: bool = False,
        as_pandas: bool = True,
    ) -> FinanceFrame | pl.DataFrame:
        """
        Select the rows matching the filters, shared by every select().

        Args:
            filters (dict[str, Any]): Column names mapped to a value or list of values.
            only_primary_listing (bool, optional): Whether to only keep primary listings.
                Defaults to False.
            exclude_delisted (bool, optional): Whether to exclude delisted entries.
                Defaults to False.
            as_pandas (bool, optional): Whether to return a pandas DataFrame.
                Defaults to True.

        Returns:
            FinanceFrame | pl.DataFrame: The matching rows.
        """
        lazy = self.filter_lazy_frame(filters, only_primary_listing, exclude_delisted)
        return self._convert_output(lazy.collect(), as_pandas)

    def _collect_options(
        self,
        selection: str | None,
        selection_values: list[str],
        invalid_selection_message: str,
        filters: dict[str, Any],
        exclude_delisted: bool = False,
        as_pandas: bool = True,
    ) -> dict | np.ndarray | pl.Series:
        """
        Collect the sorted unique values of columns, shared by every show_options().

        Args:
            selection (str | None): The column to show options for, or None for all.
            selection_values (list[str]): The columns that can be selected.
            invalid_selection_message (str): The error message for an invalid selection.
            filters (dict[str, Any]): Column names mapped to a value or list of values.
            exclude_delisted (bool, optional): Whether to leave out delisted entries.
                Defaults to False.
            as_pandas (bool, optional): Whether to return numpy arrays instead of Polars
                Series. Defaults to True.

        Returns:
            dict | np.ndarray | pl.Series: The options of one column, or a dictionary with
                the options of every column.

        Raises:
            ValueError: If the selection is not one of the selection values.
        """
        if selection is not None and selection not in selection_values:
            raise ValueError(invalid_selection_message)
        columns = selection_values if selection is None else [selection]
        unique = query_model.get_unique_values(
            self.filter_lazy_frame(filters, False, exclude_delisted), columns
        )
        if selection is None:
            return {
                column: query_model.get_sorted_options(unique[column], as_pandas)
                for column in selection_values
            }
        return query_model.get_sorted_options(unique[selection], as_pandas)

    def search(self, **kwargs: Any) -> pd.DataFrame | pl.DataFrame:
        """
        Search the database based on column names and queries.

        A query is a regular expression matched anywhere in the value; a list of queries
        keeps rows that contain any of them.

        Args:
            **kwargs: Column names and search queries.
                For example, symbol="TSLA" or sector="Technology".
            case_sensitive (bool, optional): Whether the search should be case-sensitive.
                Defaults to False.
            only_primary_listing (bool, optional): Whether to exclude secondary listings.
                Defaults to False.
            index (str, optional): Search within the DataFrame index. Defaults to None.
            exclude_delisted (bool, optional): Whether to exclude delisted entries (equities
                and ETFs). Defaults to True.
            as_pandas (bool, optional): Whether to return a pandas DataFrame (True) or a
                Polars DataFrame (False). Defaults to True.

        Returns:
            pd.DataFrame | pl.DataFrame: The rows matching every query.

        As an example:

        ```python
        import financedatabase as fd

        equities = fd.Equities()

        equities.search(
            summary="semiconductor", country="Netherlands", only_primary_listing=True
        )[["name", "currency", "industry", "exchange", "market_cap"]].head()
        ```

        Which returns:

        | symbol | name                             | currency | industry                                 | exchange | market_cap |
        |:-------|:---------------------------------|:---------|:-----------------------------------------|:---------|:-----------|
        | ASMIY  | ASM International N.V.           | USD      | Semiconductors & Semiconductor Equipment | PNK      | Large Cap  |
        | ASML   | ASML Holding N.V.                | USD      | Semiconductors & Semiconductor Equipment | NMS      | Mega Cap   |
        | ASMLF  | ASML Holding N.V.                | USD      | Semiconductors & Semiconductor Equipment | PNK      | Mega Cap   |
        | ASMXF  | ASM International N.V.           | USD      | Semiconductors & Semiconductor Equipment | PNK      | Large Cap  |
        | BESIY  | BE Semiconductor Industries N.V. | USD      | Semiconductors & Semiconductor Equipment | PNK      | Mid Cap    |
        """  # noqa: E501
        as_pandas = kwargs.pop("as_pandas", True) in [True, "True"]
        case_sensitive = kwargs.pop("case_sensitive", False) in [True, "True"]
        exclude_delisted = kwargs.pop("exclude_delisted", True) in [True, "True"]
        lazy = query_model.search_rows(
            self.get_lazy_frame(exclude_delisted),
            kwargs,
            self.get_columns(),
            case_sensitive,
            (
                self.get_primary_symbols()
                if kwargs.get("only_primary_listing") is True
                else None
            ),
        )
        return self._convert_output(lazy.collect(), as_pandas)

    def show_options(self) -> pd.Index | dict | np.ndarray:
        """
        Show the columns of the asset class.

        The asset classes override this method to show the values of their filters.

        Returns:
            pd.Index | dict | np.ndarray: The column names of the asset class.
        """
        return self.data.columns


def show_options(
    selection: str | None = None,
    base_url: str = DATA_REPO,
    use_local_location: bool = False,
    as_pandas: bool = True,
) -> dict:
    """
    Show the category options of an asset class without initializing it.

    Args:
        selection (str | None, optional): Asset class to show the options of. Choose from:
            'equities', 'etfs', 'funds', 'indices', 'currencies', 'cryptos' or
            'moneymarkets'. Defaults to None.
        base_url (str, optional): The URL of the compressed files.
            Defaults to the GitHub repository.
        use_local_location (bool, optional): Whether to use the compressed files of a local
            copy of the repository. Defaults to False.
        as_pandas (bool, optional): Whether to return the values as numpy arrays (True) or
            as Polars Series (False). Defaults to True.

    Returns:
        dict: Category names mapped to their possible values.

    Raises:
        ValueError: If the selection is None or invalid, or the data can't be loaded.

    As an example:

    ```python
    import financedatabase as fd

    fd.show_options("equities")["sector"]
    ```

    Which returns:

    ```
    ['Communication Services', 'Consumer Discretionary', 'Consumer Staples', 'Energy',
     'Financials', 'Health Care', 'Industrials', 'Information Technology', 'Materials',
     'Real Estate', 'Utilities']
    ```
    """
    if selection is None:
        raise ValueError(
            "The 'selection' variable is not set. Please provide a valid selection.\n"
            f"The available options are: {', '.join(ASSET_CLASSES)}"
        )
    if selection not in ASSET_CLASSES:
        raise ValueError(
            f"The selection variable provided is not valid, "
            f"choose from {', '.join(ASSET_CLASSES)}"
        )

    location = str(COMPRESSION_PATH) + "/" if use_local_location else base_url
    location += f"/categories/{selection}_categories"

    try:
        categories = categories_model.get_categories(location, use_local_location)
    except requests.exceptions.RequestException as error:
        raise ValueError(
            f"Failed to load data from {location}: {str(error)}.\n{LOAD_ERROR_HINT}"
        ) from error

    if not as_pandas:
        return {
            name: pl.Series(name, values, dtype=pl.String)
            for name, values in categories.items()
        }
    return {name: np.array(values, dtype=object) for name, values in categories.items()}
