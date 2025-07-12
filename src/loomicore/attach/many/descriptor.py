"""
Many list resource attachment pattern.

This module provides the ManyListDescriptor for multiple homogeneous resource
attachment via the AttachMany() function. It creates a ListCoordinator that
manages an ordered collection of resources based on a list of specs.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from loomicore.common.descriptor import StorageStrategy, ValidationStrategy

from ..base_descriptor import BaseResourceDescriptor
from ..exceptions import AttachError
from .coordinator import ListCoordinator

if TYPE_CHECKING:
    from loomicore.resource import Resource
    from loomicore.runtime.dependency_manager import DependencyManager
    from loomicore.spec import Spec

__all__ = [
    "ManyListDescriptor",
    "AttachMany",
]


class ManyListDescriptor(BaseResourceDescriptor):
    """
    Descriptor for multiple homogeneous resource attachment via AttachMany().

    This descriptor creates a ListCoordinator that manages multiple resources
    created from a list of specs. It handles resource creation, dependency
    tracking, and provides indexed access to individual resources.

    Priority for spec resolution:
    1. Specs from parent resource's spec (if attribute exists and is list)
    2. Specs from descriptor itself (provided to AttachMany())
    3. Error if no specs found

    Examples:
        ```python
        class MyService(SyncResource):
            # Specs from descriptor
            workers = AttachMany([
                WorkerSpec(name="worker-1"),
                WorkerSpec(name="worker-2"),
            ])

            # Specs from parent resource spec (MyServiceSpec.databases)
            databases = AttachMany()
        ```
    """

    def __init__(
        self, specs: tuple["Spec", ...] | None = None, /, *, alias: str | None = None
    ) -> None:
        """
        Initialize many list descriptor.

        Args:
            specs: List of resource specifications for the dependencies
            alias: Optional alias name for the dependency group
        """
        super().__init__(
            storage=StorageStrategy.WEAKREF,
            validation_strategy=ValidationStrategy.STRICT,
            allow_none=True,
        )
        self.specs: tuple["Spec", ...] = specs or tuple()
        self.alias = alias

    def _validate_type(self, value: Any) -> bool:
        """Validate that value is a ListCoordinator (or None)."""
        return value is None or isinstance(value, ListCoordinator)

    def _get_default(self) -> None:
        """Default value is None until resolved."""
        return None

    def resolve(
        self, parent: "Resource", name: str, dependency_manager: "DependencyManager"
    ) -> ListCoordinator:
        """
        Resolve multiple resources using priority-based spec resolution.

        This method implements the core resolution logic for multiple resource
        attachment. It uses a priority system to determine the specs, then
        creates resources for each spec and returns a ListCoordinator.

        Args:
            parent: Resource containing this descriptor
            name: Attribute name of this descriptor
            dependency_manager: Dependency manager for resource operations

        Returns:
            ListCoordinator managing the resolved resources

        Raises:
            AttachError: If spec resolution or resource creation fails
        """
        # Get specs using priority system
        specs = self._get_specs(parent, name)

        if not specs:
            raise AttachError(
                f"No specs found for AttachMany descriptor '{name}' in '{parent.readable_name}'. "
                "Either provide specs to AttachMany() or add a list of specs to the parent resource spec."
            )

        # Create resources for each spec
        resources: list["Resource"] = []
        for i, spec in enumerate(specs):
            try:
                resource = dependency_manager.resolve_dependency(parent, f"{name}[{i}]", spec)
                resources.append(resource)
            except Exception as e:
                raise AttachError(
                    f"Failed to resolve resource at index {i} for AttachMany '{name}' with spec '{spec}' in '{parent.readable_name}': {str(e)}"
                ) from e

        # Create and return coordinator
        try:
            coordinator = ListCoordinator(resources)
            return coordinator
        except Exception as e:
            raise AttachError(
                f"Failed to create ListCoordinator for AttachMany '{name}' "
                f"in '{parent.readable_name}': {str(e)}"
            ) from e

    def _get_specs(self, parent: "Resource", name: str) -> tuple["Spec", ...]:
        """
        Get specs using priority: parent spec > descriptor specs.

        Args:
            parent: Parent resource
            name: Descriptor attribute name

        Returns:
            List of resolved specs

        Raises:
            AttachError: If no specs found or invalid spec type
        """
        # Priority 1: ResourceSpecs from parent resource's spec
        if hasattr(parent.spec, name):
            parent_specs = getattr(parent.spec, name)
            if isinstance(parent_specs, tuple):
                return parent_specs
            else:
                raise AttachError(
                    f"AttachMany descriptor '{name}' in '{parent.readable_name}' "
                    f"expects a tuple of specs from parent, but got {type(parent_specs).__name__}"
                )

        # Priority 2: ResourceSpecs from descriptor
        if self.specs:
            return self.specs

        # No specs found - error
        raise AttachError(
            f"No specs found for AttachMany descriptor '{name}' in '{parent.readable_name}'. "
            "Either add a list of specs to the parent resource spec or use AttachMany([specs]) "
            "to provide specifications directly."
        )


def AttachMany(specs: tuple["Spec", ...] | None = None, /, *, alias: str | None = None) -> Any:
    """
    Create a multiple resource attachment descriptor.

    This function creates a descriptor that will resolve to a ListCoordinator
    managing multiple homogeneous resources. The resource specifications can be
    provided directly or inherited from the parent resource's spec.

    Args:
        specs: Optional list of resource specifications. If not provided, the specs
               will be resolved from the parent resource's spec using the
               descriptor's attribute name.
        alias: Optional alias name for the dependency group

    Returns:
        ManyListDescriptor that will resolve to a ListCoordinator

    Examples:
        ```python
        class WorkerService(SyncResource):
            # Specs provided directly
            workers = AttachMany([
                WorkerSpec(name="worker-1", port=8001),
                WorkerSpec(name="worker-2", port=8002),
                WorkerSpec(name="worker-3", port=8003),
            ])

            # Specs from parent resource spec (WorkerServiceSpec.databases)
            databases = AttachMany()

        # Usage with parent spec
        service = WorkerService(WorkerServiceSpec(
            databases=[
                DatabaseSpec(name="primary", host="db1.example.com"),
                DatabaseSpec(name="replica", host="db2.example.com"),
            ]
        ))

        # Access resources
        primary_worker = service.workers.get(0)
        all_workers = service.workers.resources
        worker_count = len(service.workers)

        # Iterate over resources
        for i, worker in enumerate(service.workers):
            print(f"Worker {i}: {worker.readable_name}")
        ```

    Notes:
        - Type annotation ListCoordinator is for static type checking
        - Actual runtime type is ManyListDescriptor
        - Resolution happens during resource composition
        - Supports priority-based spec resolution
        - All resources must have the same factory type for homogeneity
    """
    return ManyListDescriptor(specs, alias=alias)
