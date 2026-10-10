"""MCP analytics tests: off by default, counting, storage and the /stats summary."""

import asyncio
import inspect
import json

import pytest

from financedatabase.mcp_server import analytics_model
from financedatabase.mcp_server.analytics_model import UsageAnalytics


def test_analytics_are_off_unless_switched_on(monkeypatch, tmp_path) -> None:
    """Test that a local installation never writes statistics."""
    monkeypatch.delenv(analytics_model.ENABLED_ENVIRONMENT_VARIABLE, raising=False)
    assert (
        analytics_model.create_from_environment("Server", tmp_path / "s.json") is None
    )

    monkeypatch.setenv(analytics_model.ENABLED_ENVIRONMENT_VARIABLE, "1")
    analytics = analytics_model.create_from_environment("Server", tmp_path / "s.json")
    assert analytics is not None
    assert analytics.location == tmp_path / "s.json"


def test_wrapped_tools_are_counted_and_keep_their_signature(tmp_path) -> None:
    """Test that calls and failures are counted and FastMCP still sees the parameters."""
    analytics = UsageAnalytics("Server", tmp_path / "stats.json")

    def lookup(country: str, limit: int = 25) -> str:
        if country == "fail":
            raise ValueError("bad country")
        return country

    wrapped = analytics.wrap_tool("equities", lookup)
    assert list(inspect.signature(wrapped).parameters) == ["country", "limit"]
    assert not hasattr(wrapped, "__wrapped__")

    assert wrapped("Netherlands") == "Netherlands"
    with pytest.raises(ValueError):
        wrapped("fail")

    assert analytics.total_calls == 2
    assert analytics.failed_calls == 1
    assert analytics.calls_per_tool == {"equities": 2}
    assert analytics.failures_per_tool == {"equities": 1}


def test_async_tools_are_counted(tmp_path) -> None:
    """Test that coroutine tools are awaited and counted."""
    analytics = UsageAnalytics("Server", tmp_path / "stats.json")

    async def search(query: str) -> str:
        return query

    wrapped = analytics.wrap_tool("search_instruments", search)
    assert asyncio.run(wrapped("Apple")) == "Apple"
    assert analytics.calls_per_tool == {"search_instruments": 1}


def test_counts_survive_a_restart(tmp_path) -> None:
    """Test that saved counts are read back by a new counter."""
    location = tmp_path / "stats.json"
    analytics = UsageAnalytics("Server", location)
    for _ in range(analytics_model.SAVE_EVERY_CALLS):
        analytics.record_call("etfs", seconds=0.5)
    assert json.loads(location.read_text())["total_calls"] == 5

    restarted = UsageAnalytics("Server", location)
    restarted.load()
    assert restarted.total_calls == 5
    assert restarted.calls_per_tool == {"etfs": 5}


def test_summary_reports_totals_without_raw_counts(tmp_path) -> None:
    """Test the totals published at /stats."""
    analytics = UsageAnalytics("Finance Database", tmp_path / "stats.json")
    analytics.record_call("equities", seconds=1.0)
    analytics.record_call("equities", seconds=3.0)
    analytics.record_call("show_options", succeeded=False)

    summary = analytics.get_summary()
    assert summary["server"] == "Finance Database"
    assert summary["total_calls"] == 3
    assert summary["success_rate"] == round(2 / 3, 4)
    assert summary["calls_today"] == 3
    assert len(summary["daily_calls"]) == analytics_model.DAILY_SERIES_DAYS
    assert summary["top_tools"][0] == {
        "tool": "equities",
        "calls": 2,
        "average_seconds": 2.0,
    }


def test_stats_route_is_registered(tmp_path) -> None:
    """Test that the summary is served at /stats."""
    from mcp.server.fastmcp import FastMCP
    from starlette.testclient import TestClient

    mcp = FastMCP(name="test")
    analytics = UsageAnalytics("Finance Database", tmp_path / "stats.json")
    analytics.record_call("equities")
    analytics.register_route(mcp)

    response = TestClient(mcp.streamable_http_app()).get("/stats")
    assert response.status_code == 200
    assert response.json()["total_calls"] == 1
