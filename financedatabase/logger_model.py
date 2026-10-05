"""Logger Module"""

__docformat__ = "google"

import logging
import sys

# Shared by the package and the MCP server so every message has the same name and format.
LOGGER_NAME = "financedatabase"


def setup_logger(log_level: int | str = logging.INFO) -> logging.Logger:
    """
    Set up and configure the package logger with timestamp formatting.

    Args:
        log_level (int | str, optional): Logging level. Defaults to logging.INFO.

    Returns:
        logging.Logger: Configured logger instance.
    """
    logger = logging.getLogger(LOGGER_NAME)

    # Don't override a level that was already set explicitly (e.g. by a test).
    if logger.level == logging.NOTSET:
        logger.setLevel(log_level)

    # Avoid duplicate handlers when the module is imported more than once.
    if not logger.handlers:
        # stderr always: stdout is reserved for JSON-RPC under the MCP stdio transport.
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
