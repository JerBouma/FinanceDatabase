"""Logger Module"""

__docformat__ = "google"

import logging
import sys

LOGGER_NAME = "financedatabase"


def setup_logger(log_level: int | str = logging.INFO) -> logging.Logger:
    """
    Set up the package logger, which writes to stderr with timestamp formatting.

    Args:
        log_level (int | str, optional): Logging level. Defaults to logging.INFO.

    Returns:
        logging.Logger: Configured logger instance.
    """
    logger = logging.getLogger(LOGGER_NAME)

    if logger.level == logging.NOTSET:
        logger.setLevel(log_level)

    if not logger.handlers:
        # stdout is reserved for JSON-RPC under the MCP stdio transport.
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        logger.addHandler(console_handler)

    logger.propagate = False

    return logger


def get_logger() -> logging.Logger:
    """
    Get the package logger.

    Returns:
        logging.Logger: Logger instance named after the package.
    """
    return logging.getLogger(LOGGER_NAME)
