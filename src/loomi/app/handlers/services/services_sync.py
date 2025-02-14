from __future__ import annotations

from loomi.app.base import SyncApp

from .base import AppCommonServices

__all__ = [
    "SyncAppServices",
]


class SyncAppServices(AppCommonServices, SyncApp):
    """
    App mixin for service location and initialization.
    """

    def initialize_services(self):
        self._init_service_descriptors()

        for service in self._services.values():
            service.initialize()

    def shutdown_services(self):
        for service in self._services.values():
            service.shutdown()
