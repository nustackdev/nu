from __future__ import annotations

from typing import TYPE_CHECKING, cast

from loomi.descriptors.attach import AttachDescriptor, is_attach_descriptor

from .base import AsyncServiceABC, ServiceABC, SyncServiceABC
from .exceptions import DependencyError
from .logger import logger

if TYPE_CHECKING:
    from loomi.spec import Spec

    from .service import Service


class CommonServiceComposer(ServiceABC):
    def _add_dependency(
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
        try:
            return self._dep_manager.resolve_dependency(self, name, spec)
        except DependencyError as e:
            logger.error(f"Failed to add dependency '{name}' to '{self.readable_name}': {str(e)}")
            raise

    def _get_dependency(self, name: str) -> "Service":
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

    def _get_dependencies(self) -> dict[str, "Service"]:
        """
        Get all service dependencies.

        Returns:
            Dict mapping dependency names to services
        """
        return self._dep_manager.get_dependencies(self)

    def _get_dependents(self) -> set["Service"]:
        """
        Get all dependent services.

        Returns:
            Set of services depending on this one
        """
        return self._dep_manager.get_dependents(self)

    def _detach_dependent(self, dependent: ServiceABC) -> None:
        """
        Remove a dependent service.

        Args:
            dependent: Dependent service to remove
        """
        self._dep_manager.detach_relationship(dependent, self)

    def _initialize_attach_descriptors(self):
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

            attach_service = self._add_dependency(f"{name}", attach_spec)

            setattr(self, name, attach_service)


class AsyncServiceComposer(CommonServiceComposer, AsyncServiceABC):
    """
    Service mixin combining dependency injection and component architecture.

    Features:
    - Declarative dependency specification via Attach

    Example:
        class DataService(AsyncService):
            storage = Attach(Storage)
    """

    pass


class SyncServiceComposer(CommonServiceComposer, SyncServiceABC):
    """
    Service mixin combining dependency injection and component architecture.

    Features:
    - Declarative dependency specification via Attach

    Example:
        class DataService(SyncService):
            storage = Attach(Storage)
    """

    pass
