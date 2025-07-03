from __future__ import annotations

from typing import TYPE_CHECKING, cast

from ..descriptors import ResourceDescriptor
from ..exceptions import DependencyError
from .base import AsyncResourceABC, ResourceABC, SyncResourceABC
from .logger import logger

if TYPE_CHECKING:
    from ..spec import Spec
    from .resource import Resource


class CommonResourceComposer(ResourceABC):
    def _add_dependency(
        self,
        name: str,
        spec: "Spec",
    ) -> "Resource":
        """
        Add resource dependency.

        Args:
            name: Dependency name
            spec: Spec of the resource

        Raises:
            DependencyError: If dependency invalid or creates cycle
        """
        try:
            return self._dep_manager.resolve_dependency(self, name, spec)
        except DependencyError as e:
            logger.error(f"Failed to add dependency '{name}' to '{self.readable_name}': {str(e)}")
            raise

    def _get_dependency(self, name: str) -> "Resource":
        """
        Get named dependency if it exists.

        Args:
            name: Dependency name to retrieve

        Returns:
            Dependency resource
        """
        deps = self._dep_manager.get_dependencies(self)
        if name not in deps.keys():
            raise DependencyError(
                f"Dependency '{name}' not found for resource '{self.readable_name}'"
            )

        return deps[name]

    def _get_dependencies(self) -> dict[str, "Resource"]:
        """
        Get all resource dependencies.

        Returns:
            Dict mapping dependency names to resources
        """
        return self._dep_manager.get_dependencies(self)

    def _get_dependents(self) -> set["Resource"]:
        """
        Get all dependent resources.

        Returns:
            Set of resources depending on this one
        """
        return self._dep_manager.get_dependents(self)

    def _detach_dependent(self, dependent: ResourceABC) -> None:
        """
        Remove a dependent resource.

        Args:
            dependent: Dependent resource to remove
        """
        self._dep_manager.detach_relationship(dependent, self)

    def _initialize_attach_descriptors(self):
        for name, value in self.__class__.__dict__.items():
            if not isinstance(value, ResourceDescriptor):
                continue

            attach = cast(ResourceDescriptor, value)

            # Get resource spec by priority
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

            attach_resource = self._add_dependency(f"{name}", attach_spec)

            setattr(self, name, attach_resource)


class AsyncResourceComposer(CommonResourceComposer, AsyncResourceABC):
    """
    Resource mixin combining dependency injection and component architecture.

    Features:
    - Declarative dependency specification via UseResource

    Example:
        class DataResource(AsyncResource):
            storage = UseResource(Storage)
    """

    pass


class SyncResourceComposer(CommonResourceComposer, SyncResourceABC):
    """
    Resource mixin combining dependency injection and component architecture.

    Features:
    - Declarative dependency specification via UseResource

    Example:
        class DataResource(SyncResource):
            storage = UseResource(Storage)
    """

    pass
