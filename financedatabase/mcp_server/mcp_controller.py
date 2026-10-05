"""MCP Server Module"""

__docformat__ = "google"

import argparse
import os
import pathlib
import subprocess
import sys
from typing import Literal

import anyio
import uvicorn
import yaml
from mcp.server.fastmcp import FastMCP
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from financedatabase.mcp_server import setup_model
from financedatabase.mcp_server.provider_model import (
    AssetClassSpec,
    DatabaseProvider,
)
from financedatabase.mcp_server.registry_model import AssetToolRegistry
from financedatabase.mcp_server.tools_model import UtilityToolRegistry
from financedatabase.utilities.logger_model import get_logger

TRANSPORTS: dict[str, Literal["stdio", "sse", "streamable-http"]] = {
    "stdio": "stdio",
    "sse": "sse",
    "streamable-http": "streamable-http",
}

CONFIGURATION_PATH = pathlib.Path(__file__).parent / "config.yaml"


def load_configuration() -> dict:
    """
    Read the server configuration.

    Returns:
        dict: The parsed config.yaml.
    """
    with open(CONFIGURATION_PATH, encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def _build_mcp_app() -> tuple[FastMCP, DatabaseProvider]:
    """
    Bootstrap the MCP application.

    Reads config.yaml, creates the DatabaseProvider (which loads nothing until the
    first tool call) and registers the asset class and utility tools.

    Returns:
        tuple[FastMCP, DatabaseProvider]: The ready-to-run FastMCP instance and the
            provider holding the cached Finance Database instances.
    """
    logger = get_logger()
    configuration = load_configuration()
    known_fields = set(AssetClassSpec.__dataclass_fields__)

    provider = DatabaseProvider(
        specs=[
            AssetClassSpec(**{k: v for k, v in entry.items() if k in known_fields})
            for entry in configuration["asset_classes"]
        ],
        instance_ttl_seconds=int(configuration["cache"]["instance_ttl_seconds"]),
        identifier_columns=configuration.get("identifier_columns", []),
    )

    mcp = FastMCP(
        name=configuration["server"]["name"],
        instructions=configuration["server"]["instructions"],
        log_level="CRITICAL",
        # Bound to all interfaces for Docker; this also leaves FastMCP's localhost-only
        # DNS-rebinding guard off, matching the Finance Toolkit server.
        host="0.0.0.0",  # noqa: S104
    )

    asset_count = AssetToolRegistry(
        mcp=mcp,
        provider=provider,
        filter_descriptions=configuration["filter_descriptions"],
        limits=configuration["limits"],
    ).register_all_tools()
    utility_count = UtilityToolRegistry(
        mcp=mcp,
        provider=provider,
        limits=configuration["limits"],
    ).register_all_tools()

    @mcp.custom_route("/health", methods=["GET"])
    async def check_health(request: Request) -> JSONResponse:  # noqa: ARG001
        return JSONResponse({"status": "ok"})

    logger.info(
        f"Finance Database MCP Server ready. Registered {asset_count} asset class "
        f"tools and {utility_count} utility tools."
    )
    return mcp, provider


mcp, provider = _build_mcp_app()


def main() -> None:
    """
    Start the Finance Database MCP server.

    Starts the server using the transport defined by `--transport`, falling back
    to the MCP_TRANSPORT environment variable and then to stdio, which is the
    correct setting for Claude Desktop, VS Code and other local MCP clients.

    The server contains the following optional arguments:

    --transport {stdio,sse,streamable-http}
        The transport to serve on. Defaults to MCP_TRANSPORT, then stdio.
    --host HOST
        The interface to bind to, for the sse and streamable-http transports
        only. Defaults to MCP_HOST, then 0.0.0.0.
    --port PORT
        The port to bind to, for the sse and streamable-http transports only.
        Defaults to MCP_PORT, then 8000.
    """
    parser = argparse.ArgumentParser(
        prog="financedatabase-mcp",
        description="Start the Finance Database MCP server.",
        epilog=(
            "Every option falls back to its environment variable, so an MCP client "
            "that can only set the environment (MCP_TRANSPORT, MCP_HOST, MCP_PORT) "
            "keeps working unchanged. No API keys are needed. The database is cached "
            "in FINANCEDATABASE_CACHE_DIR (or the platform cache directory) and "
            "checked for updates at most once a day."
        ),
    )
    parser.add_argument(
        "--transport",
        choices=list(TRANSPORTS),
        help="The transport to serve on. Defaults to MCP_TRANSPORT, then stdio.",
    )
    parser.add_argument(
        "--host",
        help=(
            "The interface to bind to, for the sse and streamable-http transports "
            "only. Defaults to MCP_HOST, then 0.0.0.0."
        ),
    )
    parser.add_argument(
        "--port",
        type=int,
        help=(
            "The port to bind to, for the sse and streamable-http transports only. "
            "Defaults to MCP_PORT, then 8000."
        ),
    )

    arguments = parser.parse_args()

    transport = arguments.transport or os.environ.get("MCP_TRANSPORT", "stdio")

    if transport not in TRANSPORTS:
        raise ValueError(
            f"Unknown MCP transport {transport!r}; choose one of {', '.join(TRANSPORTS)}."
        )
    get_logger().info(f"Starting MCP server on transport {transport}")

    if transport in ("sse", "streamable-http"):
        host = arguments.host or os.environ.get("MCP_HOST", "0.0.0.0")  # noqa: S104
        port_env = os.environ.get("MCP_PORT", "8000")
        port = (
            arguments.port
            if arguments.port is not None
            else (int(port_env) if port_env.isdigit() else 8000)
        )

        mcp.settings.host = host
        mcp.settings.port = port

        starlette_app = (
            mcp.streamable_http_app()
            if transport == "streamable-http"
            else mcp.sse_app()
        )
        starlette_app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_methods=["*"],
            allow_headers=["*"],
            expose_headers=["Mcp-Session-Id"],
        )

        config = uvicorn.Config(
            starlette_app,
            host=mcp.settings.host,
            port=mcp.settings.port,
            log_level="info",
            access_log=True,
            proxy_headers=True,
            forwarded_allow_ips="*",
        )
        server = uvicorn.Server(config)
        anyio.run(server.serve)
    else:
        mcp.run(transport=TRANSPORTS[transport])


