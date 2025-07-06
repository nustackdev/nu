"""
Loomi Logger Interface.

This module provides simple logging protocols for both synchronous and
asynchronous logging operations. Implementations will be provided in loomistd.

Protocols:
    SyncLoggerProtocol: Synchronous logging interface
    AsyncLoggerProtocol: Asynchronous logging interface

Example:
    ```python
    # In user code (App/Service)
    await self.log.info("Processing started")
    await self.log.error("Failed to process item", exc_info=True)

    # Implementation is injected via LoomiCore
    from loomistd.logger import ConsoleLoggerSpec
    logger_spec = ConsoleLoggerSpec(level="INFO")
    ```
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

__all__ = [
    "SyncLoggerProtocol",
    "AsyncLoggerProtocol",
]


@runtime_checkable
class SyncLoggerProtocol(Protocol):
    """
    Protocol for synchronous logging operations.

    Provides standard logging levels with optional extra parameters
    for structured logging, exception info, and custom fields.
    """

    def debug(self, message: str, /, **kwargs: Any) -> None:
        """
        Log a debug message.

        Args:
            message: Log message
            **kwargs: Additional fields (exc_info, extra, etc.)
        """
        ...

    def info(self, message: str, /, **kwargs: Any) -> None:
        """
        Log an info message.

        Args:
            message: Log message
            **kwargs: Additional fields (exc_info, extra, etc.)
        """
        ...

    def warning(self, message: str, /, **kwargs: Any) -> None:
        """
        Log a warning message.

        Args:
            message: Log message
            **kwargs: Additional fields (exc_info, extra, etc.)
        """
        ...

    def error(self, message: str, /, **kwargs: Any) -> None:
        """
        Log an error message.

        Args:
            message: Log message
            **kwargs: Additional fields (exc_info, extra, etc.)
        """
        ...

    def critical(self, message: str, /, **kwargs: Any) -> None:
        """
        Log a critical message.

        Args:
            message: Log message
            **kwargs: Additional fields (exc_info, extra, etc.)
        """
        ...


@runtime_checkable
class AsyncLoggerProtocol(Protocol):
    """
    Protocol for asynchronous logging operations.

    Provides standard logging levels with optional extra parameters
    for structured logging, exception info, and custom fields.
    Useful for async logging backends like database or remote logging.
    """

    async def debug(self, message: str, /, **kwargs: Any) -> None:
        """
        Log a debug message asynchronously.

        Args:
            message: Log message
            **kwargs: Additional fields (exc_info, extra, etc.)
        """
        ...

    async def info(self, message: str, /, **kwargs: Any) -> None:
        """
        Log an info message asynchronously.

        Args:
            message: Log message
            **kwargs: Additional fields (exc_info, extra, etc.)
        """
        ...

    async def warning(self, message: str, /, **kwargs: Any) -> None:
        """
        Log a warning message asynchronously.

        Args:
            message: Log message
            **kwargs: Additional fields (exc_info, extra, etc.)
        """
        ...

    async def error(self, message: str, /, **kwargs: Any) -> None:
        """
        Log an error message asynchronously.

        Args:
            message: Log message
            **kwargs: Additional fields (exc_info, extra, etc.)
        """
        ...

    async def critical(self, message: str, /, **kwargs: Any) -> None:
        """
        Log a critical message asynchronously.

        Args:
            message: Log message
            **kwargs: Additional fields (exc_info, extra, etc.)
        """
        ...
