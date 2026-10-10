"""Analytics Model

A small usage counter for a hosted MCP server: how often each tool is called, how often
it fails and how long it takes, with the totals published at ``/stats``.

It is off unless ``FD_MCP_ANALYTICS=1`` is set, so a local installation never writes a
statistics file or exposes a ``/stats`` page. The Finance Database needs no API key, so
calls are counted, not people. The counts live in one process; several worker processes
would each keep their own and overwrite each other's file.
"""

__docformat__ = "google"

import atexit
import functools
import inspect
import json
import os
import threading
import time
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from starlette.requests import Request
from starlette.responses import JSONResponse

from financedatabase.utilities.logger_model import get_logger

logger = get_logger()

ENABLED_ENVIRONMENT_VARIABLE = "FD_MCP_ANALYTICS"
LOCATION_ENVIRONMENT_VARIABLE = "FD_MCP_STATS_FILE"
SERVER_NAME_ENVIRONMENT_VARIABLE = "FD_MCP_SERVER_NAME"

SAVE_EVERY_CALLS = 5
DAILY_SERIES_DAYS = 30
TOP_TOOLS = 15


def is_enabled() -> bool:
    """
    Check whether usage analytics are switched on, which they are only explicitly.

    Returns:
        bool: True when FD_MCP_ANALYTICS is 1, true, yes or on.
    """
    return os.environ.get(ENABLED_ENVIRONMENT_VARIABLE, "").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def get_today() -> str:
    """
    Get today's date in UTC.

    Returns:
        str: The date as YYYY-MM-DD.
    """
    return datetime.now(tz=UTC).strftime("%Y-%m-%d")


