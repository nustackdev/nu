from __future__ import annotations

from asyncio import Lock
from types import TracebackType
from typing import Self

from loomi.app.base import AsyncApp

from .base import AppCommonInitializer
from .logger import logger

__all__ = [
    "AsyncAppInitializer",
]


class AsyncAppInitializer(AppCommonInitializer, AsyncApp):
    _lock: Lock

    async def initialize(self) -> None:
        """
        Initialize app.
        """
        logger.debug(f"Initializing app '{self.readable_name}'")

        if not hasattr(self, "_lock"):
            self._lock = Lock()

        async with self._lock:
            # Initialize composite apps
            self._initialize_app_composition_descriptors()
            await self.initialize_apps()

            # Initialize services
            self._initialize_service_descriptors()
            await self.initialize_services()

            # Initialize state descriptors
            self._initialize_model_descriptors()
            self._initialize_state_descriptor()

        logger.info(f"Initialized app '{self.readable_name}'")

    async def shutdown(self) -> None:
        """
        Shutdown app and cleanup.

        Raises:
            ShutdownError: If shutdown fails
        """
        logger.debug(f"Shutting down app '{self.readable_name}'")
        async with self._lock:
            await self.shutdown_apps()

            await self.shutdown_services()
        logger.info(f"Shut down app '{self.readable_name}'")

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
