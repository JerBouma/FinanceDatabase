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
from financedatabase.mcp_server import ranking_model
from financedatabase.mcp_server.coercion_model import resolve_values, suggest
from financedatabase.mcp_server.ranking_model import PREFERENCE_COLUMNS, RankingProfile
from financedatabase.utilities.logger_model import get_logger

logger = get_logger()

LOCAL_ENV = "FINANCEDATABASE_MCP_LOCAL"


# Number of recent query results kept per provider.
MATCH_CACHE_SIZE = 32
# Up to this many matches filter the data scan; more are joined.
MATCH_FILTER_SIZE = 10_000
# A brand stands for the family that issues at least this share of the instruments
# whose name starts with it.
BRAND_SHARE = 0.8


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
        self._profiles: dict[str, tuple[FinanceDatabase, RankingProfile]] = {}
        self._matches: dict[tuple[str, int, str], pl.DataFrame] = {}
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
                raw,
                instance.get_lowercase_options(name, exclude_delisted),
                expand_prefix=name == "family",
            )
            if missing and name == "family":
                brands = self._resolve_brands(tool_name, missing)
                values = [v for v in values if v not in brands] + [
                    family for family in brands.values() if family
                ]
                missing = [v for v in missing if not brands.get(v)]
            resolved[name] = values
            if missing:
                unknown[name] = missing
        return resolved, unknown

    def _resolve_brands(self, tool_name: str, values: list[str]) -> dict[str, str]:
        """
        Resolve brand names to the family that issues them: when most instruments
        whose name starts with the brand belong to one family, the brand stands for
        it ('iShares' for BlackRock Asset Management).

        Args:
            tool_name (str): The asset class tool name.
            values (list[str]): Family values that match no option.

        Returns:
            dict[str, str]: Value -> family, empty for a value that is no brand.
        """
        lazy = self.get_instance(tool_name).get_lazy_frame()
        brands = {}
        for value in values:
            words = value.strip().lower()
            counts = (
                lazy.filter(
                    pl.col("name").str.to_lowercase().str.starts_with(words + " ")
                    & pl.col("family").is_not_null()
                )
                .group_by("family")
                .len()
                .sort("len", descending=True)
                .collect()
            )
            if counts.height and counts["len"][0] >= BRAND_SHARE * counts["len"].sum():
                brands[value] = counts["family"][0]
        return brands

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

    def _add_listing_ranks(
        self, tool_name: str, lazy: pl.LazyFrame
    ) -> tuple[pl.LazyFrame, RankingProfile, bool]:
        """
        Join the listing ranks of each row where the asset class has listings, and
        get the ranking measurements of the class.

        Args:
            tool_name (str): The asset class tool name.
            lazy (pl.LazyFrame): The (filtered) dataset.

        Returns:
            tuple[pl.LazyFrame, RankingProfile, bool]: The dataset, the measurements
                and whether the listing ranks were joined.
        """
        instance = self.get_instance(tool_name)
        ranks = instance.get_listing_ranks()
        profile = self._get_profile(tool_name)
        symbol = instance.get_columns()[0]
        if ranks is None:
            return lazy, profile, False
        return lazy.join(ranks.lazy(), on=symbol, how="left"), profile, True

    def _add_name_keys(self, tool_name: str, lazy: pl.LazyFrame) -> pl.LazyFrame:
        """
        Join the name key and word form of each row's name (see ranking_model).

        Args:
            tool_name (str): The asset class tool name.
            lazy (pl.LazyFrame): The (filtered) dataset.

        Returns:
            pl.LazyFrame: The dataset with "_key" and "_words" where it has names.
        """
        profile = self._get_profile(tool_name)
        if profile.name_keys is None:
            return lazy
        symbol = self.get_instance(tool_name).get_columns()[0]
        return lazy.join(
            profile.name_keys.lazy().select(symbol, "_key"), on=symbol, how="left"
        )

    def _find_matches(self, tool_name: str, query: str) -> pl.DataFrame:
        """
        Match a query on the search frame of an asset class (see ranking_model). The
        latest results are kept, as a tool counts and then ranks the same matches.

        Args:
            tool_name (str): The asset class tool name.
            query (str): The free-text query.

        Returns:
            pl.DataFrame: The symbol column, "_tier" and "_key" of the matching rows.
        """
        instance = self.get_instance(tool_name)
        cache_key = (tool_name, id(instance), query)
        if cache_key in self._matches:
            return self._matches[cache_key]
        available = instance.get_columns()
        profile = self._get_profile(tool_name)
        match, tier = ranking_model.build_query_expressions(
            available, query, profile, self._identifier_columns
        )
        if profile.name_keys is None:
            frame = instance.get_lazy_frame().select(
                [c for c in [available[0], *self._identifier_columns] if c in available]
            )
            matches = (
                frame.filter(match)
                .select(
                    available[0],
                    tier.alias("_tier"),
                    pl.col(available[0]).alias("_key"),
                )
                .collect()
            )
        else:
            matches = (
                profile.name_keys.lazy()
                .filter(match)
                .select(available[0], tier.alias("_tier"), "_key")
                .collect()
            )
        if len(self._matches) >= MATCH_CACHE_SIZE:
            self._matches.pop(next(iter(self._matches)))
        self._matches[cache_key] = matches
        return matches

    @staticmethod
    def _keep_matches(
        lazy: pl.LazyFrame, symbol: str, matches: pl.DataFrame
    ) -> pl.LazyFrame:
        """
        Keep the rows of the matching symbols. A short list filters the scan, so only
        the matching rows are read; a long one is joined, which is faster for it.

        Args:
            lazy (pl.LazyFrame): The dataset.
            symbol (str): The symbol column.
            matches (pl.DataFrame): The matching rows, see _find_matches.

        Returns:
            pl.LazyFrame: The matching rows of the dataset.
        """
        if matches.height <= MATCH_FILTER_SIZE:
            return lazy.filter(
                pl.col(symbol).is_in(matches.get_column(symbol).implode())
            )
        return lazy.join(matches.lazy().select(symbol), on=symbol, how="semi")

    def _count_matches(
        self, tool_name: str, lazy: pl.LazyFrame, query: str | None
    ) -> int:
        """
        Count the rows matching a query without ranking them.

        Args:
            tool_name (str): The asset class tool name.
            lazy (pl.LazyFrame): The (filtered) dataset.
            query (str | None): The free-text query.

        Returns:
            int: The number of matching rows.
        """
        if query and query.strip():
            symbol = self.get_instance(tool_name).get_columns()[0]
            lazy = self._keep_matches(
                lazy, symbol, self._find_matches(tool_name, query)
            )
        return lazy.select(pl.len()).collect().item()

    def _get_profile(self, tool_name: str) -> RankingProfile:
        """
        Get the ranking measurements of an asset class, made once per instance.

        Args:
            tool_name (str): The asset class tool name.

        Returns:
            RankingProfile: The measurements.
        """
        instance = self.get_instance(tool_name)
        cached = self._profiles.get(tool_name)
        if cached is None or cached[0] is not instance:
            profile = ranking_model.create_profile(
                instance.get_lazy_frame(),
                instance.get_listing_ranks(),
                self._identifier_columns,
            )
            self._profiles[tool_name] = (instance, profile)
        return self._profiles[tool_name][1]

    def _rank_rows(
        self, tool_name: str, lazy: pl.LazyFrame, query: str | None
    ) -> pl.LazyFrame:
        """
        Filter the rows matching a query and order them by relevance, or without a
        query by preference alone (see ranking_model).

        Args:
            tool_name (str): The asset class tool name.
            lazy (pl.LazyFrame): The (filtered) dataset.
            query (str | None): The free-text query.

        Returns:
            pl.LazyFrame: The ordered rows with the ranking columns.
        """
        available = self.get_instance(tool_name).get_columns()
        searching = bool(query and query.strip())
        profile = self._get_profile(tool_name)
        has_listings = self.get_instance(tool_name).get_listing_ranks() is not None
        if searching:
            matches = self._find_matches(tool_name, query)
            lazy = self._keep_matches(lazy, available[0], matches).join(
                matches.lazy(), on=available[0], how="inner"
            )
        elif not has_listings:
            # Name keys mark the duplicates of classes without listings.
            lazy = self._add_name_keys(tool_name, lazy)
        lazy, profile, has_ranks = self._add_listing_ranks(tool_name, lazy)
        lazy = lazy.with_columns(
            *ranking_model.build_preference_columns(available, profile, has_ranks)
        )
        sort_columns = [*PREFERENCE_COLUMNS, available[0]]
        if searching:
            sort_columns = ["_tier", *sort_columns]
        if not has_ranks:
            lazy = ranking_model.mark_duplicates(lazy, sort_columns)
        if searching:
            lazy = lazy.with_columns(
                ranking_model.get_bucket(pl.col("_tier")).alias("_bucket")
            )
            sort_columns = ["_bucket", *sort_columns[1:]]
        return lazy.sort(sort_columns)

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
            only_primary_listing (bool): Only primary listings, see listings_model.
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
        total = self._count_matches(tool_name, lazy, query)
        lazy = self._rank_rows(tool_name, lazy, query)
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
                    (~pl.col("delisted").fill_null(False)).sum().alias("listed"),
                    pl.col("delisted").fill_null(False).sum().alias("delisted"),
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
            per_class[tool_name] = self._count_matches(tool_name, lazy, query)
            if not per_class[tool_name]:
                continue
            lazy = self._rank_rows(tool_name, lazy, query)

            def select_column(
                name: str, source: str, columns: list[str] = available
            ) -> pl.Expr:
                if source in columns:
                    return pl.col(source).alias(name)
                return pl.lit(None, dtype=pl.String).alias(name)

            frames.append(
                lazy.head(offset + limit)
                .select(
                    pl.lit(tool_name).alias("asset_class"),
                    pl.col(available[0]).alias("symbol"),
                    *(
                        select_column(
                            name, spec.category_column if name == "category" else name
                        )
                        for name in output_columns[1:]
                    ),
                    "_bucket",
                    "_tier",
                    "_derivative",
                    "_cap",
                    "_listings",
                    "_name_length",
                )
                .collect()
            )

        total = sum(per_class.values())
        if not frames:
            return pl.DataFrame(schema=["asset_class", *output_columns]), 0, per_class
        merged = ranking_model.interleave_classes(frames).slice(offset, limit)
        logger.debug(
            "search_instruments(%r): %d matches in %.3fs",
            query,
            total,
            time.perf_counter() - start,
        )
        return merged, total, per_class