def run_inspector() -> None:
    """
    Launch the MCP Inspector UI for interactive testing of the server.

    Invokes the MCP Inspector via npx, pointing it at this module so that all
    registered tools can be explored and tested interactively in a browser.
    Exits with the same return code as the Inspector process.

    The Inspector takes no arguments of its own beyond --help.
    """
    argparse.ArgumentParser(
        prog="financedatabase-mcp-inspector",
        description=(
            "Launch the MCP Inspector against the Finance Database MCP server. "
            "Requires npx, which ships with Node.js."
        ),
    ).parse_args()

    sys.exit(
        subprocess.call(  # noqa: S603
            [  # noqa: S607
                "npx",
                "@modelcontextprotocol/inspector",
                sys.executable,
                "-m",
                "financedatabase.mcp_server",
            ]
        )
    )


def run_setup() -> None:
    """
    Run the financedatabase-mcp-setup command.

    When called **without** arguments the interactive setup wizard is launched.

    When called **with** ``--client`` the configuration is written
    non-interactively using a uvx-based server invocation so the entry works
    without a pre-installed local package.

    The setup contains the following optional arguments:

    --client {claude-desktop,claude-code,vscode,cursor,gemini,windsurf}
        Configure a single client without opening the interactive menu.
    --overwrite
        Overwrite an existing configuration. Without this flag the command
        leaves an existing ``finance-database`` entry unchanged.
    """
    parser = argparse.ArgumentParser(
        prog="financedatabase-mcp-setup",
        description="Finance Database MCP Setup Wizard",
    )
    parser.add_argument(
        "--client",
        choices=list(setup_model.CLIENTS),
        metavar="CLIENT",
        help=(
            "Configure a specific client non-interactively. "
            f"Choices: {', '.join(setup_model.CLIENTS)}."
        ),
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite an existing configuration without prompting.",
    )

    args = parser.parse_args()

    setup_model.print_banner()
    if args.client:
        setup_model.write_client_config(args.client, pathlib.Path.cwd(), args.overwrite)
        setup_model.console.print()
        return

    _run_interactive_setup()


def _run_interactive_setup() -> None:
    """
    Launch the interactive setup wizard.
    """
    setup_model.print_info("No API key needed: the Finance Database is free and open.")
    setup_model.console.print()
    setup_model.print_menu()
    setup_model.console.print()
    choice_str = setup_model.console.input("  [cyan]›[/] ").strip()

    if not choice_str or "0" in choice_str:
        setup_model.console.print()
        setup_model.print_info("Setup cancelled.")
        setup_model.console.print()
        return

    cwd = pathlib.Path.cwd()
    if "7" in choice_str:
        setup_model.remove_all_configs(cwd)
        return

    to_process = [
        c for c in dict.fromkeys(choice_str) if c in setup_model.MENU_TO_CLIENT
    ]
    if not to_process:
        setup_model.console.print()
        setup_model.print_error("No valid options selected.")
        return

    setup_model.console.print()
    for choice in to_process:
        client = setup_model.MENU_TO_CLIENT[choice]
        try:
            setup_model.write_client_config(client, cwd, interactive=True)
        except Exception as error:
            setup_model.print_error(
                f"Error configuring {setup_model.CLIENTS[client][2]}: {error}"
            )

    setup_model.console.print()
    setup_model.console.rule("[dim]Done[/]", style="dim")
    setup_model.console.print()
    setup_model.print_success("[bold]All selected configurations updated![/]")
    setup_model.print_info("Restart your client(s) to apply changes.")
    setup_model.console.print()


if __name__ == "__main__":
    main()
