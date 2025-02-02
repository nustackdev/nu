from __future__ import annotations

from scriptable.app.base import AppAsyncBase

from .base import AppCommonServices


class AppServices(AppCommonServices, AppAsyncBase):
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
