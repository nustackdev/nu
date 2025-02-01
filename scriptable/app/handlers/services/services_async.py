from __future__ import annotations

from typing import Self

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

    async def start(self):
        await self.initialize_services()

    async def stop(self):
        await self.shutdown_services()

    async def __aenter__(self) -> Self:
        await self.start()
        return self

    async def __aexit__(self, *args) -> None:
        await self.stop()
