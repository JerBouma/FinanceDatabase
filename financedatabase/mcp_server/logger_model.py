"""Logger Module"""

__docformat__ = "google"

import logging
import os

from financedatabase import logger_model

# Re-exported for the MCP server modules that refer to the logger by name.
LOGGER_NAME = logger_model.LOGGER_NAME


def setup_logger(log_level: int | str | None = None) -> logging.Logger:
    """
    Set up and configure the package logger for the MCP server.

    The handler always writes to stderr: under the stdio transport stdout carries the
    JSON-RPC stream, so a single log line on stdout would corrupt the protocol.

    Args:
        log_level (int | str | None, optional): Logging level. Defaults to the
            FINANCEDATABASE_MCP_LOG_LEVEL environment variable, then INFO.

    Returns:
        logging.Logger: Configured logger instance.
    """
    logger = logger_model.setup_logger()

    # The package already set INFO on import, so an explicit level is applied here.
    if log_level is None:
        log_level = os.environ.get("FINANCEDATABASE_MCP_LOG_LEVEL")
    if log_level is not None:
        logger.setLevel(log_level.upper() if isinstance(log_level, str) else log_level)

    return logger


def get_logger() -> logging.Logger:
    """
    Get the package logger.

    Returns:
        logging.Logger: Logger instance named after the package.
    """
    return logger_model.get_logger()
