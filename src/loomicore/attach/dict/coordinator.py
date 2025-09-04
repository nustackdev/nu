"""
Dict coordinator for AttachDict pattern.

This module provides the DictCoordinator that manages homogeneous resources
created from a dict of specs, maintaining key-value mapping and providing named access.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Generic, TypeVar

from loomicore.attach.exceptions import AttachError

if TYPE_CHECKING:
    from loomicore.resource import Resource

__all__ = [
    "DictCoordinator",
]

ResourceType = TypeVar("ResourceType", bound="Resource")


class DictCoordinator(Generic[ResourceType]):
    """
    Coordinator for managing a key-value mapping of homogeneous resources.

    This coordinator manages multiple resources created from a dict of specs,
    maintaining their key-value mapping and providing named access. It handles the
    lifecycle of all managed resources and provides a simple interface
    for accessing individual resources by key.

    Features:
        - Key-value mapping of resources based on spec keys
        - Named access via get(key) method
        - Lifecycle management for all resources
        - Homogeneous resource type (all same factory)

    Examples:
        ```python
        class MyService(SyncResource):
            workers = AttachDict({
                "primary": WorkerSpec(name="primary-worker"),
                "secondary": WorkerSpec(name="secondary-worker"),
                "backup": WorkerSpec(name="backup-worker"),
            })

        # Usage
        service = MyService(spec)
        primary = service.workers.get("primary")  # Primary worker
        secondary = service.workers.get("secondary")  # Secondary worker
        all_workers = service.workers.resources  # All workers as dict
        count = len(service.workers)  # Number of workers
        ```
    """

    def __init__(self, resources: dict[str, "ResourceType"]) -> None:
        """
        Initialize coordinator with dict of resources.

        Args:
            resources: Key-value mapping of resources to manage

        Raises:
            AttachError: If resources dict is empty
        """
        if not resources:
            raise AttachError("AttachDict requires at least one resource")

        self._resources = dict(resources)

    def get(self, key: str) -> "ResourceType":
        """
        Get resource with specified key.

        Args:
            key: Key of resource to retrieve

        Returns:
            Resource with the specified key

        Raises:
            KeyError: If key is not found

        Examples:
            ```python
            worker = coordinator.get("primary")  # Primary resource
            worker = coordinator.get("backup")   # Backup resource
            ```
        """
        try:
            return self._resources[key]
        except KeyError:
            available_keys = list(self._resources.keys())
            raise KeyError(f"Resource key '{key}' not found. " f"Available keys: {available_keys}")

    @property
    def resources(self) -> dict[str, "Resource"]:
        """
        Get all managed resources as a dict.

        Returns:
            Read-only view of all resources as key-value mapping

        Notes:
            - Returns a copy to prevent external modification
            - Resources maintain their original key mapping
        """
        return dict(self._resources)  # Return copy for safety

    def keys(self) -> list[str]:
        """
        Get all resource keys.

        Returns:
            List of all resource keys

        Examples:
            ```python
            keys = coordinator.keys()
            for key in keys:
                resource = coordinator.get(key)
            ```
        """
        return list(self._resources.keys())

    def __len__(self) -> int:
        """
        Get number of managed resources.

        Returns:
            Number of resources in the coordinator

        Examples:
            ```python
            count = len(coordinator)
            ```
        """
        return len(self._resources)

    def __iter__(self):
        """
        Iterate over all resource keys.

        Returns:
            Iterator over resource keys

        Examples:
            ```python
            for key in coordinator:
                resource = coordinator.get(key)
                # Process each resource
                resource.do_something()
            ```
        """
        return iter(self._resources.keys())

    def __getitem__(self, key: str) -> "ResourceType":
        """
        Get resource using bracket notation.

        Args:
            key: Key of resource to retrieve

        Returns:
            Resource with the specified key

        Examples:
            ```python
            worker = coordinator["primary"]  # Primary resource
            worker = coordinator["backup"]   # Backup resource
            ```
        """
        return self.get(key)

    def __contains__(self, key: str) -> bool:
        """
        Check if key exists in coordinator.

        Args:
            key: Key to check

        Returns:
            True if key exists, False otherwise

        Examples:
            ```python
            if "primary" in coordinator:
                worker = coordinator["primary"]
            ```
        """
        return key in self._resources

    def items(self):
        """
        Iterate over key-value pairs.

        Returns:
            Iterator over (key, resource) pairs

        Examples:
            ```python
            for key, resource in coordinator.items():
                print(f"{key}: {resource.readable_name}")
            ```
        """
        return self._resources.items()

    def values(self):
        """
        Iterate over all managed resources.

        Returns:
            Iterator over resources

        Examples:
            ```python
            for resource in coordinator.values():
                # Process each resource
                resource.do_something()
            ```
        """
        return self._resources.values()

    def __repr__(self) -> str:
        """
        String representation for debugging.

        Returns:
            String showing coordinator type and resource count with keys
        """
        resource_info = {k: getattr(v, "readable_name", str(v)) for k, v in self._resources.items()}
        return f"<DictCoordinator: {len(self._resources)} resources: {resource_info}>"
