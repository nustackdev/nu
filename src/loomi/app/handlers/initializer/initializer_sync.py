from __future__ import annotations

from threading import Lock
from types import TracebackType
from typing import Self

from loomi.app.base import SyncApp

from .base import AppCommonInitializer

__all__ = [
    "SyncAppInitializer",
]


class SyncAppInitializer(AppCommonInitializer, SyncApp):
    _lock: Lock

    def initialize(self) -> None:
        """
        Initialize service and its dependencies synchronously.
        """
        if not hasattr(self, "_lock"):
            self._lock = Lock()

        with self._lock:
            self._initialize_model_descriptors()
            self.initialize_services()

    def shutdown(self) -> None:
        """
        Shutdown app and cleanup.

        Raises:
            ShutdownError: If shutdown fails
        """
        with self._lock:
            self.shutdown_services()

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
