"""MCP Server Module"""

__docformat__ = "google"

import os

from financedatabase.utilities.logger_model import setup_logger

setup_logger().setLevel(
    os.environ.get("FINANCEDATABASE_MCP_LOG_LEVEL", "INFO").strip().upper()
)
