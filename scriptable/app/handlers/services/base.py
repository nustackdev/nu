from typing import TYPE_CHECKING, cast, final

from scriptable.app.base import AppBase

from .descriptor import ServiceDescriptor
from .exceptions import ServiceDependencyError
from .logger import logger

if TYPE_CHECKING:
    from scriptable.service.base import ServiceType, Spec


class AppCommonServices(AppBase):
    @final
    def add_service_dependency(
        self,
        name: str,
        spec: "Spec",
    ) -> "ServiceType":
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

    @final
    def get_service_dependency(self, name: str) -> "ServiceType":
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

    def _init_service_descriptors(self):
        for name, value in self.__class__.__dict__.items():
            if not isinstance(value, ServiceDescriptor):
                continue

            descriptor = cast(ServiceDescriptor, value)
            if descriptor.spec is None:
                logger.error(f"No spec found for dependency '{name}'")
                raise ServiceDependencyError(f"No spec found for dependency '{name}'")

            service = self.add_service_dependency(name, descriptor.spec)

            setattr(self, name, service)
