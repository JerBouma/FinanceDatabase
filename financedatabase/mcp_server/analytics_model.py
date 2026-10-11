"""Analytics Model

A small usage counter for a hosted MCP server: how often each tool is called, how often
it fails and how long it takes, with the totals published at ``/stats``.

It is off unless ``FD_MCP_ANALYTICS=1`` is set, so a local installation never writes a
statistics file or exposes a ``/stats`` page. The Finance Database needs no API key, so
people are told apart by the client address and user agent of their requests. Neither
is stored: a user is the HMAC of the two under the server's secret, so an identifier
cannot be traced back to an address by anyone who lacks that secret. People behind one
address count as one user, and a new address counts as a new one. The counts live in
one process; several worker processes would each keep their own and overwrite each
other's file.
"""

__docformat__ = "google"

import atexit
import functools
import hashlib
import hmac
import inspect
import json
import os
import secrets
import threading
import time
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from mcp.server.lowlevel.server import request_ctx
from starlette.requests import Request
from starlette.responses import JSONResponse

from financedatabase.utilities.logger_model import get_logger

logger = get_logger()

ENABLED_ENVIRONMENT_VARIABLE = "FD_MCP_ANALYTICS"
LOCATION_ENVIRONMENT_VARIABLE = "FD_MCP_STATS_FILE"
SERVER_NAME_ENVIRONMENT_VARIABLE = "FD_MCP_SERVER_NAME"
SECRET_ENVIRONMENT_VARIABLE = "FD_MCP_SECRET_KEY"

ANONYMOUS = "anonymous"

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


def get_client(request: Any) -> str:
    """
    Get who sent a request: the client address (the visitor's own one behind a
    Cloudflare tunnel or proxy) and the user agent.

    Args:
        request (Any): The HTTP request, None for a local (stdio) call.

    Returns:
        str: The address and user agent, empty when unknown.
    """
    if request is None:
        return ""
    headers = request.headers
    forwarded = headers.get("x-forwarded-for", "").split(",")[0].strip()
    address = (
        headers.get("cf-connecting-ip")
        or forwarded
        or (request.client.host if request.client else "")
    )
    return f"{address}|{headers.get('user-agent', '')}" if address else ""


def get_current_request() -> Any:
    """
    Get the HTTP request of the tool call being handled.

    Returns:
        Any: The request, None outside an HTTP request.
    """
    try:
        return request_ctx.get().request
    except (LookupError, AttributeError):
        return None