class UsageAnalytics:
    """
    Counts the tool calls of an MCP server and keeps the counts in a JSON file.

    Every method catches its own errors: counting must never break a tool call.
    """

    def __init__(self, server_name: str, location: str | Path):
        """
        Initialize the counter. The stored counts are read with ``load``.

        Args:
            server_name (str): The name shown on the ``/stats`` page.
            location (str | Path): The JSON file the counts are kept in.
        """
        self.server_name = server_name
        self.location = Path(location)
        self._lock = threading.Lock()
        self._started = time.time()
        self._unsaved_calls = 0

        self.total_calls = 0
        self.failed_calls = 0
        self.calls_per_tool: dict[str, int] = {}
        self.failures_per_tool: dict[str, int] = {}
        self.seconds_per_tool: dict[str, float] = {}
        self.calls_per_day: dict[str, int] = {}

    def record_call(
        self, tool: str, succeeded: bool = True, seconds: float = 0.0
    ) -> None:
        """
        Count a call of a tool, and save every few calls.

        Args:
            tool (str): The tool's name.
            succeeded (bool): Whether the tool returned rather than raised.
            seconds (float): How long the call took.
        """
        try:
            today = get_today()

            with self._lock:
                self.total_calls += 1
                self.calls_per_tool[tool] = self.calls_per_tool.get(tool, 0) + 1
                self.seconds_per_tool[tool] = (
                    self.seconds_per_tool.get(tool, 0.0) + seconds
                )
                self.calls_per_day[today] = self.calls_per_day.get(today, 0) + 1

                if not succeeded:
                    self.failed_calls += 1
                    self.failures_per_tool[tool] = (
                        self.failures_per_tool.get(tool, 0) + 1
                    )

                self._unsaved_calls += 1
                due = self._unsaved_calls >= SAVE_EVERY_CALLS

            if due:
                self.save()
        except Exception as error:  # noqa: BLE001
            logger.debug("Could not count the call of %s: %s", tool, error)

    def wrap_tool(self, tool: str, function: Callable) -> Any:
        """
        Wrap a tool so every call is counted, keeping the signature and annotations
        FastMCP builds the tool's input schema from.

        Args:
            tool (str): The tool's name.
            function (Callable): The tool, synchronous or asynchronous.

        Returns:
            Any: The counting tool.
        """
        if inspect.iscoroutinefunction(function):

            @functools.wraps(function)
            async def count_coroutine(*args, **kwargs):
                started, succeeded = time.perf_counter(), False
                try:
                    result = await function(*args, **kwargs)
                    succeeded = True
                    return result
                finally:
                    self.record_call(tool, succeeded, time.perf_counter() - started)

            wrapper: Any = count_coroutine
        else:

            @functools.wraps(function)
            def count_function(*args, **kwargs):
                started, succeeded = time.perf_counter(), False
                try:
                    result = function(*args, **kwargs)
                    succeeded = True
                    return result
                finally:
                    self.record_call(tool, succeeded, time.perf_counter() - started)

            wrapper = count_function

        # Resolved against the tool's own module: FastMCP would otherwise look string
        # annotations up in this module and fail.
        signature = inspect.signature(function, eval_str=True)
        wrapper.__signature__ = signature
        wrapper.__annotations__ = {
            name: parameter.annotation
            for name, parameter in signature.parameters.items()
            if parameter.annotation is not inspect.Parameter.empty
        }

        if signature.return_annotation is not inspect.Signature.empty:
            wrapper.__annotations__["return"] = signature.return_annotation

        # The wrapper is described by __signature__, so FastMCP must not unwrap it.
        del wrapper.__wrapped__

        return wrapper

    def to_dict(self) -> dict[str, Any]:
        """
        Get the counts as stored in the file.

        Returns:
            dict[str, Any]: The counts.
        """
        return {
            "server": self.server_name,
            "total_calls": self.total_calls,
            "failed_calls": self.failed_calls,
            "calls_per_tool": self.calls_per_tool,
            "failures_per_tool": self.failures_per_tool,
            "seconds_per_tool": self.seconds_per_tool,
            "calls_per_day": self.calls_per_day,
        }

    def load(self) -> None:
        """Read the counts back from the file, if there is one."""
        try:
            if not self.location.exists():
                return

            stored = json.loads(self.location.read_text(encoding="utf-8"))

            with self._lock:
                self.total_calls = int(stored.get("total_calls", 0))
                self.failed_calls = int(stored.get("failed_calls", 0))
                self.calls_per_tool = dict(stored.get("calls_per_tool", {}))
                self.failures_per_tool = dict(stored.get("failures_per_tool", {}))
                self.seconds_per_tool = dict(stored.get("seconds_per_tool", {}))
                self.calls_per_day = dict(stored.get("calls_per_day", {}))
        except Exception as error:  # noqa: BLE001
            logger.warning(
                "Could not read the usage statistics at %s: %s", self.location, error
            )

    def save(self) -> None:
        """Write the counts to the file, through a temporary file so it is never torn."""
        try:
            with self._lock:
                content = json.dumps(self.to_dict(), indent=1, sort_keys=True)
                self._unsaved_calls = 0

            self.location.parent.mkdir(parents=True, exist_ok=True)
            temporary = self.location.with_suffix(".tmp")
            temporary.write_text(content, encoding="utf-8")
            temporary.replace(self.location)
        except Exception as error:  # noqa: BLE001
            logger.warning(
                "Could not save the usage statistics at %s: %s", self.location, error
            )

    def get_summary(self) -> dict[str, Any]:
        """
        Get the totals published at ``/stats``.

        Returns:
            dict[str, Any]: The totals.
        """
        with self._lock:
            today = datetime.now(tz=UTC).date()
            days = [
                (today - timedelta(days=offset)).strftime("%Y-%m-%d")
                for offset in range(DAILY_SERIES_DAYS - 1, -1, -1)
            ]
            top_tools = sorted(
                self.calls_per_tool.items(), key=lambda item: item[1], reverse=True
            )[:TOP_TOOLS]

            return {
                "server": self.server_name,
                "total_calls": self.total_calls,
                "success_rate": (
                    round(1 - self.failed_calls / self.total_calls, 4)
                    if self.total_calls
                    else None
                ),
                "calls_today": self.calls_per_day.get(days[-1], 0),
                "calls_last_7_days": sum(
                    self.calls_per_day.get(day, 0) for day in days[-7:]
                ),
                "daily_calls": [
                    {"date": day, "calls": self.calls_per_day.get(day, 0)}
                    for day in days
                ],
                "top_tools": [
                    {
                        "tool": tool,
                        "calls": calls,
                        "average_seconds": round(
                            self.seconds_per_tool.get(tool, 0.0) / calls, 2
                        ),
                    }
                    for tool, calls in top_tools
                ],
                "uptime_seconds": int(time.time() - self._started),
            }

    def register_route(self, mcp: Any, path: str = "/stats") -> None:
        """
        Publish the totals at a public route of the server.

        Args:
            mcp (Any): The FastMCP server.
            path (str): The route. Defaults to "/stats".
        """
        if not hasattr(mcp, "custom_route"):
            return

        @mcp.custom_route(path, methods=["GET"])
        async def show_stats(request: Request) -> JSONResponse:  # noqa: ARG001
            return JSONResponse(self.get_summary())


def create_from_environment(
    default_server_name: str, default_location: Path
) -> UsageAnalytics | None:
    """
    Set up the counter when FD_MCP_ANALYTICS is on: read the stored counts back and
    save them once more when the server stops.

    Args:
        default_server_name (str): The server name, unless FD_MCP_SERVER_NAME is set.
        default_location (Path): The statistics file, unless FD_MCP_STATS_FILE is set.

    Returns:
        UsageAnalytics | None: The counter, or None when analytics are off.
    """
    if not is_enabled():
        return None

    analytics = UsageAnalytics(
        server_name=os.environ.get(SERVER_NAME_ENVIRONMENT_VARIABLE)
        or default_server_name,
        location=os.environ.get(LOCATION_ENVIRONMENT_VARIABLE) or default_location,
    )
    analytics.load()
    atexit.register(analytics.save)
    logger.info(
        "Usage analytics are on and kept at %s (%d calls so far).",
        analytics.location,
        analytics.total_calls,
    )

    return analytics
