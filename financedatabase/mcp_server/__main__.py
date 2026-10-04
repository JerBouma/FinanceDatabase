"""
Allows running the MCP server as a module:

    python -m financedatabase.mcp_server
"""

from financedatabase.mcp_server.mcp_controller import main, mcp  # noqa: F401

if __name__ == "__main__":
    main()
