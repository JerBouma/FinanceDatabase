"""Provider Model"""

__docformat__ = "google"

import contextlib
import os
import sys
import threading
import time
from dataclasses import dataclass, field
from typing import Any

import polars as pl

import financedatabase as fd
from financedatabase.database_controller import FinanceDatabase
from financedatabase.mcp_server.coercion_model import resolve_values, suggest
from financedatabase.utilities.logger_model import get_logger

logger = get_logger()

LOCAL_ENV = "FINANCEDATABASE_MCP_LOCAL"

MARKET_CAP_ORDER = [
    "Mega Cap",
    "Large Cap",
    "Mid Cap",
    "Small Cap",
    "Micro Cap",
    "Nano Cap",
]


class QueryError(ValueError):
    """
    An invalid request, carrying the message returned to the caller.
    """


@dataclass
class AssetClassSpec:
    """
    Specification of one asset class tool, read from config.yaml.

    Attributes:
        tool_name (str): MCP tool name, e.g. "equities".
        display_name (str): Human-readable title, e.g. "Equities".
        class_name (str): Name of the financedatabase class, e.g. "Equities".
        description (str): AI-facing tool description.
        summary (str): Short description for listings.
        default_columns (list[str]): Columns returned when show_columns is not set.
        columns (list[str]): Every column of the dataset (for parameter descriptions).
        category_column (str): Column shown as "category" by search_instruments.
        supports_delisted (bool): Whether the class keeps delisted entries.
        supports_primary_listing (bool): Whether select() has only_primary_listing.
    """

    tool_name: str
    display_name: str
    class_name: str
    description: str
    summary: str = ""
    default_columns: list[str] = field(default_factory=list)
    columns: list[str] = field(default_factory=list)
    category_column: str = ""
    supports_delisted: bool = False
    supports_primary_listing: bool = False

    def get_class(self) -> type[FinanceDatabase]:
        """
        Get the financedatabase class serving this asset class.

        Returns:
            type[FinanceDatabase]: The asset class, e.g. fd.Equities.
        """
        return getattr(fd, self.class_name)

    def get_filters(self) -> list[str]:
        """
        Get the select() filters, taken from the package so they never drift apart.

        Returns:
            list[str]: The filter names.
        """
        return list(self.get_class().FIELDS)


def check_local_data() -> bool:
    """
    Check whether to read the repository's local compression files instead of GitHub.

    Returns:
        bool: Whether FINANCEDATABASE_MCP_LOCAL is set to a true value.
    """
    return os.environ.get(LOCAL_ENV, "").strip().lower() in ("1", "true", "yes", "on")


@contextlib.contextmanager
def redirect_stdout_to_stderr():
    """
    Redirect anything printed while a tool runs to stderr.

    Under the stdio transport stdout is the JSON-RPC stream, so a stray print would
    corrupt it. Tools run synchronously on the event loop thread, so swapping
    sys.stdout for the duration of a call affects nothing else.
    """
    with contextlib.redirect_stdout(sys.stderr):
        yield


