"""
Remote resource client for connecting to resource servers.

This module provides simple client functionality for connecting to
remote resource servers and creating resource instances.
"""

from typing import Any, Optional, Type, TypeVar

import rpyc
from rpyc.core.stream import SocketStream

from loomi._lib.resource.spec import Spec

from ..utils import serialize_spec
from ..wrapper import wrap_remote_resource

__all__ = [
    "RemoteResourceClient",
    "create_remote_resource",
]

ResourceT = TypeVar("ResourceT")


class RemoteResourceClient:
    """
    Client for connecting to remote resource servers.
    """

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        socket_path: Optional[str] = None,
        **rpyc_config,
    ):
        """
        Initialize client connection parameters.

        Args:
            host: Server hostname (for TCP)
            port: Server port (for TCP)
            socket_path: Unix socket path (takes precedence over host/port)
            **rpyc_config: Additional RPyC configuration
        """
        self.host = host
        self.port = port
        self.socket_path = socket_path
        self.rpyc_config = {"allow_all_attrs": True, "sync_request_timeout": 30, **rpyc_config}
        self._connection = None

    def connect(self):
        """Establish connection to the server."""
        if self._connection:
            return self._connection

        if self.socket_path:
            stream = SocketStream.unix_connect(self.socket_path)
            self._connection = rpyc.connect_stream(stream, config=self.rpyc_config)
        elif self.host and self.port:
            self._connection = rpyc.connect(self.host, self.port, config=self.rpyc_config)
        else:
            raise ValueError("Must provide either socket_path or host/port")

        return self._connection

    def disconnect(self):
        """Close connection to the server."""
        if self._connection:
            self._connection.close()
            self._connection = None

    def create_resource(self, spec: Spec, resource_type: Optional[Type[ResourceT]] = None) -> Any:
        """
        Create a remote resource instance.

        Args:
            spec: Resource specification
            resource_type: Optional type for wrapper (enables autocomplete)

        Returns:
            Remote resource proxy (optionally wrapped for autocomplete)
        """
        conn = self.connect()
        spec_data = serialize_spec(spec)

        # Create remote resource
        remote_proxy = conn.root.create_resource(spec_data)

        # Optionally wrap for autocomplete
        if resource_type:
            return wrap_remote_resource(resource_type, remote_proxy)

        return remote_proxy

    def create_named_resource(
        self, name: str, spec: Spec, resource_type: Optional[Type[ResourceT]] = None
    ) -> Any:
        """
        Create a named remote resource.

        Args:
            name: Name to store resource under
            spec: Resource specification
            resource_type: Optional type for wrapper

        Returns:
            Remote resource proxy
        """
        conn = self.connect()
        spec_data = serialize_spec(spec)

        remote_proxy = conn.root.create_named_resource(name, spec_data)

        if resource_type:
            return wrap_remote_resource(resource_type, remote_proxy)

        return remote_proxy

    def get_resource(self, name: str, resource_type: Optional[Type[ResourceT]] = None) -> Any:
        """
        Get a previously created named resource.

        Args:
            name: Resource name
            resource_type: Optional type for wrapper

        Returns:
            Remote resource proxy or None
        """
        conn = self.connect()
        remote_proxy = conn.root.get_resource(name)

        if remote_proxy and resource_type:
            return wrap_remote_resource(resource_type, remote_proxy)

        return remote_proxy

    def list_resources(self) -> list[str]:
        """List all resources on the server."""
        conn = self.connect()
        return conn.root.list_resources()

    def shutdown_all_resources(self):
        """Shutdown all resources on the server."""
        conn = self.connect()
        return conn.root.shutdown_all()

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()


def create_remote_resource(
    spec: Spec,
    resource_type: Optional[Type[ResourceT]] = None,
    host: Optional[str] = None,
    port: Optional[int] = None,
    socket_path: Optional[str] = None,
    **rpyc_config,
) -> Any:
    """
    Convenience function to create a remote resource.

    Args:
        spec: Resource specification
        resource_type: Optional type for wrapper
        host: Server hostname
        port: Server port
        socket_path: Unix socket path
        **rpyc_config: RPyC configuration

    Returns:
        Remote resource proxy
    """
    client = RemoteResourceClient(host=host, port=port, socket_path=socket_path, **rpyc_config)

    with client:
        return client.create_resource(spec, resource_type)
