from __future__ import annotations

from scriptable.app.base import AppSyncBase

from .base import AppCommonServices


class AppServices(AppCommonServices, AppSyncBase):
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
