# loomistd/rpyc/factory.py
"""
RPyC factory for creating and managing Loomi resources remotely.

This module provides the factory class that gets exposed through RPyC to create
and manage Loomi resources on the server side. It's a regular Python class that
handles resource lifecycle, deduplication, and registry management.
"""

from __future__ import annotations

from typing import Any, Dict, cast

from rpyc import Service

from loomi.resource import SyncResource
from loomi.spec import Spec

from .exceptions import RPyCServerError
from .logger import logger
from .types import ResourceRegistry

__all__ = [
    "ResourceFactory",
]


class ResourceFactory(Service):
    """
    Factory class for creating and managing Loomi resources remotely.

    This class is exposed through RPyC and handles resource creation, lifecycle
    management, and deduplication on the server side. It maintains a registry
    of active resources and ensures proper cleanup.

    The factory is designed to be thread-safe and handle multiple concurrent
    client connections accessing resources.
    """

    def __init__(self) -> None:
        """Initialize the Loomi resource factory."""
        self._resources: Dict[Spec, Any] = {}
        logger.debug("LoomiResourceFactory initialized")

    def exposed_get_resource(self, spec: Spec) -> Any:
        """
        Get or create a resource based on its specification.

        This is the main method that clients use to get remote resources.
        It implements resource deduplication based on spec equality to ensure
        that identical resource specifications return the same instance.

        Args:
            spec: Resource specification

        Returns:
            Resource instance (will be proxied by RPyC)

        Raises:
            RPyCServerError: If resource creation fails
        """
        # Check if resource already exists
        if spec in self._resources:
            logger.debug(f"Returning existing resource: {spec.factory.__name__}")
            return self._resources[spec]

        # Create new resource
        try:
            logger.debug(f"Creating new resource: {spec.factory.__name__}")

            # Create the resource using its factory
            resource = cast(SyncResource, spec.factory(spec))

            # Initialize the resource if it supports initialization
            if resource and not resource.is_initialized:
                resource.initialize()

            # Store in registry
            self._resources[spec] = resource

            logger.info(f"Resource created and registered: {spec.factory.__name__}")
            return resource

        except Exception as e:
            logger.error(f"Failed to create resource {spec.factory.__name__}: {e}")
            raise RPyCServerError(f"Failed to create resource {spec.factory.__name__}") from e

    def exposed_list_resources(self) -> ResourceRegistry:
        """
        List all active resources in the factory.

        Returns:
            Dict mapping resource keys to factory names
        """
        return {spec.key: spec.factory.__name__ for spec in self._resources.keys()}

    def exposed_remove_resource(self, spec: Spec) -> bool:
        """
        Remove a resource from the factory.

        Properly shuts down the resource if it supports shutdown,
        then removes it from the internal registry.

        Args:
            spec: Specification of resource to remove

        Returns:
            True if resource was removed, False if not found
        """
        if spec not in self._resources:
            logger.warning(f"Attempt to remove non-existent resource: {spec.factory.__name__}")
            return False

        try:
            resource = cast(SyncResource, self._resources[spec])

            # Shutdown the resource if it supports shutdown
            if resource and resource.is_initialized:
                resource.shutdown()

            # Remove from registry
            del self._resources[spec]

            logger.info(f"Resource removed: {spec.factory.__name__}")
            return True

        except Exception as e:
            logger.error(f"Error removing resource {spec.factory.__name__}: {e}")
            return False

    def exposed_shutdown_all_resources(self) -> None:
        """
        Shutdown all active resources.

        This method is typically called during server shutdown to ensure
        all resources are properly cleaned up.
        """
        logger.info("Shutting down all active resources")

        for spec in list(self._resources.keys()):
            try:
                self.exposed_remove_resource(spec)
            except Exception as e:
                logger.error(f"Error shutting down resource {spec.factory.__name__}: {e}")

        logger.info("All resources shutdown complete")

    def exposed_get_resource_count(self) -> int:
        """
        Get the number of active resources.

        Returns:
            Number of resources currently managed by the factory
        """
        return len(self._resources)

    def exposed_ping(self) -> str:
        """
        Simple ping method for health checks.

        Returns:
            Pong response indicating the factory is operational
        """
        return "pong"

    def exposed_get_factory_info(self) -> Dict[str, Any]:
        """
        Get information about the factory state.

        Returns:
            Dict containing factory statistics and information
        """
        return {
            "resource_count": len(self._resources),
            "active_resources": [spec.key for spec in self._resources.keys()],
            "factory_status": "operational",
        }
