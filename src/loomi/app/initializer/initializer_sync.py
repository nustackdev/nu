from __future__ import annotations

from threading import Lock
from types import TracebackType
from typing import Self

from loomi.app.base import SyncApp

from .base import AppCommonInitializer
from .logger import logger

__all__ = [
    "SyncAppInitializer",
]


class SyncAppInitializer(AppCommonInitializer, SyncApp):
    _lock: Lock

    def initialize(self) -> None:
        """
        Initialize service and its dependencies synchronously.
        """
        logger.debug(f"Initializing app '{self.readable_name}'")

        if not hasattr(self, "_lock"):
            self._lock = Lock()

        with self._lock:
            # Initialize composite apps
            self._initialize_app_composition_descriptors()
            self.initialize_apps()

            # Initialize services
            self._initialize_service_descriptors()
            self.initialize_services()

            # Initialize state descriptors
            self._initialize_model_descriptors()
            self._initialize_app_composition_descriptors()
            logger.info(f"Initialized app '{self.readable_name}'")

    def shutdown(self) -> None:
        """
        Shutdown app and cleanup.

        Raises:
            ShutdownError: If shutdown fails
        """
        logger.debug(f"Shutting down app '{self.readable_name}'")

        with self._lock:
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
