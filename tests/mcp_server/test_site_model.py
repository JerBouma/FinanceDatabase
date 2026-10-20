"""Site Model Tests"""

from mcp.server.fastmcp import FastMCP
from starlette.requests import Request
from starlette.testclient import TestClient

from financedatabase.mcp_server.site_model import (
    SetupPageMiddleware,
    register_site_routes,
    render_setup_page,
)


def test_icons_and_root_page_are_served() -> None:
    """Test that the icons and the root page are served for browsers and favicon lookups."""
    mcp = FastMCP(name="Finance Database")
    register_site_routes(mcp, "https://example.com/mcp")
    client = TestClient(mcp.streamable_http_app())

    icon = client.get("/favicon.ico")
    assert icon.status_code == 200
    assert icon.headers["content-type"] == "image/x-icon"
    assert icon.content[:4] == b"\x00\x00\x01\x00"  # ICO header
    for path in ("/favicon-32.png", "/apple-touch-icon.png", "/icon.png"):
        response = client.get(path)
        assert response.status_code == 200 and response.content[:4] == b"\x89PNG"

    page = client.get("/", follow_redirects=False)
    assert page.status_code == 200
    assert "<title>Finance Database MCP</title>" in page.text
    assert 'href="/favicon-32.png"' in page.text
    assert "https://example.com/mcp" in page.text
    assert "<code>http://testserver/mcp</code>" in page.text


def test_browsers_get_the_setup_page_and_mcp_clients_do_not() -> None:
    """Test that a browser opening the MCP endpoint gets the setup page and MCP clients pass through."""
    mcp = FastMCP(name="Finance Database")
    app = mcp.streamable_http_app()
    app.add_middleware(SetupPageMiddleware, website="https://example.com/mcp")

    with TestClient(app, base_url="http://localhost:8000") as client:
        browser = client.get(
            "/mcp", headers={"Accept": "text/html,application/xhtml+xml,*/*;q=0.8"}
        )
        assert browser.status_code == 200
        assert browser.headers["content-type"].startswith("text/html")
        assert "Setup guide and documentation" in browser.text

        stream = client.get("/mcp", headers={"Accept": "text/event-stream, text/html"})
        assert "Setup guide" not in stream.text

        initialize = client.post(
            "/mcp",
            headers={"Accept": "application/json, text/event-stream"},
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {},
                    "clientInfo": {"name": "test", "version": "1"},
                },
            },
        )
        assert initialize.status_code == 200
        assert "Finance Database" in initialize.text


def test_setup_page_escapes_what_it_shows() -> None:
    """Test that interpolated values cannot inject HTML into the setup page."""
    scope = {"type": "http", "method": "GET", "scheme": "https", "path": "/mcp"}
    scope |= {"query_string": b"", "server": ("localhost", 443), "headers": []}
    page = render_setup_page(Request(scope), 'https://example.com/"><script>').body
    assert b"<script>" not in page and b"&quot;&gt;&lt;script&gt;" in page
