"""Logging utilities for the Redwood package."""

import logging


INIT = False


def init_logging() -> None:
    """Configure the main logger."""
    global INIT

    if INIT:
        return

    # Configure main logger
    logger = logging.getLogger("loomi")

    # Add a NullHandler to prevent "No handlers could be found" warnings
    logger.addHandler(logging.NullHandler())

    INIT = True


def get_logger(name: str, level: int | None = None) -> logging.Logger:
    """Utility function to get a logger with the specified name.

    Args:
        name (str): The name of the logger, typically the module name.
        level (int | None): Optional logging level to set on the logger.

    Returns:
        logging.Logger: Configured logger instance.
    """
    init_logging()

    # From logger name - remove package name prefix and logger suffix
    if name.endswith(".logger") or name.endswith("._logger"):
        name = name.rsplit(".", 1)[0]

    logger = logging.getLogger(name)
    if level is not None:
        logger.setLevel(level)
    return logger
