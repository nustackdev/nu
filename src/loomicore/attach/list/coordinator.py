"""
List coordinator for AttachMany pattern.

This module provides the ListCoordinator that manages homogeneous resources
created from a list of specs, maintaining order and providing indexed access.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Generic, TypeVar

from loomicore.attach.exceptions import AttachError

if TYPE_CHECKING:
    from loomicore.resource import Resource

__all__ = [
    "ListCoordinator",
]

ResourceType = TypeVar("ResourceType", bound="Resource")


class ListCoordinator(Generic[ResourceType]):
    """
    Coordinator for managing an ordered list of homogeneous resources.

    This coordinator manages multiple resources created from a list of specs,
    maintaining their order and providing indexed access. It handles the
    lifecycle of all managed resources and provides a simple interface
    for accessing individual resources by index.

    Features:
        - Ordered list of resources based on spec order
        - Indexed access via get(index) method
        - Lifecycle management for all resources
        - Homogeneous resource type (all same factory)

    Examples:
        ```python
        class MyService(SyncResource):
            workers = AttachList([
                WorkerSpec(name="worker-1"),
                WorkerSpec(name="worker-2"),
                WorkerSpec(name="worker-3"),
            ])

        # Usage
        service = MyService(spec)
        worker_0 = service.workers.get(0)  # First worker
        worker_1 = service.workers.get(1)  # Second worker
        all_workers = service.workers.resources  # All workers
        count = len(service.workers)  # Number of workers
        ```
    """

    def __init__(self, resources: list["ResourceType"]) -> None:
        """
        Initialize coordinator with list of resources.

        Args:
            resources: Ordered list of resources to manage

        Raises:
            AttachError: If resources list is empty
        """
        if not resources:
            raise AttachError("AttachList requires at least one resource")

        self._resources = list(resources)

    def get(self, index: int) -> "ResourceType":
        """
        Get resource at specified index.

        Args:
            index: Index of resource to retrieve (0-based)

        Returns:
            Resource at the specified index

        Raises:
            IndexError: If index is out of range

        Examples:
            ```python
            worker = coordinator.get(0)  # First resource
            worker = coordinator.get(-1)  # Last resource
            ```
        """
        try:
            return self._resources[index]
        except IndexError:
            raise IndexError(
                f"Resource index {index} out of range. "
                f"Coordinator has {len(self._resources)} resources (indices 0-{len(self._resources) - 1})"
            )

    @property
    def resources(self) -> list["Resource"]:
        """
        Get all managed resources as a list.

        Returns:
            Read-only view of all resources in order

        Notes:
            - Returns a copy to prevent external modification
            - Resources are in the same order as the original specs
        """
        return list(self._resources)  # Return copy for safety

    def __len__(self) -> int:
        """
        Get number of managed resources.

        Returns:
            Number of resources in the coordinator

        Examples:
            ```python
            count = len(coordinator)
            for i in range(len(coordinator)):
                resource = coordinator.get(i)
            ```
        """
        return len(self._resources)

    def __iter__(self):
        """
        Iterate over all managed resources.

        Returns:
            Iterator over resources in order

        Examples:
            ```python
            for resource in coordinator:
                # Process each resource
                resource.do_something()
            ```
        """
        return iter(self._resources)

    def __getitem__(self, index: int) -> "ResourceType":
        """
        Get resource using bracket notation.

        Args:
            index: Index of resource to retrieve

        Returns:
            Resource at the specified index

        Examples:
            ```python
            worker = coordinator[0]  # First resource
            worker = coordinator[-1]  # Last resource
            ```
        """
        return self.get(index)

    def __repr__(self) -> str:
        """
        String representation for debugging.

        Returns:
            String showing coordinator type and resource count
        """
        resource_names = [getattr(r, "readable_name", str(r)) for r in self._resources]
        return f"<ListCoordinator: {len(self._resources)} resources: {resource_names}>"
