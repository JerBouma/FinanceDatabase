"""Shared setup for the MCP server tests.

Every test reads the repository's local compression files (regenerated from
database/ by tests/conftest.py) instead of GitHub, so nothing hits the network.
"""

import asyncio
import json
from typing import Any

import pytest

# The 'mcp' extra is part of the dev dependency group, so it is always installed here.
from financedatabase.mcp_server.provider_model import LOCAL_ENV


@pytest.fixture(autouse=True)
def local_data(monkeypatch):
    """Point the server at the local compression files."""
    monkeypatch.setenv(LOCAL_ENV, "1")


@pytest.fixture(scope="session")
def server():
    """The FastMCP app and its provider, built once like in production."""
    from financedatabase.mcp_server import mcp_controller

    return mcp_controller


def call_text(app, name: str, arguments: dict[str, Any] | None = None) -> str:
    """Call a tool through FastMCP (argument validation included) and return its text."""
    result = asyncio.run(app.call_tool(name, arguments or {}))
    content = result[0] if isinstance(result, tuple) else result
    assert len(content) == 1
    return content[0].text


def call_json(app, name: str, arguments: dict[str, Any] | None = None) -> dict:
    """Call a tool that should succeed and parse its JSON payload."""
    text = call_text(app, name, arguments)
    try:
        return json.loads(text)
    except json.JSONDecodeError:  # pragma: no cover - shows the error text instead
        pytest.fail(f"{name} did not return JSON: {text}")
