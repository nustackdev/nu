from __future__ import annotations

from loomi.app.base import SyncApp
from loomi.service.base import ServiceState

from .base import AppCommonServices

__all__ = [
    "SyncAppServices",
]


class SyncAppServices(AppCommonServices, SyncApp):
    """
    App mixin for service location and initialization.
    """

    def initialize_services(self):
        for service in self._services.values():
            if service.service_state is not ServiceState.INITIALIZED:
                service.initialize()

    def shutdown_services(self):
        for service in self._services.values():
            if service.service_state is not ServiceState.SHUTDOWN:
                service.shutdown()