def get_secret(location: Path) -> bytes:
    """
    Get the secret users are hashed with: FD_MCP_SECRET_KEY, else one generated once
    and kept next to the statistics file, so identifiers survive a restart.

    Args:
        location (Path): The statistics file.

    Returns:
        bytes: The secret.
    """
    configured = os.environ.get(SECRET_ENVIRONMENT_VARIABLE, "").strip()
    if configured:
        return configured.encode()
    path = location.with_suffix(".secret")
    try:
        return bytes.fromhex(path.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        secret = secrets.token_bytes(32)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(secret.hex(), encoding="utf-8")
        path.chmod(0o600)
        return secret


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

    def __init__(
        self,
        server_name: str,
        location: str | Path,
        secret: bytes = b"",
        resolve_client: Callable[[], str] | None = None,
    ):
        """
        Initialize the counter. The stored counts are read with ``load``.

        Args:
            server_name (str): The name shown on the ``/stats`` page.
            location (str | Path): The JSON file the counts are kept in.
            secret (bytes): The secret clients are hashed with.
            resolve_client (Callable[[], str] | None): Returns who sent the request
                being handled (see get_client), empty when unknown.
        """
        self.server_name = server_name
        self.location = Path(location)
        self._secret = secret
        self._resolve_client = resolve_client or (
            lambda: get_client(get_current_request())
        )
        self._lock = threading.Lock()
        self._started = time.time()
        self._unsaved_calls = 0

        self.total_calls = 0
        self.failed_calls = 0
        self.calls_per_tool: dict[str, int] = {}
        self.failures_per_tool: dict[str, int] = {}
        self.seconds_per_tool: dict[str, float] = {}
        self.calls_per_day: dict[str, int] = {}
        self.calls_per_user: dict[str, int] = {}
        self.first_seen: dict[str, str] = {}
        self.users_per_day: dict[str, list[str]] = {}

    def get_user(self, client: str) -> str:
        """
        Get the identifier of a client.

        Args:
            client (str): The client address and user agent, see get_client.

        Returns:
            str: "u_" and 12 characters of the client's HMAC, or "anonymous".
        """
        if not client:
            return ANONYMOUS
        digest = hmac.new(self._secret, client.encode(), hashlib.sha256).hexdigest()
        return f"u_{digest[:12]}"

    def record_call(
        self,
        tool: str,
        succeeded: bool = True,
        seconds: float = 0.0,
        client: str | None = None,
    ) -> None:
        """
        Count a call of a tool, and save every few calls.

        Args:
            tool (str): The tool's name.
            succeeded (bool): Whether the tool returned rather than raised.
            seconds (float): How long the call took.
            client (str | None): Who sent the call, resolved from the request when
                None.
        """
        try:
            today = get_today()
            user = self.get_user(self._resolve_client() if client is None else client)

            with self._lock:
                self.calls_per_user[user] = self.calls_per_user.get(user, 0) + 1
                if user != ANONYMOUS:
                    self.first_seen.setdefault(user, today)
                    users = self.users_per_day.setdefault(today, [])
                    if user not in users:
                        users.append(user)
                    for day in sorted(self.users_per_day)[:-DAILY_SERIES_DAYS]:
                        del self.users_per_day[day]
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
            "calls_per_user": self.calls_per_user,
            "first_seen": self.first_seen,
            "users_per_day": self.users_per_day,
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
                self.calls_per_user = dict(stored.get("calls_per_user", {}))
                self.first_seen = dict(stored.get("first_seen", {}))
                self.users_per_day = {
                    day: list(users)
                    for day, users in stored.get("users_per_day", {}).items()
                }
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
        Get the totals published at ``/stats``, without any per-user figures.

        Returns:
            dict[str, Any]: The totals.
        """
        with self._lock:
            today = datetime.now(tz=UTC).date()
            days = [
                (today - timedelta(days=offset)).strftime("%Y-%m-%d")
                for offset in range(DAILY_SERIES_DAYS - 1, -1, -1)
            ]
            users = [user for user in self.calls_per_user if user != ANONYMOUS]
            identified_calls = sum(self.calls_per_user[user] for user in users)

            def count_users(period: list[str]) -> int:
                return len(
                    {user for day in period for user in self.users_per_day.get(day, [])}
                )

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
                "unique_users": len(users),
                "users_today": count_users(days[-1:]),
                "users_last_7_days": count_users(days[-7:]),
                "users_last_30_days": count_users(days),
                "new_users_last_7_days": sum(
                    1 for user in users if self.first_seen.get(user, "") >= days[-7]
                ),
                "average_calls_per_user": (
                    round(identified_calls / len(users), 1) if users else None
                ),
                "anonymous_calls": self.calls_per_user.get(ANONYMOUS, 0),
                "calls_today": self.calls_per_day.get(days[-1], 0),
                "calls_last_7_days": sum(
                    self.calls_per_day.get(day, 0) for day in days[-7:]
                ),
                "daily_calls": [
                    {
                        "date": day,
                        "calls": self.calls_per_day.get(day, 0),
                        "users": len(self.users_per_day.get(day, [])),
                    }
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
    save them once more when the server stops. Users are hashed with
    FD_MCP_SECRET_KEY, or a secret generated once next to the statistics file.

    Args:
        default_server_name (str): The server name, unless FD_MCP_SERVER_NAME is set.
        default_location (Path): The statistics file, unless FD_MCP_STATS_FILE is set.

    Returns:
        UsageAnalytics | None: The counter, or None when analytics are off.
    """
    if not is_enabled():
        return None

    location = Path(os.environ.get(LOCATION_ENVIRONMENT_VARIABLE) or default_location)
    analytics = UsageAnalytics(
        server_name=os.environ.get(SERVER_NAME_ENVIRONMENT_VARIABLE)
        or default_server_name,
        location=location,
        secret=get_secret(location),
    )
    analytics.load()
    atexit.register(analytics.save)
    logger.info(
        "Usage analytics are on and kept at %s (%d calls by %d users so far).",
        analytics.location,
        analytics.total_calls,
        len([user for user in analytics.calls_per_user if user != ANONYMOUS]),
    )

    return analytics
