"""
Resource Registry - Manages resource instances and deduplication.

This module provides the ResourceRegistry which handles resource instance tracking
and deduplication. State management has been moved to LifecycleManager for better
separation of concerns.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .exceptions import RegistryError, RegistryKeyError
from .logger import logger

if TYPE_CHECKING:
    from loomicore.resource import Resource
    from loomicore.spec import Spec

__all__ = [
    "ResourceRegistry",
]


class ResourceRegistry:
    """
    Registry managing resource instances and deduplication.

    Primary responsibilities:
    - Maintain unique resource instances based on factory and spec
    - Provide fast instance lookup for deduplication
    - Track resource existence (not state - that's in LifecycleManager)

    This registry acts as the source of truth for resource existence and
    provides the deduplication mechanism. State management is handled by
    the LifecycleManager.

    Updated Design:
        - Focused solely on instance tracking and deduplication
        - No state management (moved to LifecycleManager)
        - Simplified interface and responsibilities
        - Better separation of concerns
    """

    def __init__(self) -> None:
        """
        Initialize the resource registry.

        Sets up internal storage for resource instance tracking.
        """
        # Map of resource key to resource instance
        self._instances: dict[str, "Resource"] = {}

        logger.debug("Initialized resource registry")

    def get_resource(self, spec: "Spec") -> "Resource | None":
        """
        Retrieve existing resource instance for given spec.

        This is the primary deduplication mechanism - same spec
        should always return the same instance if it exists.

        Args:
            spec: Resource specification to look up

        Returns:
            Existing resource instance or None if not found

        Notes:
            - Core deduplication functionality
            - Fast O(1) lookup by spec key
            - Returns None if resource doesn't exist (not an error)
        """
        key = spec.key
        resource = self._instances.get(key, None)

        if resource is not None:
            logger.debug(f"Found existing resource for spec key: {key}")
            return resource

        logger.debug(f"No existing resource found for spec key: {key}")
        return None

    def add_resource(self, resource: "Resource") -> None:
        """
        Register new resource instance for tracking and deduplication.

        Args:
            resource: Resource instance to register

        Raises:
            RegistryError: If resource with same key already exists

        Notes:
            - Enables deduplication for future lookups
            - Key collision indicates programming error
            - Idempotent operations should use get_resource() first
        """
        key = resource.key

        if key in self._instances:
            raise RegistryError(
                f"Resource already exists with key: '{key}' ({resource.readable_name})"
            )

        self._instances[key] = resource
        logger.debug(
            f"Registered resource for deduplication: '{resource.readable_name}' (key: {key})"
        )

    def remove_resource(self, resource: "Resource") -> None:
        """
        Remove resource from registry.

        Args:
            resource: Resource to remove

        Raises:
            RegistryKeyError: If resource not found in registry

        Notes:
            - Removes from deduplication tracking
            - Should be called during resource cleanup
            - No state validation (handled by LifecycleManager)
        """
        key = resource.key

        if key not in self._instances:
            raise RegistryKeyError(
                f"Resource not found in registry: '{resource.readable_name}' (key: {key})"
            )

        del self._instances[key]
        logger.debug(f"Removed resource from registry: '{resource.readable_name}' (key: {key})")

    def has_resource(self, spec: "Spec") -> bool:
        """
        Check if resource exists for given spec.

        Args:
            spec: Resource specification to check

        Returns:
            True if resource exists in registry

        Notes:
            - Convenience method for existence checking
            - Does not return the resource instance
            - Fast O(1) lookup
        """
        return spec.key in self._instances

    def has_resource_by_key(self, key: str) -> bool:
        """
        Check if resource exists for given key.

        Args:
            key: Resource key to check

        Returns:
            True if resource exists in registry

        Notes:
            - Direct key lookup without spec creation
            - Useful for internal runtime operations
        """
        return key in self._instances

    def get_all_resources(self) -> list["Resource"]:
        """
        Get all resources currently in the registry.

        Returns:
            List of all resource instances

        Notes:
            - Useful for debugging and monitoring
            - Returns snapshot at time of call
            - Order not guaranteed
        """
        return [resource for resource in self._instances.values()]

    def get_resource_count(self) -> int:
        """
        Get total number of resources in registry.

        Returns:
            Number of resource instances currently tracked

        Notes:
            - Fast O(1) operation
            - Useful for monitoring and debugging
        """
        return len(self._instances)

    def clear_all_resources(self) -> None:
        """
        Remove all resources from registry.

        Notes:
            - Used for cleanup during shutdown
            - Does not call resource lifecycle methods
            - Should only be used when all resources are properly shut down
        """
        count = len(self._instances)
        self._instances.clear()
        logger.debug(f"Cleared all {count} resources from registry")

    def get_resources_by_factory(self, factory_type: type) -> list["Resource"]:
        """
        Get all resources of a specific factory type.

        Args:
            factory_type: Resource class/factory to filter by

        Returns:
            List of resources matching the factory type

        Notes:
            - Useful for debugging and monitoring
            - O(n) operation - scans all resources
            - Returns snapshot at time of call
        """
        matching_resources = []
        for resource in self._instances.values():
            # Check if resource is instance of factory_type
            if isinstance(resource, factory_type):
                matching_resources.append(resource)

        logger.debug(f"Found {len(matching_resources)} resources of type {factory_type.__name__}")
        return matching_resources

    # === Private Implementation ===

    def __len__(self) -> int:
        """
        Get number of resources in registry.

        Returns:
            Number of resource instances
        """
        return len(self._instances)

    def __contains__(self, spec: "Spec") -> bool:
        """
        Check if resource exists for spec using 'in' operator.

        Args:
            spec: Resource specification to check

        Returns:
            True if resource exists

        Example:
            >>> if my_spec in registry:
            ...     resource = registry.get_resource(my_spec)
        """
        return self.has_resource(spec)

    def __repr__(self) -> str:
        """
        String representation of registry for debugging.

        Returns:
            String showing registry contents summary
        """
        resource_summary = []
        for resource in self._instances.values():
            resource_summary.append(f"  - {resource.readable_name} (key: {resource.key})")

        summary = "\n".join(resource_summary) if resource_summary else "  (empty)"

        return f"<ResourceRegistry: {len(self._instances)} resources\n" f"{summary}\n" ">"
