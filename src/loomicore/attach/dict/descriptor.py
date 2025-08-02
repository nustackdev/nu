"""
Dict resource attachment pattern.

This module provides the DictDescriptor for multiple homogeneous resource
attachment via the AttachDict() function. It creates a DictCoordinator that
manages a key-value collection of resources based on a dict of specs.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from loomicore.common.descriptor import StorageStrategy, ValidationStrategy

from ..base_descriptor import BaseResourceDescriptor
from ..exceptions import AttachError
from .coordinator import DictCoordinator

if TYPE_CHECKING:
    from loomicore.resource import Resource
    from loomicore.runtime.dependency_manager import DependencyManager
    from loomicore.spec import Spec

__all__ = [
    "DictDescriptor",
    "AttachDict",
]


class DictDescriptor(BaseResourceDescriptor):
    """
    Descriptor for multiple homogeneous resource attachment via AttachDict().

    This descriptor creates a DictCoordinator that manages multiple resources
    created from a dict of specs. It handles resource creation, dependency
    tracking, and provides named access to individual resources.

    Priority for spec resolution:
    1. Specs from parent resource's spec (if attribute exists and is dict)
    2. Specs from descriptor itself (provided to AttachDict())
    3. Error if no specs found

    Examples:
        ```python
        class MyService(SyncResource):
            # Specs from descriptor
            workers = AttachDict({
                "primary": WorkerSpec(name="primary-worker"),
                "secondary": WorkerSpec(name="secondary-worker"),
            })

            # Specs from parent resource spec (MyServiceSpec.databases)
            databases = AttachDict()
        ```
    """

    def __init__(
        self, specs: dict[str, "Spec"] | None = None, /, *, alias: str | None = None
    ) -> None:
        """
        Initialize dict descriptor.

        Args:
            specs: Dict of resource specifications for the dependencies
            alias: Optional alias name for the dependency group
        """
        super().__init__(
            storage=StorageStrategy.WEAKREF,
            validation_strategy=ValidationStrategy.STRICT,
            allow_none=True,
        )
        self.specs: dict[str, "Spec"] = specs or {}
        self.alias = alias

    def _validate_type(self, value: Any) -> bool:
        """Validate that value is a DictCoordinator (or None)."""
        return value is None or isinstance(value, DictCoordinator)

    def _get_default(self) -> None:
        """Default value is None until resolved."""
        return None

    def resolve(
        self, parent: "Resource", name: str, dependency_manager: "DependencyManager"
    ) -> DictCoordinator:
        """
        Resolve multiple resources using priority-based spec resolution.

        This method implements the core resolution logic for multiple resource
        attachment. It uses a priority system to determine the specs, then
        creates resources for each spec and returns a DictCoordinator.

        Args:
            parent: Resource containing this descriptor
            name: Attribute name of this descriptor
            dependency_manager: Dependency manager for resource operations

        Returns:
            DictCoordinator managing the resolved resources

        Raises:
            AttachError: If spec resolution or resource creation fails
        """
        # Get specs using priority system
        specs = self._get_specs(parent, name)

        if not specs:
            raise AttachError(
                f"No specs found for AttachDict descriptor '{name}' in '{parent.readable_name}'. "
                "Either provide specs to AttachDict() or add a dict of specs to the parent resource spec."
            )

        # Create resources for each spec
        resources: dict[str, "Resource"] = {}
        for key, spec in specs.items():
            try:
                resource = dependency_manager.resolve_dependency(parent, f"{name}[{key}]", spec)
                resources[key] = resource
            except Exception as e:
                raise AttachError(
                    f"Failed to resolve resource with key '{key}' for AttachDict '{name}' with spec '{spec}' in '{parent.readable_name}': {str(e)}"
                ) from e

        # Create and return coordinator
        try:
            coordinator = DictCoordinator(resources)
            return coordinator
        except Exception as e:
            raise AttachError(
                f"Failed to create DictCoordinator for AttachDict '{name}' "
                f"in '{parent.readable_name}': {str(e)}"
            ) from e

    def _get_specs(self, parent: "Resource", name: str) -> dict[str, "Spec"]:
        """
        Get specs using priority: parent spec > descriptor specs.

        Args:
            parent: Parent resource
            name: Descriptor attribute name

        Returns:
            Dict of resolved specs

        Raises:
            AttachError: If no specs found or invalid spec type
        """
        # Priority 1: ResourceSpecs from parent resource's spec
        if hasattr(parent.spec, name):
            parent_specs = getattr(parent.spec, name)
            if isinstance(parent_specs, dict):
                return parent_specs
            else:
                raise AttachError(
                    f"AttachDict descriptor '{name}' in '{parent.readable_name}' "
                    f"expects a dict of specs from parent, but got {type(parent_specs).__name__}"
                )

        # Priority 2: ResourceSpecs from descriptor
        if self.specs:
            return self.specs

        # No specs found - error
        raise AttachError(
            f"No specs found for AttachDict descriptor '{name}' in '{parent.readable_name}'. "
            "Either add a dict of specs to the parent resource spec or use AttachDict({{specs}}) "
            "to provide specifications directly."
        )


def AttachDict(specs: dict[str, "Spec"] | None = None, /, *, alias: str | None = None) -> Any:
    """
    Create a dict resource attachment descriptor.

    This function creates a descriptor that will resolve to a DictCoordinator
    managing multiple homogeneous resources. The resource specifications can be
    provided directly or inherited from the parent resource's spec.

    Args:
        specs: Optional dict of resource specifications. If not provided, the specs
               will be resolved from the parent resource's spec using the
               descriptor's attribute name.
        alias: Optional alias name for the dependency group

    Returns:
        DictDescriptor that will resolve to a DictCoordinator

    Examples:
        ```python
        class WorkerService(SyncResource):
            # Specs provided directly
            workers = AttachDict({
                "primary": WorkerSpec(name="primary-worker", port=8001),
                "secondary": WorkerSpec(name="secondary-worker", port=8002),
                "backup": WorkerSpec(name="backup-worker", port=8003),
            })

            # Specs from parent resource spec (WorkerServiceSpec.databases)
            databases = AttachDict()

        # Usage with parent spec
        service = WorkerService(WorkerServiceSpec(
            databases={
                "primary": DatabaseSpec(name="primary", host="db1.example.com"),
                "replica": DatabaseSpec(name="replica", host="db2.example.com"),
            }
        ))

        # Access resources
        primary_worker = service.workers.get("primary")
        all_workers = service.workers.resources
        worker_count = len(service.workers)

        # Iterate over resources
        for key, worker in service.workers.items():
            print(f"Worker {key}: {worker.readable_name}")

        # Check if key exists
        if "backup" in service.workers:
            backup = service.workers["backup"]
        ```

    Notes:
        - Type annotation DictCoordinator is for static type checking
        - Actual runtime type is DictDescriptor
        - Resolution happens during resource composition
        - Supports priority-based spec resolution
        - All resources must have the same factory type for homogeneity
    """
    return DictDescriptor(specs, alias=alias)
