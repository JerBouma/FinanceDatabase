"""Tools Model"""

__docformat__ = "google"

from typing import Annotated, Any, Literal

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pydantic import Field

from financedatabase.mcp_server.analytics_model import UsageAnalytics
from financedatabase.mcp_server.coercion_model import (
    convert_to_boolean,
    convert_to_int,
    split_values,
    suggest,
)
from financedatabase.mcp_server.formatting_model import (
    convert_to_json,
    format_markdown_table,
    format_page,
)
from financedatabase.mcp_server.provider_model import DatabaseProvider, QueryError
from financedatabase.mcp_server.registry_model import run_tool
from financedatabase.utilities.logger_model import get_logger

logger = get_logger()

AssetClass = Literal[
    "equities", "etfs", "funds", "indices", "currencies", "cryptos", "moneymarkets"
]


class UtilityToolRegistry:
    """
    Registers the discovery tools on a FastMCP instance.

    Args:
        mcp (FastMCP): The FastMCP server instance to register tools on.
        provider (DatabaseProvider): The query engine serving the tools.
        limits (dict[str, int]): Output limits from config.yaml.
        analytics (UsageAnalytics | None): Counts the tool calls when usage analytics
            are on.
    """

    def __init__(
        self,
        mcp: FastMCP,
        provider: DatabaseProvider,
        limits: dict[str, int],
        analytics: UsageAnalytics | None = None,
    ) -> None:
        """
        Initializes the UtilityToolRegistry.

        Args:
            mcp (FastMCP): The FastMCP server instance to register tools on.
            provider (DatabaseProvider): The query engine serving the tools.
            limits (dict[str, int]): Output limits (default_limit, max_limit,
                max_text_length, default_options, max_options, overview_options).
            analytics (UsageAnalytics | None): Counts the tool calls when usage
                analytics are on. Defaults to None.
        """
        self._mcp = mcp
        self._provider = provider
        self._analytics = analytics
        self._limits = {key: int(value) for key, value in limits.items()}

    def register_all_tools(self) -> int:
        """
        Register all utility tools on the FastMCP instance.

        Returns:
            int: Number of utility tools registered.
        """
        tools = [
            (self.search_categories, "search_categories", "List Asset Classes"),
            (self.show_options, "show_options", "Show Filter Options"),
            (self.search_instruments, "search_instruments", "Search Instruments"),
        ]
        for method, tool_name, title in tools:
            tool = method
            if self._analytics is not None:
                tool = self._analytics.wrap_tool(tool_name, method)
            self._mcp.add_tool(
                tool,
                name=tool_name,
                description=method.__doc__ or "",
                annotations=ToolAnnotations(
                    title=title,
                    readOnlyHint=True,
                    idempotentHint=True,
                    openWorldHint=False,
                ),
                structured_output=False,
            )
        logger.debug("Registered %d utility tools.", len(tools))
        return len(tools)

    def _resolve_asset_classes(self, value: Any) -> list[str]:
        """
        Resolve an asset class selection: 'all', a name, or comma-separated names.

        Args:
            value (Any): The raw selection.

        Returns:
            list[str]: The asset class names.

        Raises:
            QueryError: For an unknown asset class, with suggestions.
        """
        names = [name.lower() for name in split_values(value)]
        if not names or "all" in names:
            return list(self._provider.specs)
        unknown = [name for name in names if name not in self._provider.specs]
        if unknown:
            close = suggest(unknown[0], self._provider.specs, 3)
            hint = f" Did you mean: {', '.join(close)}?" if close else ""
            raise QueryError(
                f"Unknown asset class '{unknown[0]}'.{hint} "
                f"Choose from: all, {', '.join(self._provider.specs)}."
            )
        return list(dict.fromkeys(names))

    def search_categories(self) -> str:
        """
        List the asset classes in the Finance Database, with their tool, size and filters.

        Use this first to see what is available. Each asset class has its own tool
        (e.g. `equities`) whose filters are listed here; `show_options` gives the
        valid values of each filter.

        Returns:
            str: Markdown table of asset classes.
        """

        def build_response() -> str:
            rows = []
            for name, spec in self._provider.specs.items():
                try:
                    listed, delisted = self._provider.count_entries(name)
                    entries = f"{listed:,}" + (
                        f" (+{delisted:,} delisted)" if delisted else ""
                    )
                except Exception as error:
                    logger.warning("Could not count %s: %s", name, error)
                    entries = "n/a"
                rows.append(
                    [
                        f"`{name}`",
                        spec.display_name,
                        entries,
                        ", ".join(spec.get_filters()),
                        spec.summary or spec.description,
                    ]
                )
            table = format_markdown_table(
                ["Tool", "Asset class", "Entries", "Filters", "Description"], rows
            )
            return (
                f"{table}\n\n"
                "**Tip:** `search_instruments('apple')` finds a symbol in every asset "
                "class; `show_options('equities', 'sector')` lists the valid values of "
                "a filter."
            )

        return run_tool("search_categories", build_response)

    def show_options(
        self,
        asset_class: Annotated[
            AssetClass,
            Field(description="The asset class, e.g. 'equities' or 'etfs'."),
        ],
        selection: Annotated[
            str | None,
            Field(
                description="The filter to list the values of, e.g. 'sector', 'country', "
                "'industry' (equities) or 'category', 'family' (ETFs and funds). Leave "
                "empty for an overview of every filter."
            ),
        ] = None,
        filters: Annotated[
            dict[str, str | list[str]] | None,
            Field(
                description="Optional filters narrowing the options, e.g. "
                "{'country': 'Netherlands'} to list only the sectors present in the "
                "Netherlands. Values may be comma-separated."
            ),
        ] = None,
        include_delisted: Annotated[
            bool,
            Field(
                description="Include values only used by delisted entries (equities and ETFs)."
            ),
        ] = False,
        limit: Annotated[
            int | None,
            Field(
                description="Maximum values to return (default 100, maximum 500); the "
                "total count is always given."
            ),
        ] = None,
    ) -> str:
        """
        Show the valid values of a filter (e.g. every sector or country) for an asset class.

        Use this before filtering an asset class tool so the exact values are known.
        Filters narrow the options to what actually occurs, e.g. the industries of
        the 'Health Care' sector in Germany.

        Returns:
            str: Compact JSON with the values and their total count.
        """

        def build_response() -> str:
            spec_name = str(asset_class).lower()
            if spec_name not in self._provider.specs:
                self._resolve_asset_classes(spec_name)  # raises with suggestions
            delisted = convert_to_boolean(include_delisted)
            if filters is not None and not isinstance(filters, dict):
                raise QueryError(
                    "filters must be an object such as {'country': 'Netherlands'}."
                )
            options = self._provider.show_options(
                spec_name, selection or None, dict(filters or {}), delisted
            )

            if selection:
                cap = convert_to_int(
                    limit,
                    self._limits["default_options"],
                    1,
                    self._limits["max_options"],
                )
                values = options[selection]
                payload: dict[str, Any] = {
                    "asset_class": spec_name,
                    "selection": selection,
                    "total": len(values),
                    "returned": min(cap, len(values)),
                    "values": values[:cap],
                }
                if len(values) > cap:
                    payload["_notes"] = [
                        f"Showing {cap} of {len(values)} values. Raise limit (max "
                        f"{self._limits['max_options']}) or narrow with filters. Values "
                        "beyond this list are still valid filters for the asset class "
                        "tools."
                    ]
                return convert_to_json(payload)

            cap = convert_to_int(
                limit,
                self._limits["overview_options"],
                1,
                self._limits["max_options"],
            )
            overview = {
                name: {"total": len(values), "values": values[:cap]}
                for name, values in options.items()
            }
            payload = {"asset_class": spec_name, "options": overview}
            if any(len(values) > cap for values in options.values()):
                payload["_notes"] = [
                    f"Up to {cap} values per filter. Call show_options with a "
                    "selection (e.g. 'country') to see more of one filter."
                ]
            return convert_to_json(payload)

        return run_tool("show_options", build_response)

    def search_instruments(
        self,
        query: Annotated[
            str,
            Field(
                description="Ticker, (part of a) name or identifier to look up, e.g. "
                "'AAPL', 'apple', 'S&P 500', 'bitcoin' or an ISIN such as "
                "'US0378331005'. Case-insensitive."
            ),
        ],
        asset_classes: Annotated[
            str | list[str],
            Field(
                description="Asset classes to search: 'all' (default) or one or more of "
                "equities, etfs, funds, indices, currencies, cryptos, moneymarkets "
                "(comma-separated)."
            ),
        ] = "all",
        include_delisted: Annotated[
            bool,
            Field(description="Include delisted equities and ETFs."),
        ] = False,
        limit: Annotated[
            int,
            Field(description="Rows to return (default 25, maximum 200)."),
        ] = 25,
        offset: Annotated[
            int,
            Field(description="Rows to skip, for paging."),
        ] = 0,
    ) -> str:
        """
        Find instruments by ticker, name or ISIN across all asset classes at once.

        Matches are case-insensitive substrings of the symbol or name (plus exact
        ISIN/CUSIP/FIGI matches), ordered by relevance: exact symbol first, then
        symbols and names starting with the query, primary listings and larger
        companies first. Each row says which asset class tool has the full record.

        Returns:
            str: Compact JSON with the matches and their total count per asset class.
        """

        def build_response() -> str:
            text = (query or "").strip()
            if not text:
                raise QueryError("query is empty; pass a ticker, name or ISIN.")
            names = self._resolve_asset_classes(asset_classes)
            page_limit = convert_to_int(
                limit, self._limits["default_limit"], 1, self._limits["max_limit"]
            )
            page_offset = convert_to_int(offset, 0, 0)
            page, total, per_class = self._provider.search_instruments(
                text,
                names,
                include_delisted=convert_to_boolean(include_delisted),
                offset=page_offset,
                limit=page_limit,
            )
            return format_page(
                page,
                total=total,
                offset=page_offset,
                limit=page_limit,
                max_text_length=self._limits["max_text_length"],
                extra={
                    "query": text,
                    "matches_per_asset_class": {
                        name: count for name, count in per_class.items() if count
                    },
                },
                empty_note="Nothing matches. Try a shorter part of the name or the "
                "ticker without exchange suffix.",
            )

        return run_tool("search_instruments", build_response)
