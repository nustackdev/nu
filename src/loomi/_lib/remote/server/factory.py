"""
Remote resource factory for creating resources on the server side.

This module provides a simple factory that creates resource instances
from serialized specs and returns them for RPyC to proxy automatically.
"""

from typing import Any, Dict

from ..utils import deserialize_spec

__all__ = [
    "ResourceFactory",
]


class ResourceFactory:
    """
    Factory for creating resources from specs.

    This class is designed to be exposed via RPyC to allow remote
    clients to create resource instances on the server.
    """

    def __init__(self):
        self.created_resources: Dict[str, Any] = {}
        self._resource_counter = 0

    def create_resource(self, spec_data: bytes) -> Any:
        """
        Create a resource instance from serialized spec.

        Args:
            spec_data: Serialized spec data

        Returns:
            Resource instance (will be auto-proxied by RPyC)
        """
        # Deserialize spec
        spec = deserialize_spec(spec_data)

        # Create resource instance
        resource = spec.factory(spec)

        # Track the resource
        resource_id = f"resource_{self._resource_counter}"
        self.created_resources[resource_id] = resource
        self._resource_counter += 1

        return resource

    def create_named_resource(self, name: str, spec_data: bytes) -> Any:
        """
        Create a named resource instance.

        Args:
            name: Name to store resource under
            spec_data: Serialized spec data

        Returns:
            Resource instance
        """
        spec = deserialize_spec(spec_data)
        resource = spec.factory(spec)
        self.created_resources[name] = resource
        return resource

    def get_resource(self, name: str) -> Any:
        """
        Get a previously created named resource.

        Args:
            name: Resource name

        Returns:
            Resource instance or None if not found
        """
        return self.created_resources.get(name)

    def list_resources(self) -> list[str]:
        """
        List all created resource names.

        Returns:
            List of resource names
        """
        return list(self.created_resources.keys())

    def shutdown_all(self) -> None:
        """
        Shutdown all created resources.
        """
        for resource in self.created_resources.values():
            if hasattr(resource, "shutdown"):
                try:
                    resource.shutdown()
                except Exception as e:
                    print(f"Error shutting down resource: {e}")

        self.created_resources.clear()
