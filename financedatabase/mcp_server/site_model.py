"""Site Model"""

__docformat__ = "google"

from pathlib import Path
from typing import Any

from starlette.requests import Request
from starlette.responses import HTMLResponse, Response

ICON_DIRECTORY = Path(__file__).parent / "icons"
FULL_ICON = Path(__file__).parent / "mcpb" / "finance_database_icon.png"
ICONS = {
    "/favicon.ico": (ICON_DIRECTORY / "favicon.ico", "image/x-icon"),
    "/favicon-32.png": (ICON_DIRECTORY / "favicon-32.png", "image/png"),
    "/apple-touch-icon.png": (ICON_DIRECTORY / "apple-touch-icon.png", "image/png"),
    "/icon.png": (FULL_ICON, "image/png"),
}
PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Finance Database MCP</title>
<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32.png">
<link rel="icon" type="image/png" sizes="512x512" href="/icon.png">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
</head>
<body>
<p>This is the Finance Database MCP server; MCP clients connect at <code>/mcp</code>.
See <a href="{website}">{website}</a> for how to add it.</p>
</body>
</html>
"""


def register_site_routes(mcp: Any, website: str) -> None:
    """
    Serve the icons and a short page at the root, so browsers and favicon lookups find the
    Finance Database icon.

    Args:
        mcp (Any): The FastMCP server.
        website (str): The documentation page the root page links to.
    """
    if not hasattr(mcp, "custom_route"):
        return

    for path, (file, media_type) in ICONS.items():
        content = file.read_bytes()

        @mcp.custom_route(path, methods=["GET"])
        async def show_icon(
            request: Request,  # noqa: ARG001
            content: bytes = content,
            media_type: str = media_type,
        ) -> Response:
            return Response(
                content,
                media_type=media_type,
                headers={"Cache-Control": "public, max-age=86400"},
            )

    page = PAGE.format(website=website)

    @mcp.custom_route("/", methods=["GET"])
    async def show_page(request: Request) -> HTMLResponse:  # noqa: ARG001
        return HTMLResponse(page)
