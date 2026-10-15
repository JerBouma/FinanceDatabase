"""Site Model Tests"""

from mcp.server.fastmcp import FastMCP
from starlette.testclient import TestClient

from financedatabase.mcp_server.site_model import register_site_routes


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
