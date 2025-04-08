from __future__ import annotations

from loomi.app.base import AsyncApp

from .base import AppCommonComposer

__all__ = [
    "AsyncAppComposer",
]


class AsyncAppComposer(AppCommonComposer, AsyncApp):
    """
    App mixin combining dependency injection and component architecture.

    Features:
    - Declarative dependency specification via AppDescriptor

    Example:
        class CalculatorApp(AsyncApp):
            adder = AppDescriptor(AdderApp)
            ...
    """

    async def initialize_apps(self):
        """
        Initialize apps.
        """
        for app in self._app_deps.values():
            await app.initialize()

    async def shutdown_apps(self):
        """
        Shutdown app and cleanup.

        Raises:
            ShutdownError: If shutdown fails
        """
        for app in self._app_deps.values():
            await app.shutdown()
