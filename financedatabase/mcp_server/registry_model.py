"""Registry Model"""

__docformat__ = "google"

import inspect
import time
from collections.abc import Callable
from typing import Annotated, Any

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pydantic import Field

from financedatabase.mcp_server.coercion_model import (
    convert_to_boolean,
    convert_to_int,
    split_values,
)
from financedatabase.mcp_server.formatting_model import format_page
from financedatabase.mcp_server.provider_model import (
    AssetClassSpec,
    DatabaseProvider,
    QueryError,
)
from financedatabase.utilities.logger_model import get_logger

logger = get_logger()

MULTI_VALUE_HINT = (
    " Several values: comma-separated (e.g. 'A, B') or a list. Case-insensitive."
)


def run_tool(tool_name: str, call: Callable[[], str]) -> str:
    """
    Run a tool body and return any failure as text instead of raising.

    A raised exception reaches the model as a bare protocol error; a returned
    message explains what went wrong and how to fix the call.

    Args:
        tool_name (str): The tool name, for the log and the message.
        call (Callable[[], str]): The tool body.

    Returns:
        str: The tool output, or an error message.
    """
    start = time.perf_counter()
    try:
        return call()
    except QueryError as error:
        return f"Invalid input for `{tool_name}`: {error}"
    except Exception as error:
        logger.warning("Tool %s failed: %s", tool_name, error, exc_info=True)
        return f"`{tool_name}` failed with error: {type(error).__name__}: {error}"
    finally:
        logger.debug("Tool %s ran in %.3fs", tool_name, time.perf_counter() - start)


