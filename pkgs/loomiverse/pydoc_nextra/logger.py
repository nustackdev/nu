"""
Logging utilities for the Python API Reference Generator.

This module provides logging functionality for the generator.
"""

import logging
import sys
from typing import Optional


def setup_logger(
    name: str = "pydoc_nextra",
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    console: bool = True,
) -> logging.Logger:
    """
    Set up a logger with file and/or console handlers.

    Args:
        name: Name of the logger
        level: Logging level
        log_file: Path to log file (if None, no file logging)
        console: Whether to log to console

    Returns:
        Configured logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Clear existing handlers
    logger.handlers = []

    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    # Add file handler if log_file is specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    # Add console handler if console is True
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger


# Create default logger
logger = setup_logger()
