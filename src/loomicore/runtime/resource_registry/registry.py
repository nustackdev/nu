"""
Resource Registry - Manages resource instances and deduplication.

This module provides the ResourceRegistry which handles resource instance tracking
and deduplication.
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
    - Maintain unique resource instances based on resource spec
    - Provide instance lookup for deduplication
    - Track resource existence (not state - that's in LifecycleManager)

    This registry acts as the source of truth for resource existence and
    provides the deduplication mechanism.
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
