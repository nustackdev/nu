from __future__ import annotations

from typing import TYPE_CHECKING, cast

from loomi.descriptors.use_service import ServiceDescriptor
from loomi.service import AsyncService, Service, ServiceState, SyncService

from ..base import AppABC, AsyncAppABC, SyncAppABC
from ..exceptions import ServiceDependencyError
from ..types import ExecutorT, StateT, SyncExecutorT, SyncStateT
from .logger import logger

if TYPE_CHECKING:
    from loomi.spec import Spec

__all__ = [
    "CommonAppServicesHandler",
    "AsyncAppServicesHandler",
    "SyncAppServicesHandler",
]


class CommonAppServicesHandler(AppABC[StateT, ExecutorT]):
    def add_service_dependency(
        self,
        name: str,
        spec: "Spec",
    ) -> "Service":
        """
        Add service dependency.

        Args:
            name: Dependency name
            spec: Spec of the service

        Raises:
            DependencyError: If dependency invalid or creates cycle
        """

        if spec.factory is None:
            raise ServiceDependencyError("Factory not defined for service spec")

        try:
            service = spec.factory(spec)
            self._services[name] = service
        except ServiceDependencyError as e:
            logger.error(f"Failed to attach service '{name}' to '{self.readable_name}': {str(e)}")
            raise

        return service

    def get_service_dependency(self, name: str) -> "Service":
        """
        Get named dependency if it exists.

        Args:
            name: Dependency name to retrieve

        Returns:
            Dependency service
        """
        if name not in self._services.keys():
            raise ServiceDependencyError(
                f"Dependency '{name}' not found for app '{self.readable_name}'"
            )

        return self._services[name]

    def _initialize_service_descriptors(self) -> None:
        app_service_specs = getattr(self, "_specs", {})

        for name, value in self.__class__.__dict__.items():
            if not isinstance(value, ServiceDescriptor):
                continue

            # Get the service spec:
            # First, check if service spec is passed as app __init__ argument
            spec = app_service_specs.get(name, None)

            # If spec is not provided, try to use default spec from descriptor
            if spec is None:
                descriptor = cast(ServiceDescriptor, value)
                if descriptor.spec is not None:
                    spec = descriptor.spec

            # Raise an exception if spec is still not found
            if spec is None:
                logger.error(f"No spec found for dependency '{name}'")
                raise ServiceDependencyError(f"No spec found for dependency '{name}'")

            service = self.add_service_dependency(name, spec)

            setattr(self, name, service)


class AsyncAppServicesHandler(
    CommonAppServicesHandler[StateT, ExecutorT], AsyncAppABC[StateT, ExecutorT]
):
    """
    App mixin for service location and initialization.
    """

    async def initialize_services(self):
        for service in self._services.values():
            if service.service_state is not ServiceState.INITIALIZED:
                if isinstance(service, SyncService):
                    service.initialize()
                elif isinstance(service, AsyncService):
                    await service.initialize()

    async def shutdown_services(self):
        for service in self._services.values():
            if service.service_state is not ServiceState.SHUTDOWN:
                if isinstance(service, SyncService):
                    service.shutdown()
                elif isinstance(service, AsyncService):
                    await service.shutdown()


class SyncAppServicesHandler(
    CommonAppServicesHandler[SyncStateT, SyncExecutorT], SyncAppABC[SyncStateT, SyncExecutorT]
):
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
