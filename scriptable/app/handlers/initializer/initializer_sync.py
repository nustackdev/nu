from __future__ import annotations

from threading import Lock
from typing import Any, Self

from scriptable.app.base import AppSyncBase

from .base import AppCommonInitializer


class AppInitializer(AppCommonInitializer, AppSyncBase):
    def initialize(self) -> None:
        """
        Initialize service and its dependencies synchronously.
        """
        if not hasattr(self, "_lock"):
            self._lock = Lock()

        with self._lock:
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

    def __exit__(self, *exc_info: Any) -> None:
        """Exit async context, shutting down service."""
        self.shutdown()
