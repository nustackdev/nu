from __future__ import annotations

from loomi.app.base import SyncApp

from .base import AppCommonComposer

__all__ = [
    "SyncAppComposer",
]


class SyncAppComposer(AppCommonComposer, SyncApp):
    """
    App mixin combining dependency injection and component architecture.

    Features:
    - Declarative dependency specification via Attach

    Example:
        class DataApp(SyncApp):
            storage = Attach(Storage)
            ...
    """

    def initialize_apps(self):
        """
        Initialize apps.
        """
        for app in self._app_deps.values():
            app.initialize()

    def shutdown_apps(self):
        """
        Shutdown app and cleanup.

        Raises:
            ShutdownError: If shutdown fails
        """
        for app in self._app_deps.values():
            app.shutdown()