class AssetToolRegistry:
    """
    Registers one tool per asset class on a FastMCP instance.

    Args:
        mcp (FastMCP): The FastMCP server instance to register tools on.
        provider (DatabaseProvider): The query engine serving the tools.
        filter_descriptions (dict[str, str]): Description per filter parameter.
        limits (dict[str, int]): Output limits (default_limit, max_limit,
            max_text_length).
    """

    def __init__(
        self,
        mcp: FastMCP,
        provider: DatabaseProvider,
        filter_descriptions: dict[str, str],
        limits: dict[str, int],
    ) -> None:
        """
        Initializes the AssetToolRegistry.

        Args:
            mcp (FastMCP): The FastMCP server instance to register tools on.
            provider (DatabaseProvider): The query engine serving the tools.
            filter_descriptions (dict[str, str]): Description per filter parameter.
            limits (dict[str, int]): Output limits from config.yaml.
        """
        self._mcp = mcp
        self._provider = provider
        self._filter_descriptions = filter_descriptions
        self._default_limit = int(limits["default_limit"])
        self._max_limit = int(limits["max_limit"])
        self._max_text_length = int(limits["max_text_length"])

    def _run_asset_tool(
        self,
        spec: AssetClassSpec,
        kwargs: dict[str, Any],
    ) -> str:
        """
        Answer one asset class tool call.

        Args:
            spec (AssetClassSpec): The asset class being queried.
            kwargs (dict[str, Any]): The tool arguments.

        Returns:
            str: The page as compact JSON.
        """
        notes: list[str] = []
        requested_limit = kwargs.pop("limit", None)
        limit = convert_to_int(requested_limit, self._default_limit, 1, self._max_limit)
        if (
            requested_limit is not None
            and convert_to_int(requested_limit, 0, 0) > self._max_limit
        ):
            notes.append(f"limit is capped at {self._max_limit} rows per call.")
        offset = convert_to_int(kwargs.pop("offset", 0), 0, 0)
        query = kwargs.pop("query", None)
        include_delisted = convert_to_boolean(kwargs.pop("include_delisted", False))
        only_primary_listing = convert_to_boolean(
            kwargs.pop("only_primary_listing", False)
        )
        include_summary = convert_to_boolean(kwargs.pop("include_summary", False))
        show_columns = split_values(kwargs.pop("show_columns", None))

        requested = show_columns or list(spec.default_columns)
        if include_summary and "summary" not in requested:
            position = requested.index("name") + 1 if "name" in requested else 1
            requested.insert(position, "summary")
        if include_delisted and spec.supports_delisted and not show_columns:
            requested.append("delisted")
        columns = self._provider.resolve_columns(spec.tool_name, requested)

        page, total = self._provider.select_page(
            spec.tool_name,
            filters=kwargs,
            query=query,
            include_delisted=include_delisted,
            only_primary_listing=only_primary_listing,
            columns=columns,
            offset=offset,
            limit=limit,
        )
        if "summary" in columns:
            notes.append(
                f"Text longer than {self._max_text_length} characters is truncated (…)."
            )
        return format_page(
            page,
            total=total,
            offset=offset,
            limit=limit,
            max_text_length=self._max_text_length,
            notes=notes,
            extra={"asset_class": spec.tool_name},
        )

    def _build_wrapper(self, spec: AssetClassSpec) -> Callable[..., str]:
        """
        Build the tool function for an asset class with a FastMCP-ready signature.

        Args:
            spec (AssetClassSpec): The asset class specification.

        Returns:
            Callable[..., str]: A function with a replaced ``__signature__``.
        """

        def run_wrapper(**kwargs: Any) -> str:
            return run_tool(
                spec.tool_name, lambda: self._run_asset_tool(spec, dict(kwargs))
            )

        P = inspect.Parameter
        KW = P.KEYWORD_ONLY

        def create_parameter(
            name: str, annotation: Any, default: Any, description: str
        ) -> P:
            return P(
                name,
                KW,
                default=default,
                annotation=Annotated[annotation, Field(description=description)],
            )

        params = [
            create_parameter(
                "query",
                str | None,
                None,
                "Optional free-text search on symbol and name (case-insensitive "
                "substring, e.g. 'apple' or 'AAPL'); an ISIN also matches where "
                "available. Best matches come first.",
            )
        ]
        for name in spec.get_filters():
            description = self._filter_descriptions.get(
                name, f"Filter on {name.replace('_', ' ')}."
            )
            params.append(
                create_parameter(
                    name, str | list[str] | None, None, description + MULTI_VALUE_HINT
                )
            )
        if spec.supports_delisted:
            params.append(
                create_parameter(
                    "include_delisted",
                    bool,
                    False,
                    "Include delisted entries (excluded by default). Adds a "
                    "`delisted` column.",
                )
            )
        if spec.supports_primary_listing:
            params.append(
                create_parameter(
                    "only_primary_listing",
                    bool,
                    False,
                    "Only primary listings (symbols without an exchange suffix such "
                    "as '.L' or '.DE').",
                )
            )
        columns = ", ".join(spec.columns) if spec.columns else "see the data"
        params += [
            create_parameter(
                "show_columns",
                str | list[str] | None,
                None,
                "Columns to return, comma-separated. Default: "
                f"{', '.join(spec.default_columns)}. Available: {columns}.",
            ),
            create_parameter(
                "include_summary",
                bool,
                False,
                "Add the business/fund description (truncated to "
                f"{self._max_text_length} characters). Off by default to keep "
                "responses small.",
            ),
            create_parameter(
                "limit",
                int,
                self._default_limit,
                f"Rows to return (default {self._default_limit}, maximum "
                f"{self._max_limit}).",
            ),
            create_parameter(
                "offset",
                int,
                0,
                "Rows to skip, for paging (see the `_notes` hint in the response).",
            ),
        ]

        run_wrapper.__signature__ = inspect.Signature(params, return_annotation=str)  # type: ignore[attr-defined]
        run_wrapper.__annotations__ = {p.name: p.annotation for p in params}
        run_wrapper.__annotations__["return"] = str
        run_wrapper.__name__ = spec.tool_name
        run_wrapper.__doc__ = spec.description
        return run_wrapper

    def register_all_tools(self) -> int:
        """
        Register one tool per configured asset class.

        Returns:
            int: Number of tools registered.
        """
        for spec in self._provider.specs.values():
            self._mcp.add_tool(
                self._build_wrapper(spec),
                name=spec.tool_name,
                description=spec.description,
                annotations=ToolAnnotations(
                    title=spec.display_name,
                    readOnlyHint=True,
                    idempotentHint=True,
                    openWorldHint=False,
                ),
                structured_output=False,
            )
            logger.debug("Registered asset class tool '%s'", spec.tool_name)
        logger.debug("Registered %d asset class tools.", len(self._provider.specs))
        return len(self._provider.specs)
