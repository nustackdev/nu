"""RPyC factory for creating and managing EveryFlow resources remotely.

This module provides the factory class that gets exposed through RPyC to create
and manage EveryFlow resources on the server side. It's a regular Python class that
handles resource lifecycle, deduplication, and registry management.
"""

from __future__ import annotations

import pickle
from logging import getLogger
from typing import Any, cast

from everylink import Spec, SyncResource
from rpyc import Service

from .exceptions import RPyCServerError
from .types import ResourceRegistry


logger = getLogger(__name__)


__all__ = [
    "ResourceFactory",
]


class ResourceFactory(Service):
    """Factory class for creating and managing EveryFlow resources remotely.

    This class is exposed through RPyC and handles resource creation, lifecycle
    management, and deduplication on the server side. It maintains a registry
    of active resources and ensures proper cleanup.

    The factory is designed to be thread-safe and handle multiple concurrent
    client connections accessing resources.
    """

    def __init__(self) -> None:
        """Initialize the EveryFlow resource factory."""
        self._resources: dict[Spec, Any] = {}
        logger.debug("EveryFlowResourceFactory initialized")

    def exposed_get_resource(self, spec_data: bytes) -> Any:
        """Get or create a resource based on its specification.

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
        spec: Spec = self._deserialize_spec(spec_data)

        # Check if resource already exists
        if spec in self._resources:
            logger.debug(f"Returning existing resource: {spec}")
            return self._resources[spec]

        # Create new resource
        try:
            logger.debug(f"Creating new resource: {spec}")

            # Create the resource using its factory
            resource = cast(
                "SyncResource",
                spec.factory(spec),  # type: ignore
            )  # FIXME: Proper instance creation via runtime factory

            # Initialize the resource if it supports initialization
            if resource and not resource.is_initialized:
                resource.initialize()

            # Store in registry
            self._resources[spec] = resource

            logger.info(f"Resource created and registered: {spec}")
            return resource

        except Exception as e:
            logger.error(f"Failed to create resource {spec}: {e}")
            raise RPyCServerError(f"Failed to create resource {spec}") from e

    def exposed_list_resources(self) -> ResourceRegistry:
        """List all active resources in the factory.

        Returns:
            Dict mapping resource keys to factory names
        """
        return {spec.key: spec.key for spec in self._resources.keys()}

    def exposed_remove_resource(self, spec_data: bytes) -> bool:
        """Remove a resource from the factory.

        Properly shuts down the resource if it supports shutdown,
        then removes it from the internal registry.

        Args:
            spec: Specification of resource to remove

        Returns:
            True if resource was removed, False if not found
        """
        spec: Spec = self._deserialize_spec(spec_data)
        return self.remove_resource(spec)

    def remove_resource(self, spec: Spec) -> bool:
        """Remove a resource from the factory registry.
        This method is called when a resource is removed, either through
        exposed_remove_resource or during shutdown.

        Args:
            spec: Specification of the resource to remove

        Returns:
            True if the resource was successfully removed, False if it was not found
        """
        if spec not in self._resources:
            logger.warning(f"Attempt to remove non-existent resource: {spec}")
            return False

        try:
            resource = cast("SyncResource", self._resources[spec])

            # Shutdown the resource if it supports shutdown
            if resource and resource.is_initialized:
                resource.shutdown()

            # Remove from registry
            del self._resources[spec]

            logger.info(f"Resource removed: {spec}")
            return True

        except Exception as e:
            logger.error(f"Error removing resource {spec}: {e}")
            return False

    def exposed_shutdown_all_resources(self) -> None:
        """Shutdown all active resources.

        This method is typically called during server shutdown to ensure
        all resources are properly cleaned up.
        """
        logger.info("Shutting down all active resources")

        for spec in list(self._resources.keys()):
            try:
                self.remove_resource(spec)
            except Exception as e:
                logger.error(f"Error shutting down resource {spec}: {e}")

        logger.info("All resources shutdown complete")

    def exposed_get_resource_count(self) -> int:
        """Get the number of active resources.

        Returns:
            Number of resources currently managed by the factory
        """
        return len(self._resources)

    def exposed_ping(self) -> str:
        """Simple ping method for health checks.

        Returns:
            Pong response indicating the factory is operational
        """
        return "pong"

    def exposed_get_factory_info(self) -> dict[str, Any]:
        """Get information about the factory state.

        Returns:
            Dict containing factory statistics and information
        """
        return {
            "resource_count": len(self._resources),
            "active_resources": [spec.key for spec in self._resources.keys()],
            "factory_status": "operational",
        }

    @staticmethod
    def _deserialize_spec(serialized_spec: bytes) -> Spec:
        """Deserialize a resource spec from its serialized form.

        Args:
            serialized_spec: Serialized representation of the spec

        Returns:
            Deserialized Spec object
        """
        # Assuming Spec has a from_dict method for deserialization
        return pickle.loads(serialized_spec)
