"""
AttachFleet - Fleet Coordinator for Distributed Execution

This module implements an AttachFleet that extends AttachMany
with execution coordination capabilities for distributed resource fleets.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypeVar

from loomicore.attach import AttachError, BaseResourceDescriptor
from loomicore.common.descriptor import StorageStrategy, ValidationStrategy

from .coordinator import FleetCoordinator

if TYPE_CHECKING:
    from loomicore.resource import Resource
    from loomicore.runtime import DependencyManager
    from loomicore.spec import Spec

__all__ = [
    "AttachFleet",
    "FleetDescriptor",
]

ResourceType = TypeVar("ResourceType", bound="Resource")


class FleetDescriptor(BaseResourceDescriptor):
    """
    Descriptor for fleet resource attachment via AttachFleet().

    Similar to ManyListDescriptor but creates FleetCoordinator instead of ListCoordinator.
    """

    def __init__(
        self, specs: tuple["Spec", ...] | None = None, /, *, alias: str | None = None
    ) -> None:
        """
        Initialize fleet descriptor.

        Args:
            specs: List of resource specifications for the fleet
            alias: Optional alias name for the fleet
        """
        super().__init__(
            storage=StorageStrategy.WEAKREF,
            validation_strategy=ValidationStrategy.STRICT,
            allow_none=True,
        )
        self.specs: tuple["Spec", ...] = specs or tuple()
        self.alias = alias

    def _validate_type(self, value: Any) -> bool:
        """Validate that value is a FleetCoordinator (or None)."""
        return value is None or isinstance(value, FleetCoordinator)

    def _get_default(self) -> None:
        """Default value is None until resolved."""
        return None

    def resolve(
        self, parent: "Resource", name: str, dependency_manager: "DependencyManager"
    ) -> FleetCoordinator:
        """
        Resolve fleet resources using priority-based spec resolution.

        Args:
            parent: Resource containing this descriptor
            name: Attribute name of this descriptor
            dependency_manager: Dependency manager for resource operations

        Returns:
            FleetCoordinator managing the resolved resources

        Raises:
            AttachError: If spec resolution or resource creation fails
        """
        # Get specs using priority system (same as AttachMany)
        specs = self._get_specs(parent, name)

        if not specs:
            raise AttachError(
                f"No specs found for AttachFleet descriptor '{name}' in '{parent.readable_name}'. "
                "Either provide specs to AttachFleet() or add a list of specs to the parent resource spec."
            )

        # Create resources for each spec
        resources: list["Resource"] = []
        for i, spec in enumerate(specs):
            try:
                resource = dependency_manager.resolve_dependency(parent, f"{name}[{i}]", spec)
                resources.append(resource)
            except Exception as e:
                raise AttachError(
                    f"Failed to resolve resource at index {i} for AttachFleet '{name}' with spec '{spec}' in '{parent.readable_name}': {str(e)}"
                ) from e

        # Create and return fleet coordinator
        try:
            coordinator = FleetCoordinator(resources)
            return coordinator
        except Exception as e:
            raise AttachError(
                f"Failed to create FleetCoordinator for AttachFleet '{name}' "
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
                    f"AttachFleet descriptor '{name}' in '{parent.readable_name}' "
                    f"expects a tuple of specs from parent, but got {type(parent_specs).__name__}"
                )

        # Priority 2: ResourceSpecs from descriptor
        if self.specs:
            return self.specs

        # No specs found - error
        raise AttachError(
            f"No specs found for AttachFleet descriptor '{name}' in '{parent.readable_name}'. "
            "Either add a list of specs to the parent resource spec or use AttachFleet([specs]) "
            "to provide specifications directly."
        )


def AttachFleet(specs: tuple["Spec", ...] | None = None, /, *, alias: str | None = None) -> Any:
    """
    Create a fleet resource attachment descriptor.

    This function creates a descriptor that will resolve to a FleetCoordinator
    managing multiple resources with execution coordination capabilities.

    Args:
        specs: Optional list of resource specifications. If not provided, the specs
               will be resolved from the parent resource's spec using the
               descriptor's attribute name.
        alias: Optional alias name for the fleet

    Returns:
        FleetDescriptor that will resolve to a FleetCoordinator

    Examples:
        ```python
        class Worker(SyncResource):
            def process(self, data: str) -> str:
                return f"processed: {data}"

        class Service(SyncResource):
            # Specs provided directly
            fleet = AttachFleet([
                WorkerSpec(name="worker-1"),
                WorkerSpec(name="worker-2"),
                WorkerSpec(name="worker-3"),
            ])

            # Specs from parent resource spec (ServiceSpec.workers)
            workers = AttachFleet()

            def process_batch(self, items: list[str]) -> list[str]:
                # Distribute variable number of jobs across workers
                jobs = [(item,) for item in items]  # Convert to job format
                futures = self.fleet.distribute(Worker.process, jobs)
                return [f.result() for f in futures]

            def process_exact_mapping(self, items: list[str]) -> list[str]:
                # Execute on all workers with different data (1:1 mapping)
                futures = self.fleet.map(Worker.process, items)
                return [f.result() for f in futures]

            def broadcast_config(self, config: dict) -> list[bool]:
                # Execute same operation on all workers
                futures = self.fleet.broadcast(Worker.configure, config)
                return [f.result() for f in futures]

        # Usage
        service = Service(ServiceSpec(
            workers=[
                WorkerSpec(name="worker-1"),
                WorkerSpec(name="worker-2"),
            ]
        ))

        # Process variable number of jobs (3 workers, 7 jobs)
        results = service.process_batch(["data1", "data2", "data3", "data4", "data5", "data6", "data7"])

        # Process with exact 1:1 mapping (must match worker count)
        results = service.process_exact_mapping(["data1", "data2", "data3"])

        # Configure all workers
        success = service.broadcast_config({"env": "prod"})
        ```

    Notes:
        - FleetCoordinator extends ListCoordinator with execution methods
        - Supports map(), submit(), broadcast(), and cancel_all() operations
        - Built on ThreadPoolExecutor for PoC (can be extended for distributed)
        - Handles both bound and unbound methods
        - Provides proper cleanup and cancellation support
    """
    return FleetDescriptor(specs, alias=alias)
