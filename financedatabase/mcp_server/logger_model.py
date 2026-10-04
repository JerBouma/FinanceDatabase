"""Logger Module for the Finance Database MCP server."""

__docformat__ = "google"

import logging
import os
import sys

LOGGER_NAME = "financedatabase"


def setup_logger(log_level: int | str | None = None) -> logging.Logger:
    """
    Set up and configure the package logger with timestamp formatting.

    The handler always writes to stderr: under the stdio transport stdout carries the
    JSON-RPC stream, so a single log line on stdout would corrupt the protocol.

    Args:
        log_level (int | str | None, optional): Logging level. Defaults to the
            FINANCEDATABASE_MCP_LOG_LEVEL environment variable, then INFO.

    Returns:
        logging.Logger: Configured logger instance.
    """
    if log_level is None:
        log_level = os.environ.get("FINANCEDATABASE_MCP_LOG_LEVEL", "INFO").upper()

    logger = logging.getLogger(LOGGER_NAME)

    # Don't override a level that was already set explicitly (e.g. by a test).
    if logger.level == logging.NOTSET:
        logger.setLevel(log_level)

    # Avoid duplicate handlers when the module is imported more than once.
    if not logger.handlers:
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        logger.addHandler(console_handler)

    # Prevents duplicate emission through third-party root handlers on stdout.
    logger.propagate = False

    return logger


def get_logger() -> logging.Logger:
    """
    Get the package logger.

    Returns:
        logging.Logger: Logger instance named after the package.
    """
    return logging.getLogger(LOGGER_NAME)
