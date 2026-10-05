"""MCP controller tests: caching, stdout hygiene, entry points, setup and packaging."""

import asyncio
import json
import logging
import os
import pathlib
import re
import subprocess
import sys
import threading

import httpx
import polars as pl
import pytest
import yaml
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

import financedatabase as fd
from financedatabase.mcp_server import setup_model
from financedatabase.mcp_server.coercion_model import (
    resolve_values,
    split_values,
    suggest,
    to_int,
)
from financedatabase.mcp_server.formatting_model import format_page, truncate_text
from financedatabase.mcp_server.mcp_controller import provider as server_provider
from financedatabase.mcp_server.provider_model import DatabaseProvider
from tests.mcp_server.conftest import call_json, call_text

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
SERVER_DIR = REPO_ROOT / "financedatabase" / "mcp_server"


# ── Instance cache ────────────────────────────────────────────────────────────


@pytest.fixture
def counting_cryptos(monkeypatch, server):
    """Replace fd.Cryptos with a subclass counting its constructions."""
    created = []

    class CountingCryptos(fd.Cryptos):
        def __init__(self, *args, **kwargs):
            created.append(kwargs)
            super().__init__(*args, **kwargs)

    monkeypatch.setattr(fd, "Cryptos", CountingCryptos)
    server.provider._instances.pop("cryptos", None)
    yield created
    server.provider._instances.pop("cryptos", None)


def test_instance_is_created_once_and_reused(server, counting_cryptos):
    """Test that every call reuses one instance, created lazily with local data."""
    assert counting_cryptos == []
    call_json(server.mcp, "cryptos", {"limit": 2})
    call_json(server.mcp, "cryptos", {"query": "ethereum"})
    call_json(server.mcp, "show_options", {"asset_class": "cryptos"})
    call_json(
        server.mcp, "search_instruments", {"query": "eth", "asset_classes": "cryptos"}
    )
    assert counting_cryptos == [{"use_local_location": True}]
    assert server.provider.get_instance("cryptos") is server.provider.get_instance(
        "cryptos"
    )


