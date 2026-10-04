"""
Finance Database MCP Setup Model

Helper functions that locate and write the MCP client configuration files for
Claude Desktop, Claude Code, VS Code, Cursor, Gemini and Windsurf. Each writer
reads any existing file before writing so that unrelated server entries are
never disturbed, and asks before replacing an existing ``finance-database``
entry. The Finance Database needs no API keys, so the entry is only the
command that starts the server.
"""

from __future__ import annotations

import json
import os
import pathlib
import platform
from collections.abc import Callable
from contextlib import suppress

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
from rich.text import Text

# The setup wizard talks to the user on stderr, like the server's logging.
console = Console(stderr=True)

ENTRY_NAME = "finance-database"


def print_banner() -> None:
    """Print the Finance Database MCP setup wizard header."""
    body = Text()
    body.append("\nFinanceDatabase", style="bold cyan")
    body.append("  ·  ", style="dim")
    body.append("MCP Setup Wizard\n", style="bold")
    body.append(
        "300,000+ Equities, ETFs, Funds, Indices, Currencies, Cryptos and Money Markets\n",
        style="dim",
    )
    console.print(Panel(body, border_style="cyan", padding=(0, 2)))
    console.print()


def print_menu() -> None:
    """Print the numbered client-selection menu."""
    text = Text()
    for number, (_, _, name) in CLIENT_MENU.items():
        text.append(f"  {number}  ", style="bold cyan")
        text.append(f"{name}\n")
    text.append("\n  7  ", style="yellow")
    text.append("Remove configuration\n")
    text.append("  0  ", style="dim")
    text.append("Exit", style="dim")
    console.print(
        Panel(
            text,
            title="[bold]Configure Clients[/]",
            subtitle="[dim]e.g. [cyan]13[/] for Claude Desktop + VS Code[/]",
            border_style="dim",
            padding=(1, 2),
        )
    )


def ok(message: str) -> None:
    """Print a success line."""
    console.print(f"  [green]✔[/]  {message}")


def warn(message: str) -> None:
    """Print a warning line."""
    console.print(f"  [yellow]⚠[/]  {message}")


def err(message: str) -> None:
    """Print an error line."""
    console.print(f"  [red]✘[/]  {message}")


def info(message: str) -> None:
    """Print a dim informational line."""
    console.print(f"  [dim]{message}[/]")


def get_claude_config_path() -> pathlib.Path:
    """
    Return the platform-specific path to the Claude Desktop configuration file.

    Returns:
        pathlib.Path: Absolute path to claude_desktop_config.json for the
            current operating system.
    """
    system = platform.system()
    if system == "Darwin":
        return (
            pathlib.Path.home()
            / "Library"
            / "Application Support"
            / "Claude"
            / "claude_desktop_config.json"
        )
    if system == "Windows":
        appdata = os.environ.get("APPDATA") or str(
            pathlib.Path.home() / "AppData" / "Roaming"
        )
        return pathlib.Path(appdata) / "Claude" / "claude_desktop_config.json"
    return pathlib.Path.home() / ".config" / "claude" / "claude_desktop_config.json"


def get_claude_code_config_path() -> pathlib.Path:
    """
    Return the path to the Claude Code user-level MCP configuration file.

    Returns:
        pathlib.Path: Absolute path to ``~/.claude.json``.
    """
    return pathlib.Path.home() / ".claude.json"


def get_gemini_config_path() -> pathlib.Path:
    """
    Return the path to the Gemini CLI MCP configuration file.

    Returns:
        pathlib.Path: Absolute path to ``~/.gemini/settings.json``.
    """
    return pathlib.Path.home() / ".gemini" / "settings.json"


def get_windsurf_config_path() -> pathlib.Path:
    """
    Return the path to the Windsurf MCP configuration file.

    Returns:
        pathlib.Path: Absolute path to ``~/.codeium/windsurf/mcp_config.json``.
    """
    return pathlib.Path.home() / ".codeium" / "windsurf" / "mcp_config.json"


def server_entry() -> dict:
    """
    Return the MCP server config block that starts the server via uvx.

    The entry is portable: it does not depend on a locally installed
    ``financedatabase-mcp`` binary, because uvx downloads and runs the package
    on demand. No environment variables are needed.

    Returns:
        dict: Ready-to-serialise MCP server configuration.
    """
    return {
        "command": "uvx",
        "args": ["--from", "financedatabase[mcp]", "financedatabase-mcp"],
    }


# Maps --client name to (config path given the working directory, outer JSON key,
# display name). VS Code and Cursor configs are workspace-local.
CLIENTS: dict[str, tuple[Callable[[pathlib.Path], pathlib.Path], str, str]] = {
    "claude-desktop": (
        lambda _: get_claude_config_path(),
        "mcpServers",
        "Claude Desktop",
    ),
    "claude-code": (
        lambda _: get_claude_code_config_path(),
        "mcpServers",
        "Claude Code",
    ),
    "vscode": (lambda cwd: cwd / ".vscode" / "mcp.json", "servers", "VS Code"),
    "cursor": (lambda cwd: cwd / ".cursor" / "mcp.json", "mcpServers", "Cursor"),
    "gemini": (lambda _: get_gemini_config_path(), "mcpServers", "Gemini"),
    "windsurf": (lambda _: get_windsurf_config_path(), "mcpServers", "Windsurf"),
}

