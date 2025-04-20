import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from rich.console import Console
from rich.logging import RichHandler
from rich.traceback import install

INIT = False


def init_logging() -> None:
    """
    Configure the main logger.
    """
    global INIT

    if INIT:
        return

    # Configure main logger
    logger = logging.getLogger("loomi")

    # Add a NullHandler to prevent "No handlers could be found" warnings
    logger.addHandler(logging.NullHandler())

    INIT = True


def setup_logging(log_dir_path: Path, log_level: int = logging.DEBUG):
    # Define log format
    console_formatter = logging.Formatter("[cyan]%(name)s[/cyan] - %(message)s")
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    # --- Console Handler ---
    # Install rich traceback handling
    install()
    # Create a console with our custom theme
    console = Console()
    # Create handler
    console_handler = RichHandler(
        console=console,
        tracebacks_show_locals=True,
        rich_tracebacks=True,
        markup=True,
        log_time_format="[%x %X.%f]",
    )
    console_handler.setLevel(log_level)
    console_handler.setFormatter(console_formatter)

    # --- File Handler for debug, info and error ---
    # Debug logs
    log_dir_path.mkdir(parents=True, exist_ok=True)
    (log_dir_path / "debug.log").touch()
    (log_dir_path / "info.log").touch()
    (log_dir_path / "error.log").touch()

    file_handler_debug = RotatingFileHandler(
        log_dir_path / "debug.log", maxBytes=5 * 1024 * 1024, backupCount=5
    )  # 5MB max size
    file_handler_debug.setLevel(logging.DEBUG)
    file_handler_debug.setFormatter(formatter)
    # Info logs
    file_handler_info = RotatingFileHandler(
        log_dir_path / "info.log", maxBytes=5 * 1024 * 1024, backupCount=5
    )  # 5MB max size
    file_handler_info.setLevel(logging.INFO)
    file_handler_info.setFormatter(formatter)
    # Error logs
    file_handler_err = RotatingFileHandler(
        log_dir_path / "error.log", maxBytes=5 * 1024 * 1024, backupCount=5
    )  # 5MB max size
    file_handler_err.setLevel(logging.ERROR)
    file_handler_err.setFormatter(formatter)

    # Configure the root logger (this applies globally)
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler_debug)
    root_logger.addHandler(file_handler_info)
    root_logger.addHandler(file_handler_err)

    # Adjust 3rd party loggers
    httpcore_logger = logging.getLogger("httpcore")
    httpcore_logger.setLevel(max(20, log_level))
    httpx_logger = logging.getLogger(name="filelock")
    httpx_logger.setLevel(max(20, log_level))

    root_logger.info(f"Set up logging to write to '{log_dir_path}'")


def get_logger(name: str, level: int | None = None) -> logging.Logger:
    """
    Utility function to get a logger with the specified name.
    Args:
        name (str): The name of the logger, typically the module name.
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
