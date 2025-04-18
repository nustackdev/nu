from __future__ import annotations

from asyncio import Lock as AsyncioLock
from threading import Lock as ThreadingLock
from types import TracebackType
from typing import Self

from .base import AppABC, AsyncAppABC, SyncAppABC
from .logger import logger
from .types import ExecutorT, StateT, SyncExecutorT, SyncStateT

__all__ = [
    "CommonAppInitializer",
    "SyncAppInitializer",
    "AsyncAppInitializer",
]


class CommonAppInitializer(AppABC[StateT, ExecutorT]):
    """
    Implementation of app initialization and lifecycle management.

    This mixin provides implementations for app initialization and shutdown.
    """

    pass


class AsyncAppInitializer(CommonAppInitializer[StateT, ExecutorT], AsyncAppABC[StateT, ExecutorT]):
    _app_lock: AsyncioLock

    async def initialize(self) -> None:
        """
        Initialize app.
        """
        logger.debug(f"Initializing app '{self.readable_name}'")

        if not hasattr(self, "_lock"):
            self._app_lock = AsyncioLock()

        async with self._app_lock:
            # Initialize composite apps
            self._initialize_app_composition_descriptors()
            await self.initialize_apps()

            # Initialize services
            self._initialize_service_descriptors()
            await self.initialize_services()

            # Initialize state descriptors
            self._initialize_state_descriptor()

            # Initialize engine descriptor
            self._initialize_engine_descriptor()

        logger.info(f"Initialized app '{self.readable_name}'")

    async def shutdown(self) -> None:
        """
        Shutdown app and cleanup.

        Raises:
            ShutdownError: If shutdown fails
        """
        logger.debug(f"Shutting down app '{self.readable_name}'")
        async with self._app_lock:
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


class SyncAppInitializer(
    CommonAppInitializer[SyncStateT, SyncExecutorT], SyncAppABC[SyncStateT, SyncExecutorT]
):
    _app_lock: ThreadingLock

    def initialize(self) -> None:
        """
        Initialize service and its dependencies synchronously.
        """
        logger.debug(f"Initializing app '{self.readable_name}'")

        if not hasattr(self, "_lock"):
            self._app_lock = ThreadingLock()

        with self._app_lock:
            # Initialize composite apps
            self._initialize_app_composition_descriptors()
            self.initialize_apps()

            # Initialize services
            self._initialize_service_descriptors()
            self.initialize_services()

            # Initialize state descriptors
            self._initialize_state_descriptor()

            # Initialize engine descriptor
            self._initialize_engine_descriptor()

        logger.info(f"Initialized app '{self.readable_name}'")

    def shutdown(self) -> None:
        """
        Shutdown app and cleanup.

        Raises:
            ShutdownError: If shutdown fails
        """
        logger.debug(f"Shutting down app '{self.readable_name}'")

        with self._app_lock:
            self.shutdown_apps()
            self.shutdown_services()
            logger.info(f"Shut down app '{self.readable_name}'")

    # --- Context Manager Support --- #

    def __enter__(self) -> Self:
        """
        Enter async context, initializing service.

        Returns:
            Self for context usage
        """
        self.initialize()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Exit async context, shutting down service."""
        self.shutdown()
