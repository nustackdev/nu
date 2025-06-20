"""
Simple RPyC server for exposing resource factory.

This module provides a minimal server that exposes ResourceFactory
via RPyC, allowing remote clients to create and use resources.
"""

from typing import Optional

import rpyc
from rpyc.utils.server import ThreadedServer

from .factory import ResourceFactory

__all__ = [
    "RemoteResourceServer",
]


class RemoteResourceService(rpyc.Service):
    """
    RPyC service that exposes resource factory.
    """

    def __init__(self):
        self.factory = ResourceFactory()

    def exposed_create_resource(self, spec_data: bytes):
        """Create a resource from serialized spec."""
        return self.factory.create_resource(spec_data)

    def exposed_create_named_resource(self, name: str, spec_data: bytes):
        """Create a named resource."""
        return self.factory.create_named_resource(name, spec_data)

    def exposed_get_resource(self, name: str):
        """Get a named resource."""
        return self.factory.get_resource(name)

    def exposed_list_resources(self):
        """List all resource names."""
        return self.factory.list_resources()

    def exposed_shutdown_all(self):
        """Shutdown all resources."""
        return self.factory.shutdown_all()


class RemoteResourceServer:
    """
    Server for exposing resources remotely via RPyC.
    """

    def __init__(self):
        self._server = None

    def start(
        self,
        host: str = "localhost",
        port: int = 18861,
        socket_path: Optional[str] = None,
        **rpyc_config,
    ) -> None:
        """
        Start the server.

        Args:
            host: Host to bind to (ignored if socket_path provided)
            port: Port to bind to (ignored if socket_path provided)
            socket_path: Unix socket path (takes precedence)
            **rpyc_config: Additional RPyC configuration
        """
        # Default RPyC config
        default_config = {
            "allow_all_attrs": True,
            "sync_request_timeout": 30,
        }
        default_config.update(rpyc_config)

        if socket_path:
            self._server = ThreadedServer(
                RemoteResourceService, socket_path=socket_path, protocol_config=default_config
            )
            print(f"Starting remote resource server on socket: {socket_path}")
        else:
            self._server = ThreadedServer(
                RemoteResourceService, hostname=host, port=port, protocol_config=default_config
            )
            print(f"Starting remote resource server on {host}:{port}")

        try:
            self._server.start()
        except KeyboardInterrupt:
            print("\nShutting down server...")
        finally:
            self.stop()

    def stop(self) -> None:
        """Stop the server."""
        if self._server:
            self._server.close()
            self._server = None

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
