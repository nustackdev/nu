from __future__ import annotations

from scriptable.service.base import ServiceBase, ServiceState
from scriptable.service.lib.service_registry import RegistryError


class ServiceCommonInitializer(ServiceBase):
    """
    Async implementation of service initialization and lifecycle management.

    This mixin provides async implementations for service initialization,
    shutdown, and lifecycle management. It should be used with BaseService
    for async service implementations.
    """

    @property
    def service_state(self) -> ServiceState:
        """
        Current service lifecycle state.

        Returns:
            Current ServiceState or ERROR if state unavailable
        """
        try:
            return self._registry.get_service_state(self)
        except RegistryError:
            return ServiceState.ERROR

    @property
    def is_initialized(self) -> bool:
        """Check if service is fully initialized."""
        return self.service_state == ServiceState.INITIALIZED

    def __repr__(self) -> str:
        """String representation including spec."""
        return f"<Service '{self.readable_name}' ('{self.service_state}'): spec=({self.spec})>"