class DatabaseProvider:
    """
    Serves queries for every asset class from cached Finance Database instances.

    Args:
        specs (list[AssetClassSpec]): The asset classes to serve.
        instance_ttl_seconds (int): Age after which an instance is rebuilt on its next
            use, letting the package check for a newer published database.
        identifier_columns (list[str]): Columns matched exactly by a query (ISIN, ...).
        use_local_location (bool | None): Read local compression files. None follows
            the FINANCEDATABASE_MCP_LOCAL environment variable at instance creation.
    """

    def __init__(
        self,
        specs: list[AssetClassSpec],
        instance_ttl_seconds: int = 86400,
        identifier_columns: list[str] | None = None,
        use_local_location: bool | None = None,
    ) -> None:
        """
        Initializes the DatabaseProvider. No data is loaded until the first query.

        Args:
            specs (list[AssetClassSpec]): The asset classes to serve.
            instance_ttl_seconds (int): Age in seconds after which an instance is rebuilt.
            identifier_columns (list[str] | None): Columns matched exactly by a query.
            use_local_location (bool | None): Read local compression files instead of
                GitHub; None follows FINANCEDATABASE_MCP_LOCAL.
        """
        self.specs: dict[str, AssetClassSpec] = {spec.tool_name: spec for spec in specs}
        self._instance_ttl = instance_ttl_seconds
        self._identifier_columns = list(identifier_columns or [])
        self._use_local_location = use_local_location
        self._instances: dict[str, tuple[FinanceDatabase, float]] = {}
        self._locks = {name: threading.Lock() for name in self.specs}

    def get_instance(self, tool_name: str) -> FinanceDatabase:
        """
        Get the cached instance for an asset class, creating it on first use.

        Args:
            tool_name (str): The asset class tool name, e.g. "equities".

        Returns:
            FinanceDatabase: The shared instance.

        Raises:
            ValueError: If the data cannot be loaded and no earlier instance exists.
        """
        spec = self.specs[tool_name]
        with self._locks[tool_name]:
            cached = self._instances.get(tool_name)
            if cached and time.monotonic() - cached[1] < self._instance_ttl:
                return cached[0]

            local = (
                check_local_data()
                if self._use_local_location is None
                else self._use_local_location
            )
            start = time.perf_counter()
            try:
                with redirect_stdout_to_stderr():
                    instance = spec.get_class()(use_local_location=local)
            except ValueError:
                if cached:
                    logger.warning(
                        "Refreshing %s failed; keeping the cached instance.", tool_name
                    )
                    self._instances[tool_name] = (cached[0], time.monotonic())
                    return cached[0]
                raise
            logger.debug(
                "Loaded %s (%s data) in %.2fs",
                tool_name,
                "local" if local else "remote",
                time.perf_counter() - start,
            )
            self._instances[tool_name] = (instance, time.monotonic())
            return instance

    def clear_instances(self) -> None:
        """
        Clear every cached instance; they are recreated on next use.
        """
        self._instances.clear()

    def get_options(
        self, tool_name: str, selection: str, include_delisted: bool = False
    ) -> list[str]:
        """
        Get the sorted values of one field, via the package's show_options.

        Args:
            tool_name (str): The asset class tool name.
            selection (str): The field, e.g. "sector".
            include_delisted (bool): Include values only used by delisted entries.

        Returns:
            list[str]: The values in their original case.
        """
        spec = self.specs[tool_name]
        instance = self.get_instance(tool_name)
        kwargs: dict[str, Any] = {"selection": selection, "as_pandas": False}
        if spec.supports_delisted:
            kwargs["exclude_delisted"] = not include_delisted
        with redirect_stdout_to_stderr():
            return instance.show_options(**kwargs).to_list()

    def resolve_filters(
        self,
        tool_name: str,
        filters: dict[str, Any],
        include_delisted: bool = False,
    ) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
        """
        Turn raw filter input into the lists of values the package expects.

        Comma-separated input is split, keeping commas that belong to a valid value
        ('Hotels, Restaurants & Leisure'). Values that match no option are passed on
        unchanged, so the package rejects them with its own message; they are also
        returned separately so suggestions can be added to that message.

        Args:
            tool_name (str): The asset class tool name.
            filters (dict[str, Any]): Field -> raw value (None/empty values are skipped).
            include_delisted (bool): Whether delisted entries are part of the request.

        Returns:
            tuple[dict[str, list[str]], dict[str, list[str]]]: Field -> resolved values,
                and field -> values that match no option.

        Raises:
            QueryError: For a field that is not a filter of the asset class.
        """
        spec = self.specs[tool_name]
        instance = self.get_instance(tool_name)
        exclude_delisted = spec.supports_delisted and not include_delisted

        resolved: dict[str, list[str]] = {}
        unknown: dict[str, list[str]] = {}
        for name, raw in filters.items():
            if raw is None or raw in ("", []):
                continue
            if name not in spec.get_filters():
                close = suggest(name, spec.get_filters(), 3)
                hint = f" Did you mean: {', '.join(close)}?" if close else ""
                raise QueryError(
                    f"'{name}' is not a filter of {tool_name}.{hint} "
                    f"Available filters: {', '.join(spec.get_filters())}."
                )
            values, missing = resolve_values(
                raw, instance.get_lowercase_options(name, exclude_delisted)
            )
            resolved[name] = values
            if missing:
                unknown[name] = missing
        return resolved, unknown

    def _call_package(
        self,
        tool_name: str,
        call: Any,
        unknown: dict[str, list[str]],
        include_delisted: bool,
    ) -> Any:
        """
        Run a package call, turning its ValueError into a QueryError with suggestions.

        Args:
            tool_name (str): The asset class tool name.
            call (Callable[[], Any]): The package call to run.
            unknown (dict[str, list[str]]): Field -> values that match no option.
            include_delisted (bool): Whether delisted entries are part of the request.

        Returns:
            Any: The call's result.

        Raises:
            QueryError: The package's message plus "Did you mean" suggestions.
        """
        with redirect_stdout_to_stderr():
            try:
                return call()
            except ValueError as error:
                hints = "".join(
                    self._create_suggestion_text(
                        tool_name, name, values, include_delisted
                    )
                    for name, values in unknown.items()
                )
                raise QueryError(f"{error}{hints}") from error

    def _create_suggestion_text(
        self, tool_name: str, name: str, unknown: list[str], include_delisted: bool
    ) -> str:
        """
        Create the "Did you mean" text for values that match no option.

        Args:
            tool_name (str): The asset class tool name.
            name (str): The filter name.
            unknown (list[str]): The values that match no option.
            include_delisted (bool): Whether delisted entries are part of the request.

        Returns:
            str: The suggestions, starting with a newline.
        """
        options = self.get_options(tool_name, name, include_delisted)
        lines = []
        for value in unknown:
            close = suggest(value, options)
            if close:
                lines.append(
                    f"Did you mean {' or '.join(repr(c) for c in close)} "
                    f"instead of '{value}'?"
                )
        if len(options) <= 40:
            lines.append(f"Available {name} values: {', '.join(options)}.")
        else:
            lines.append(
                f"There are {len(options)} {name} values; call "
                f"show_options(asset_class='{tool_name}', selection='{name}') to list them."
            )
        return "\n" + "\n".join(lines)

    def resolve_columns(self, tool_name: str, show_columns: list[str]) -> list[str]:
        """
        Validate requested column names (case-insensitive) against the dataset.

        Args:
            tool_name (str): The asset class tool name.
            show_columns (list[str]): Requested column names.

        Returns:
            list[str]: The columns, starting with the symbol column.

        Raises:
            QueryError: For an unknown column, with suggestions.
        """
        available = self.get_instance(tool_name).get_columns()
        by_lower = {column.lower(): column for column in available}
        columns = [available[0]]
        for requested in show_columns:
            column = by_lower.get(requested.strip().lower())
            if column is None:
                close = suggest(requested, available, 3)
                hint = f" Did you mean: {', '.join(close)}?" if close else ""
                raise QueryError(
                    f"Unknown column '{requested}' for {tool_name}.{hint} "
                    f"Available columns: {', '.join(available)}."
                )
            if column not in columns:
                columns.append(column)
        return columns

    def _build_query_expressions(
        self, columns: list[str], query: str
    ) -> tuple[pl.Expr, pl.Expr]:
        """
        Build the match filter and relevance rank for a free-text query.

        Matching is a case-insensitive literal substring on symbol and name (no regex,
        so 'S&P 500' or 'BRK.B' need no escaping), plus an exact match on identifier
        columns such as ISIN where the asset class has them.

        Args:
            columns (list[str]): The columns of the dataset, the symbol column first.
            query (str): The free-text query.

        Returns:
            tuple[pl.Expr, pl.Expr]: The boolean filter and an integer rank (0 = best).
        """
        needle = query.strip().lower()
        symbol = pl.col(columns[0]).str.to_lowercase()
        name = pl.col("name").str.to_lowercase() if "name" in columns else None

        identifier = pl.lit(False)
        for column in self._identifier_columns:
            if column in columns:
                identifier = identifier | (pl.col(column).str.to_lowercase() == needle)
        identifier = identifier.fill_null(False)

        match = symbol.str.contains(needle, literal=True).fill_null(False) | identifier
        if name is not None:
            match = match | name.str.contains(needle, literal=True).fill_null(False)

        rank = pl.when((symbol == needle) | identifier).then(0)
        rank = rank.when(symbol.str.starts_with(needle)).then(1)
        if name is not None:
            rank = rank.when(name.str.starts_with(needle)).then(2)
        return match, rank.otherwise(3).cast(pl.Int8)

    @staticmethod
    def _build_tiebreak_columns(columns: list[str]) -> list[pl.Expr]:
        """
        Build the columns that order equally relevant matches.

        Primary listings come first, then larger market caps and shorter names, so
        Apple Inc. is listed before Apple Hospitality.

        Args:
            columns (list[str]): The columns of the dataset, the symbol column first.

        Returns:
            list[pl.Expr]: The tiebreak columns.
        """
        exprs = [
            pl.col(columns[0])
            .str.contains(".", literal=True)
            .fill_null(True)
            .alias("_secondary"),
            (
                pl.col("market_cap")
                .replace_strict(
                    {tier: i for i, tier in enumerate(MARKET_CAP_ORDER)},
                    default=len(MARKET_CAP_ORDER),
                    return_dtype=pl.Int8,
                )
                .fill_null(len(MARKET_CAP_ORDER))
                if "market_cap" in columns
                else pl.lit(len(MARKET_CAP_ORDER), dtype=pl.Int8)
            ).alias("_cap"),
            (
                pl.col("name").str.len_chars().fill_null(10_000)
                if "name" in columns
                else pl.lit(0)
            ).alias("_name_length"),
        ]
        return exprs

    def select_page(
        self,
        tool_name: str,
        filters: dict[str, Any],
        query: str | None = None,
        include_delisted: bool = False,
        only_primary_listing: bool = False,
        columns: list[str] | None = None,
        offset: int = 0,
        limit: int = 25,
    ) -> tuple[pl.DataFrame, int]:
        """
        Run a select() with an optional query and return one page.

        The filtering is the package's own select() logic (validation included),
        kept lazy so that only the requested page and columns are materialised;
        collecting a full select() for every call would read up to 100,000+ rows
        with their summaries just to return 25 of them.

        Args:
            tool_name (str): The asset class tool name.
            filters (dict[str, Any]): Raw filter values per field.
            query (str | None): Free-text query on symbol and name.
            include_delisted (bool): Include delisted entries (equities and ETFs).
            only_primary_listing (bool): Only symbols without an exchange suffix.
            columns (list[str] | None): Columns to return; None for the defaults.
            offset (int): Rows to skip.
            limit (int): Rows to return.

        Returns:
            tuple[pl.DataFrame, int]: The page and the total number of matching rows.

        Raises:
            QueryError: For an invalid filter, value or column.
        """
        spec = self.specs[tool_name]
        instance = self.get_instance(tool_name)
        resolved, unknown = self.resolve_filters(tool_name, filters, include_delisted)
        start = time.perf_counter()

        lazy = self._call_package(
            tool_name,
            lambda: instance.filter_lazy_frame(
                resolved,
                only_primary_listing=(
                    only_primary_listing and spec.supports_primary_listing
                ),
                exclude_delisted=spec.supports_delisted and not include_delisted,
            ),
            unknown,
            include_delisted,
        )

        available = instance.get_columns()
        if query and query.strip():
            match, rank = self._build_query_expressions(available, query)
            lazy = (
                lazy.filter(match)
                .with_columns(
                    rank.alias("_rank"), *self._build_tiebreak_columns(available)
                )
                .sort(["_rank", "_secondary", "_cap", "_name_length", available[0]])
            )

        total = lazy.select(pl.len()).collect().item()
        page = lazy.slice(offset, limit).select(columns or available).collect()
        logger.debug(
            "%s: %d rows matched, %d returned in %.3fs",
            tool_name,
            total,
            page.height,
            time.perf_counter() - start,
        )
        return page, total

    def show_options(
        self,
        tool_name: str,
        selection: str | None,
        filters: dict[str, Any],
        include_delisted: bool = False,
    ) -> dict[str, list[str]]:
        """
        Show the available values per field via the package's show_options.

        Args:
            tool_name (str): The asset class tool name.
            selection (str | None): One field, or None for every field.
            filters (dict[str, Any]): Raw filter values narrowing the options.
            include_delisted (bool): Include values only used by delisted entries.

        Returns:
            dict[str, list[str]]: Field -> sorted values.

        Raises:
            QueryError: For an invalid selection, filter or value.
        """
        spec = self.specs[tool_name]
        if selection is not None and selection not in spec.get_filters():
            close = suggest(selection, spec.get_filters(), 3)
            hint = f" Did you mean: {', '.join(close)}?" if close else ""
            raise QueryError(
                f"The selection variable provided is not valid, choose from "
                f"{', '.join(spec.get_filters())}.{hint}"
            )
        resolved, unknown = self.resolve_filters(tool_name, filters, include_delisted)
        kwargs: dict[str, Any] = {"selection": selection, "as_pandas": False}
        if spec.supports_delisted:
            kwargs["exclude_delisted"] = not include_delisted
        instance = self.get_instance(tool_name)
        result = self._call_package(
            tool_name,
            lambda: instance.show_options(**kwargs, **resolved),
            unknown,
            include_delisted,
        )
        if selection is not None:
            return {selection: result.to_list()}
        return {name: values.to_list() for name, values in result.items()}

    def count_entries(self, tool_name: str) -> tuple[int, int]:
        """
        Count the entries of an asset class.

        Args:
            tool_name (str): The asset class tool name.

        Returns:
            tuple[int, int]: Listed entries and delisted entries.
        """
        instance = self.get_instance(tool_name)
        lazy = instance.get_lazy_frame()
        if "delisted" in lazy.collect_schema():
            row = (
                lazy.select(
                    (pl.col("delisted") != "True").sum().alias("listed"),
                    (pl.col("delisted") == "True").sum().alias("delisted"),
                )
                .collect()
                .row(0)
            )
            return int(row[0]), int(row[1])
        return int(lazy.select(pl.len()).collect().item()), 0

    def search_instruments(
        self,
        query: str,
        tool_names: list[str],
        include_delisted: bool = False,
        offset: int = 0,
        limit: int = 25,
    ) -> tuple[pl.DataFrame, int, dict[str, int]]:
        """
        Search symbol, name and identifiers across several asset classes.

        Each asset class contributes at most offset + limit best matches, which is
        enough to build any page of the merged, relevance-ordered result.

        Args:
            query (str): The free-text query.
            tool_names (list[str]): Asset classes to search.
            include_delisted (bool): Include delisted equities and ETFs.
            offset (int): Rows to skip in the merged result.
            limit (int): Rows to return.

        Returns:
            tuple[pl.DataFrame, int, dict[str, int]]: The page, the total number of
                matches, and the number of matches per asset class.
        """
        output_columns = [
            "symbol",
            "name",
            "currency",
            "exchange",
            "category",
            "country",
        ]
        frames = []
        per_class: dict[str, int] = {}
        start = time.perf_counter()
        for tool_name in tool_names:
            spec = self.specs[tool_name]
            instance = self.get_instance(tool_name)
            available = instance.get_columns()
            lazy = instance.get_lazy_frame(
                spec.supports_delisted and not include_delisted
            )
            match, rank = self._build_query_expressions(available, query)
            lazy = lazy.filter(match)
            per_class[tool_name] = lazy.select(pl.len()).collect().item()
            if not per_class[tool_name]:
                continue

            def select_column(
                name: str, source: str, columns: list[str] = available
            ) -> pl.Expr:
                if source in columns:
                    return pl.col(source).alias(name)
                return pl.lit(None, dtype=pl.String).alias(name)

            frames.append(
                lazy.with_columns(
                    rank.alias("_rank"), *self._build_tiebreak_columns(available)
                )
                .sort(["_rank", "_secondary", "_cap", "_name_length", available[0]])
                .head(offset + limit)
                .select(
                    pl.lit(tool_name).alias("asset_class"),
                    pl.col(available[0]).alias("symbol"),
                    *(
                        select_column(
                            name, spec.category_column if name == "category" else name
                        )
                        for name in output_columns[1:]
                    ),
                    "_rank",
                    "_secondary",
                    "_cap",
                    "_name_length",
                )
                .collect()
            )

        total = sum(per_class.values())
        if not frames:
            return pl.DataFrame(schema=["asset_class", *output_columns]), 0, per_class
        merged = (
            pl.concat(frames)
            .sort(["_rank", "_secondary", "_cap", "_name_length", "symbol"])
            .slice(offset, limit)
            .drop("_rank", "_secondary", "_cap", "_name_length")
        )
        logger.debug(
            "search_instruments(%r): %d matches in %.3fs",
            query,
            total,
            time.perf_counter() - start,
        )
        return merged, total, per_class