# The interactive menu numbers, in the order the Finance Toolkit wizard uses.
CLIENT_MENU = {
    "1": CLIENTS["claude-desktop"],
    "2": CLIENTS["claude-code"],
    "3": CLIENTS["vscode"],
    "4": CLIENTS["cursor"],
    "5": CLIENTS["gemini"],
    "6": CLIENTS["windsurf"],
}
MENU_TO_CLIENT = dict(zip(CLIENT_MENU, CLIENTS))


def _read_json(path: pathlib.Path) -> dict:
    """Read a JSON config file, returning an empty dict when absent or invalid."""
    if not path.exists():
        return {}
    with suppress(json.JSONDecodeError, OSError):
        content = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(content, dict):
            return content
    return {}


def write_client_config(
    client: str,
    target_dir: pathlib.Path,
    overwrite: bool = False,
    interactive: bool = False,
) -> bool:
    """
    Write the ``finance-database`` server entry into a client's config file.

    Other entries in the file are preserved. Workspace-local configs (VS Code,
    Cursor) are created in *target_dir*. For a global client whose config
    directory doesn't exist (the client is probably not installed) the block is
    printed to paste manually instead.

    Args:
        client (str): One of claude-desktop, claude-code, vscode, cursor, gemini,
            windsurf.
        target_dir (pathlib.Path): Workspace root used for VS Code and Cursor.
        overwrite (bool): Replace an existing entry without asking.
        interactive (bool): Ask before replacing an existing entry (otherwise an
            existing entry is left alone unless *overwrite* is set).

    Returns:
        bool: True when the config file was written.
    """
    path_fn, outer_key, display = CLIENTS[client]
    config_path = path_fn(target_dir)
    entry = server_entry()

    if client in ("vscode", "cursor"):
        config_path.parent.mkdir(parents=True, exist_ok=True)
    elif not config_path.parent.exists():
        warn(
            f"Config directory not found for [bold]{display}[/].  "
            "Printing the block to paste manually:"
        )
        console.print()
        console.print(json.dumps({outer_key: {ENTRY_NAME: entry}}, indent=2))
        console.print()
        return False

    existing = _read_json(config_path)
    current = existing.get(outer_key, {}).get(ENTRY_NAME)
    if current is not None and not overwrite:
        if current == entry:
            ok(f"{display} is already configured  [dim cyan]{config_path}[/]")
            return False
        warn(
            f"Existing [bold]'{ENTRY_NAME}'[/] entry found in [dim cyan]{config_path}[/]"
        )
        if not interactive:
            info("Use --overwrite to replace it.")
            return False
        console.print(f"  [dim]{json.dumps(current, indent=4)}[/]")
        if not Confirm.ask("  Overwrite this entry?", default=False, console=console):
            info(f"Skipped — existing {display} config left unchanged.")
            return False

    existing.setdefault(outer_key, {})[ENTRY_NAME] = entry
    config_path.write_text(json.dumps(existing, indent=2) + "\n", encoding="utf-8")
    ok(f"{display} config written to [dim cyan]{config_path}[/]")
    return True


def remove_client_config(client: str, target_dir: pathlib.Path) -> bool:
    """
    Remove the ``finance-database`` entry from a client's config file.

    Args:
        client (str): The client name, see ``CLIENTS``.
        target_dir (pathlib.Path): Workspace root used for VS Code and Cursor.

    Returns:
        bool: True when an entry was removed.
    """
    path_fn, outer_key, _ = CLIENTS[client]
    config_path = path_fn(target_dir)
    existing = _read_json(config_path)
    if ENTRY_NAME not in existing.get(outer_key, {}):
        return False
    del existing[outer_key][ENTRY_NAME]
    config_path.write_text(json.dumps(existing, indent=2) + "\n", encoding="utf-8")
    ok(f"Removed [bold]'{ENTRY_NAME}'[/] from [dim cyan]{config_path}[/]")
    return True


def remove_all_configs(target_dir: pathlib.Path) -> None:
    """
    Remove the ``finance-database`` entry from every known client config file.

    Shows what will be removed and asks for confirmation first.

    Args:
        target_dir (pathlib.Path): Working directory used to resolve the VS Code
            and Cursor configs.
    """
    found = []
    for client, (path_fn, outer_key, display) in CLIENTS.items():
        path = path_fn(target_dir)
        if ENTRY_NAME in _read_json(path).get(outer_key, {}):
            found.append((client, display, path))

    if not found:
        console.print()
        info("No Finance Database configuration found — nothing to remove.")
        console.print()
        return

    summary = Text()
    summary.append("The following will be removed:\n\n", style="bold")
    for _, display, path in found:
        summary.append("  ·  ", style="yellow")
        summary.append(f"{display}  ", style="bold")
        summary.append(f"{path}\n", style="dim cyan")
    console.print()
    console.print(
        Panel(
            summary,
            title="[bold yellow]Remove Configuration[/]",
            border_style="yellow",
            padding=(1, 2),
        )
    )
    console.print()
    if not Confirm.ask("  Proceed with removal?", default=False, console=console):
        info("Removal cancelled — nothing was changed.")
        console.print()
        return

    console.print()
    for client, _, _ in found:
        remove_client_config(client, target_dir)
    console.print()
    ok("[bold]Removal complete.[/]  Restart your client(s) to apply.")
    console.print()
