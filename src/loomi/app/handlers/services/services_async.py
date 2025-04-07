from __future__ import annotations

from loomi.app.base import AsyncApp
from loomi.service.base import ServiceState

from .base import AppCommonServices

__all__ = [
    "AsyncAppServices",
]


class AsyncAppServices(AppCommonServices, AsyncApp):
    """
    App mixin for service location and initialization.
    """

    async def initialize_services(self):
        for service in self._services.values():
            if service.service_state is not ServiceState.INITIALIZED:
                await service.initialize()

    async def shutdown_services(self):
        for service in self._services.values():
            if service.service_state is not ServiceState.SHUTDOWN:
                await service.shutdown()
