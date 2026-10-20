"""Site Model"""

__docformat__ = "google"

from html import escape
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
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Finance Database MCP</title>
<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32.png">
<link rel="icon" type="image/png" sizes="512x512" href="/icon.png">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<style>
  body {{ margin: 0; min-height: 100vh; display: flex; align-items: center; justify-content: center;
          background: linear-gradient(135deg, #0f172a 0%, #020617 100%); color: #f8fafc;
          font-family: Inter, system-ui, -apple-system, "Segoe UI", sans-serif; }}
  main {{ width: 100%; max-width: 640px; padding: 48px 24px; box-sizing: border-box; }}
  img {{ width: 88px; height: 88px; border-radius: 22px; }}
  h1 {{ margin: 20px 0 8px; font-size: 40px; letter-spacing: -0.02em; }}
  h1 span, a {{ color: #38bdf8; }}
  p {{ color: #cbd5e1; line-height: 1.6; }}
  ol {{ padding-left: 22px; color: #cbd5e1; line-height: 1.7; }}
  code {{ font-family: "JetBrains Mono", ui-monospace, monospace; font-size: 15px; color: #f8fafc;
          background: rgba(30, 41, 59, 0.8); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 6px;
          padding: 2px 6px; overflow-wrap: anywhere; }}
  .button {{ display: inline-block; margin-top: 16px; padding: 12px 22px; border-radius: 999px; color: #020617;
             background: #38bdf8; font-weight: 700; text-decoration: none; }}
</style>
</head>
<body>
<main>
<img src="/icon.png" alt="">
<h1>Finance Database <span>MCP</span></h1>
<p>This is an MCP server: it lets AI assistants such as Claude, Copilot and Cursor search and filter
categorised equities, ETFs, indices, currencies and cryptocurrencies. It is meant for MCP clients, not browsers.
To set it up:</p>
<ol>
<li>Add it as a remote (HTTP) MCP server with the URL <code>{url}</code>. In Claude: Customize →
Connectors → Add custom connector.</li>
<li>No sign-in or API key is needed.</li>
<li>Ask, for example: "Which Japanese semiconductor companies are listed?"</li>
</ol>
<p>Or run it locally: <code>uvx --from "financedatabase[mcp]" financedatabase-mcp-setup</code></p>
<a class="button" href="{website}">Setup guide and documentation</a>
</main>
</body>
</html>
"""


def render_setup_page(request: Request, website: str) -> HTMLResponse:
    """
    The setup page for people who open the server in a browser.

    Args:
        request (Request): The request, which gives the server's own URL.
        website (str): The documentation page.

    Returns:
        HTMLResponse: The page.
    """
    return HTMLResponse(
        PAGE.format(url=escape(f"{request.base_url}mcp"), website=escape(website))
    )


def check_browser_request(scope: dict) -> bool:
    """
    Whether a request is a browser opening the page: a GET asking for HTML. MCP clients POST
    JSON or GET an event stream, so they never match.

    Args:
        scope (dict): The ASGI scope.

    Returns:
        bool: True for a browser.
    """
    accept = dict(scope.get("headers", [])).get(b"accept", b"").decode().lower()
    return (
        scope.get("method") == "GET"
        and "text/html" in accept
        and "text/event-stream" not in accept
    )


class SetupPageMiddleware:
    """
    Serve the setup page to browsers at the MCP endpoint; everything else passes through.
    """

    def __init__(self, app: Any, website: str, path: str = "/mcp") -> None:
        self.app, self.website, self.path = app, website, path.rstrip("/")

    async def __call__(self, scope: dict, receive: Any, send: Any) -> None:
        if (
            scope["type"] == "http"
            and scope["path"].rstrip("/") == self.path
            and check_browser_request(scope)
        ):
            await render_setup_page(Request(scope, receive), self.website)(
                scope, receive, send
            )
            return
        await self.app(scope, receive, send)


def register_site_routes(mcp: Any, website: str) -> None:
    """
    Serve the icons and the setup page at the root, so browsers and favicon lookups find the
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

    @mcp.custom_route("/", methods=["GET"])
    async def show_page(request: Request) -> HTMLResponse:
        return render_setup_page(request, website)
