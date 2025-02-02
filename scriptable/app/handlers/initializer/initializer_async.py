from __future__ import annotations

from asyncio import Lock
from typing import Any, Self

from scriptable.app.base import AppAsyncBase

from .base import AppCommonInitializer


class AppInitializer(AppCommonInitializer, AppAsyncBase):
    async def initialize(self) -> None:
        """
        Initialize service and its dependencies asynchronously.
        """
        if not hasattr(self, "_lock"):
            self._lock = Lock()

        async with self._lock:
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

    async def __aexit__(self, *exc_info: Any) -> None:
        """Exit async context, shutting down service."""
        await self.shutdown()
