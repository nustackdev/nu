from typing import TYPE_CHECKING, cast, final

from scriptable.service.base import ServiceBase

from .attach import AttachDescriptor, is_attach_descriptor
from .exceptions import DependencyError
from .logger import logger

if TYPE_CHECKING:
    from scriptable.service.base import ServiceType, Spec


class ServiceCommonComposer(ServiceBase):
    @final
    def add_dependency(
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
        try:
            return self._dep_manager.resolve_dependency(self, name, spec)
        except DependencyError as e:
            logger.error(f"Failed to add dependency '{name}' to '{self.readable_name}': {str(e)}")
            raise

    @final
    def get_dependency(self, name: str) -> "ServiceType":
        """
        Get named dependency if it exists.

        Args:
            name: Dependency name to retrieve

        Returns:
            Dependency service
        """
        deps = self._dep_manager.get_dependencies(self)
        if name not in deps.keys():
            raise DependencyError(
                f"Dependency '{name}' not found for service '{self.readable_name}'"
            )

        return deps[name]

    @final
    def get_dependencies(self) -> dict[str, "ServiceType"]:
        """
        Get all service dependencies.

        Returns:
            Dict mapping dependency names to services
        """
        return self._dep_manager.get_dependencies(self)

    @final
    def get_dependents(self) -> set["ServiceType"]:
        """
        Get all dependent services.

        Returns:
            Set of services depending on this one
        """
        return self._dep_manager.get_dependents(self)

    @final
    def detach_dependent(self, dependent: "ServiceType") -> None:
        """
        Remove a dependent service.

        Args:
            dependent: Dependent service to remove
        """
        self._dep_manager.detach_relationship(dependent, self)

    def _init_attach(self):
        for name, value in self.__class__.__dict__.items():
            if not is_attach_descriptor(value):
                continue

            attach = cast(AttachDescriptor, value)

            # Get service spec by priority
            attach_spec = None

            # 1. Spec from parent class
            if hasattr(self.spec, name):
                attach_spec = getattr(self.spec, name)

            # 2. Spec from descriptor
            elif attach.spec is not None:
                attach_spec = attach.spec

            # 3. Raise error if no spec found
            else:
                logger.error(f"No spec found for dependency '{name}'")
                raise DependencyError(f"No spec found for dependency '{name}'")

            attach_service = self.add_dependency(f"{name}", attach_spec)

            setattr(self, name, attach_service)
