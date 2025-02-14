from __future__ import annotations

from loomi.app.base import AsyncApp

from .base import AppCommonServices

__all__ = [
    "AsyncAppServices",
]


class AsyncAppServices(AppCommonServices, AsyncApp):
    """
    App mixin for service location and initialization.
    """

    async def initialize_services(self):
        self._init_service_descriptors()

        for service in self._services.values():
            await service.initialize()

    async def shutdown_services(self):
        for service in self._services.values():
            await service.shutdown()