def test_concurrent_first_use_constructs_once(server, counting_cryptos):
    """Test that the per-class lock lets parallel first calls share one instance."""
    instances = []
    threads = [
        threading.Thread(
            target=lambda: instances.append(server.provider.get_instance("cryptos"))
        )
        for _ in range(8)
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert len(counting_cryptos) == 1
    assert all(instance is instances[0] for instance in instances)


def test_instance_is_rebuilt_after_its_ttl(server, counting_cryptos, monkeypatch):
    """Test that an expired instance is recreated so the package can check for updates."""
    server.provider.get_instance("cryptos")
    monkeypatch.setattr(server.provider, "_instance_ttl", 0)
    server.provider.get_instance("cryptos")
    assert len(counting_cryptos) == 2


def test_failed_refresh_keeps_serving_the_cached_instance(monkeypatch):
    """Test that a refresh that cannot reach the data keeps the previous instance."""
    provider = DatabaseProvider(
        [server_provider.specs["moneymarkets"]],
        instance_ttl_seconds=0,
        use_local_location=True,
    )
    first = provider.get_instance("moneymarkets")

    def unavailable(*args, **kwargs):
        raise ValueError("offline")

    monkeypatch.setattr(fd.Moneymarkets, "__init__", unavailable)
    assert provider.get_instance("moneymarkets") is first


# ── stdout hygiene ────────────────────────────────────────────────────────────


def test_logging_never_writes_to_stdout(server, capsys):
    """Test that the package logger writes to stderr only, even at debug level."""
    logger = logging.getLogger("financedatabase")
    assert logger.propagate is False
    assert logger.handlers
    # pytest swaps sys.stderr for a capture object, so check what the stream is not.
    for handler in logger.handlers:
        assert handler.stream not in (sys.stdout, sys.__stdout__)

    previous = logger.level
    logger.setLevel(logging.DEBUG)
    try:
        call_json(server.mcp, "currencies", {"base_currency": "EUR"})
        call_text(server.mcp, "equities", {"sector": "Tech"})
    finally:
        logger.setLevel(previous)
    assert capsys.readouterr().out == ""


def test_package_prints_are_sent_to_stderr(server, monkeypatch, capsys):
    """Test that a print inside the package cannot reach stdout during a tool call."""

    class NoisyMoneymarkets(fd.Moneymarkets):
        def __init__(self, *args, **kwargs):
            print("notice from the package")
            super().__init__(*args, **kwargs)

    monkeypatch.setattr(fd, "Moneymarkets", NoisyMoneymarkets)
    server.provider._instances.pop("moneymarkets", None)
    try:
        call_json(server.mcp, "moneymarkets", {"limit": 1})
    finally:
        server.provider._instances.pop("moneymarkets", None)
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "notice from the package" in captured.err


def test_stdio_server_end_to_end(tmp_path):
    """Test a real stdio session: stdout must carry nothing but JSON-RPC."""
    env = {**os.environ, "FINANCEDATABASE_MCP_LOCAL": "1"}
    parameters = StdioServerParameters(
        command=sys.executable,
        args=["-m", "financedatabase.mcp_server", "--transport", "stdio"],
        env=env,
        cwd=str(REPO_ROOT),
    )

    async def session():
        async with (
            stdio_client(parameters) as (read, write),
            ClientSession(read, write) as client,
        ):
            await client.initialize()
            listed = await client.list_tools()
            result = await client.call_tool(
                "currencies", {"base_currency": "EUR", "quote_currency": "USD"}
            )
            return listed, result

    listed, result = asyncio.run(asyncio.wait_for(session(), timeout=120))
    assert len(listed.tools) == 10
    payload = json.loads(result.content[0].text)
    assert payload["rows"][0]["symbol"] == "EURUSD=X"


# ── Entry points ──────────────────────────────────────────────────────────────


def test_main_defaults_to_stdio(server, monkeypatch):
    """Test that main() runs stdio unless told otherwise."""
    calls = []

    def fake_run(transport):
        calls.append(transport)

    monkeypatch.setattr(server.mcp, "run", fake_run)
    monkeypatch.setattr(sys, "argv", ["financedatabase-mcp"])
    monkeypatch.delenv("MCP_TRANSPORT", raising=False)
    server.main()
    assert calls == ["stdio"]


def test_main_serves_http_with_env_fallbacks(server, monkeypatch):
    """Test the HTTP transports: host/port from flags first, then the environment."""
    served = []

    def fake_run(serve):
        served.append(serve.__self__.config)

    monkeypatch.setattr(server.anyio, "run", fake_run)
    monkeypatch.setattr(server.mcp.settings, "host", server.mcp.settings.host)
    monkeypatch.setattr(server.mcp.settings, "port", server.mcp.settings.port)
    monkeypatch.setattr(sys, "argv", ["financedatabase-mcp", "--port", "0"])
    monkeypatch.setenv("MCP_TRANSPORT", "streamable-http")
    monkeypatch.setenv("MCP_HOST", "127.0.0.1")
    monkeypatch.setenv("MCP_PORT", "9999")
    server.main()
    assert (served[0].host, served[0].port) == ("127.0.0.1", 0)


def test_main_rejects_unknown_transport(server, monkeypatch):
    """Test that an unknown MCP_TRANSPORT fails clearly."""
    monkeypatch.setattr(sys, "argv", ["financedatabase-mcp"])
    monkeypatch.setenv("MCP_TRANSPORT", "carrier-pigeon")
    with pytest.raises(ValueError, match="Unknown MCP transport"):
        server.main()


def test_health_route(server):
    """Test the /health route used by Docker's HEALTHCHECK."""

    async def get():
        transport = httpx.ASGITransport(app=server.mcp.sse_app())
        async with httpx.AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            return await client.get("/health")

    response = asyncio.run(get())
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_module_entry_point_help():
    """Test that `python -m financedatabase.mcp_server --help` works without stdout noise."""
    result = subprocess.run(  # noqa: S603
        [sys.executable, "-m", "financedatabase.mcp_server", "--help"],
        capture_output=True,
        text=True,
        timeout=120,
        check=True,
    )
    assert result.stdout.startswith("usage: financedatabase-mcp")
    assert "--transport" in result.stdout


# ── Setup wizard ──────────────────────────────────────────────────────────────


def test_setup_writes_and_preserves_client_config(tmp_path):
    """Test the uvx entry, preservation of other servers and the overwrite guard."""
    config_path = tmp_path / ".vscode" / "mcp.json"
    config_path.parent.mkdir()
    config_path.write_text(json.dumps({"servers": {"other": {"command": "x"}}}))

    assert setup_model.write_client_config("vscode", tmp_path) is True
    config = json.loads(config_path.read_text())
    assert config["servers"]["other"] == {"command": "x"}
    assert config["servers"]["finance-database"] == {
        "command": "uvx",
        "args": ["--from", "financedatabase[mcp]", "financedatabase-mcp"],
    }

    config["servers"]["finance-database"] = {"command": "old"}
    config_path.write_text(json.dumps(config))
    assert setup_model.write_client_config("vscode", tmp_path) is False
    assert json.loads(config_path.read_text())["servers"]["finance-database"] == {
        "command": "old"
    }
    assert setup_model.write_client_config("vscode", tmp_path, overwrite=True) is True

    assert setup_model.remove_client_config("vscode", tmp_path) is True
    assert json.loads(config_path.read_text())["servers"] == {"other": {"command": "x"}}


def test_setup_cli_for_global_client(tmp_path, monkeypatch, server):
    """Test `financedatabase-mcp-setup --client claude-code` against a fake home."""
    monkeypatch.setattr(pathlib.Path, "home", lambda: tmp_path)
    monkeypatch.setattr(
        sys, "argv", ["financedatabase-mcp-setup", "--client", "claude-code"]
    )
    server.setup()
    config = json.loads((tmp_path / ".claude.json").read_text())
    assert config["mcpServers"]["finance-database"]["command"] == "uvx"
    assert "env" not in config["mcpServers"]["finance-database"]


# ── Formatting and coercion ───────────────────────────────────────────────────


def test_resolve_values_keeps_commas_of_known_values():
    """Test the greedy split that keeps 'Hotels, Restaurants & Leisure' intact."""
    options = {"hotels, restaurants & leisure", "banks", "ab fixed-income shares, inc."}
    assert resolve_values("Banks", options) == (["Banks"], [])
    assert resolve_values("Hotels, Restaurants & Leisure, banks", options) == (
        ["Hotels, Restaurants & Leisure", "banks"],
        [],
    )
    assert resolve_values(["AB Fixed-Income Shares,Inc.", "Bankz"], options) == (
        ["AB Fixed-Income Shares, Inc.", "Bankz"],
        ["Bankz"],
    )
    assert split_values(None) == []


def test_suggest_and_clamp():
    """Test suggestions for typos and partial names, and integer clamping."""
    options = ["Information Technology", "Industrials", "Financials"]
    assert suggest("Tech", options)[0] == "Information Technology"
    assert suggest("financals", options)[0] == "Financials"
    assert to_int("500", 25, 1, 200) == 200
    assert to_int(None, 25, 1, 200) == 25
    assert to_int("abc", 25, 1, 200) == 25
    assert to_int(-3, 0, 0) == 0


def test_format_page_bounds_and_notes():
    """Test truncation, the next-page note and null handling."""
    frame = pl.DataFrame(
        {"symbol": ["A", "B", "C"], "summary": ["x" * 50, None, "short"]}
    )
    payload = json.loads(
        format_page(frame, total=10, offset=0, limit=2, max_text_length=20)
    )
    assert payload["returned"] == 2
    assert payload["rows"][0]["summary"] == "x" * 19 + "…"
    assert payload["rows"][1]["summary"] is None
    assert "offset=2" in payload["_notes"][0]
    assert truncate_text(frame, 100).equals(frame)


# ── Packaging ─────────────────────────────────────────────────────────────────


def test_versions_and_tool_lists_are_in_sync():
    """Test that pyproject, server.json, the mcpb manifest and config agree."""
    # Parsed with regular expressions: tomllib needs Python 3.11 and CI runs 3.10.
    pyproject = (REPO_ROOT / "pyproject.toml").read_text()
    version = re.search(r'(?m)^version = "(.+)"', pyproject).group(1)
    mcp_name = re.search(r'(?m)^mcp-name = "(.+)"', pyproject).group(1)
    server_json = json.loads((REPO_ROOT / "server.json").read_text())
    manifest = json.loads((SERVER_DIR / "mcpb" / "manifest.json").read_text())
    config = yaml.safe_load((SERVER_DIR / "config.yaml").read_text())

    assert server_json["version"] == version
    assert all(package["version"] == version for package in server_json["packages"])
    assert manifest["version"] == version
    assert (
        f'"financedatabase[mcp]=={version}"'
        in (SERVER_DIR / "mcpb" / "pyproject.toml").read_text()
    )

    assert server_json["name"] == mcp_name
    assert (
        (REPO_ROOT / "README.md")
        .read_text()
        .startswith(f"<!-- mcp-name: {mcp_name} -->")
    )

    configured = [t["tool_name"] for t in config["asset_classes"]] + [
        t["tool_name"] for t in config["utility_tools"]
    ]
    assert [tool["name"] for tool in manifest["tools"]] == configured


def test_configured_columns_match_the_data(server):
    """Test that config.yaml lists the real columns, so its descriptions stay true."""
    for name, spec in server.provider.specs.items():
        instance = server.provider.get_instance(name)
        assert spec.columns == instance._lazy.collect_schema().names()
        assert set(spec.default_columns) <= set(spec.columns)
        assert spec.category_column in spec.columns
