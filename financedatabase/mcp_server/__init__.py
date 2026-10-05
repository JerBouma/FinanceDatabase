"""Finance Database MCP Server — explore 300,000+ categorised financial symbols."""

from financedatabase.mcp_server.logger_model import setup_logger

# Attached when the package is first imported, before any submodule imports FastMCP
# or logs anything: the handler writes to stderr because under the stdio transport
# stdout is the JSON-RPC stream.
setup_logger()
