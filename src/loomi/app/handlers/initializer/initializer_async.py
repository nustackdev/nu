from __future__ import annotations

from asyncio import Lock
from types import TracebackType
from typing import Self

from loomi.app.base import AsyncApp

from .base import AppCommonInitializer

__all__ = [
    "AsyncAppInitializer",
]


class AsyncAppInitializer(AppCommonInitializer, AsyncApp):
    _lock: Lock

    async def initialize(self) -> None:
        """
        Initialize app.
        """
        if not hasattr(self, "_lock"):
            self._lock = Lock()

        async with self._lock:
            self._initialize_model_descriptors()
            await self.initialize_services()

    async def shutdown(self) -> None:
        """
        Shutdown app and cleanup.

        Raises:
            ShutdownError: If shutdown fails
        """
        async with self._lock:
            await self.shutdown_services()

    # --- Context Manager Support --- #

    async def __aenter__(self) -> Self:
        """
        Enter async context, initializing service.

        Returns:
            Self for context usage
        """
        await self.initialize()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Exit async context, shutting down service."""
        await self.shutdown()
