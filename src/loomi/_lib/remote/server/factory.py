"""
Remote resource factory for creating resources on the server side.

This module provides a simple factory that creates resource instances
from serialized specs and returns them for RPyC to proxy automatically.
"""

from typing import Any

from ..spec import deserialize_spec

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
        pass

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

        print(f"Creating resource ddddddd with spec: {spec}")

        # Create resource instance
        resource = spec.factory(spec)

        return resource

    def list_resources(self) -> list[str]:
        """
        List all created resource names.

        Returns:
            List of resource names
        """
        raise NotImplementedError()

    def shutdown_all(self) -> None:
        """
        Shutdown all created resources.
        """
        raise NotImplementedError()
