# loomistd/rpyc/__init__.py
"""
LoomistD RPyC Package - Dedicated RPyC implementation for Loomi remote resources.

This package provides RPyC-specific services for remote resource connectivity.
It embraces RPyC's features and wraps them in Loomi's service architecture.

Components:
- Connection subpackage: TCP and Unix socket connections (for clients)
- Factory: Resource factory exposed directly via RPyC
- Server: Thin RPyC server services (TCP and Unix variants)
- Client: RPyC client services (TCP and Unix variants)

Usage:
    # Server side
    server = rpyc_server_tcp("0.0.0.0", 18812)
    server.start()

    # Client side
    client = rpyc_client_tcp("server.com", 18812)
    remote_resource = client.get_remote_resource(spec)
"""

from __future__ import annotations

from loomi.spec import Spec

# Core components
from ._conn.tcp_conn import RPyCTCPConnection, RPyCTCPConnectionSpec
from ._conn.unix_conn import RPyCUnixConnection, RPyCUnixConnectionSpec
from .client import RPyCClient, RPyCTCPClientSpec, RPyCUnixClientSpec
from .factory import ResourceFactory
from .server import (
    BaseRPyCServer,
    RPyCTCPServer,
    RPyCTCPServerSpec,
    RPyCUnixServer,
    RPyCUnixServerSpec,
)

__all__ = [
    # Connection types (used by clients)
    "RPyCTCPConnection",
    "RPyCUnixConnection",
    "RPyCTCPConnectionSpec",
    "RPyCUnixConnectionSpec",
    # Core services
    "ResourceFactory",
    "BaseRPyCServer",
    "RPyCTCPServer",
    "RPyCUnixServer",
    "RPyCClient",
    # Specifications
    "RPyCTCPServerSpec",
    "RPyCUnixServerSpec",
    "RPyCTCPClientSpec",
    "RPyCUnixClientSpec",
    # Convenience functions
    "rpyc_server_tcp",
    "rpyc_server_unix",
    "rpyc_client_tcp",
    "rpyc_client_unix",
]


# Server convenience functions
def rpyc_server_tcp(
    bind_address: str = "localhost",
    bind_port: int = 18812,
    auto_register: bool = False,
    **config: dict,
) -> RPyCTCPServer:
    """
    Create a TCP-based RPyC server service.

    Args:
        bind_address: Address to bind server to
        bind_port: Port to bind server to
        auto_register: Whether to auto-register with RPyC registry

    Returns:
        Configured RPyCTCPServer

    Example:
        server = rpyc_server_tcp("0.0.0.0", 18812)
        with server:
            server.start()  # Runs in foreground
    """
    spec = RPyCTCPServerSpec(
        bind_address=bind_address,
        bind_port=bind_port,
        auto_register=auto_register,
        config=config,
    )
    return RPyCTCPServer(spec)


def rpyc_server_unix(
    socket_path: str = "/tmp/loomi_rpyc.sock", auto_register: bool = False, **config: dict
) -> RPyCUnixServer:
    """
    Create a Unix socket-based RPyC server service.

    Args:
        socket_path: Path for Unix socket
        auto_register: Whether to auto-register with RPyC registry

    Returns:
        Configured RPyCUnixServer

    Example:
        server = rpyc_server_unix("/tmp/myapp.sock")
        with server:
            server.start()  # Runs in foreground
    """
    spec = RPyCUnixServerSpec(
        socket_path=socket_path,
        auto_register=auto_register,
        config=config,
    )
    return RPyCUnixServer(spec)


# Client convenience functions
def rpyc_client_tcp(
    host: str = "localhost", port: int = 18812, auto_connect: bool = True, **config: dict
) -> RPyCClient:
    """
    Create a TCP-based RPyC client service.

    Args:
        host: Server hostname
        port: Server port
        auto_connect: Whether to connect automatically
        **config: Additional RPyC configuration

    Returns:
        Configured RPyC client with TCP connection

    Example:
        client = rpyc_client_tcp("server.com", 18812)
        remote_resource = client.get_remote_resource(spec)
    """
    # Create TCP connection spec
    connection_spec = RPyCTCPConnectionSpec(
        factory=RPyCTCPConnection,
        host=host,
        port=port,
        config=config,
    )

    # Create client spec
    client_spec = RPyCTCPClientSpec(
        connection=connection_spec,
    )

    return RPyCClient(client_spec)


def rpyc_client_unix(
    socket_path: str = "/tmp/loomi_rpyc.sock", auto_connect: bool = True, **config: dict
) -> RPyCClient:
    """
    Create a Unix socket-based RPyC client service.

    Args:
        socket_path: Path to Unix socket
        auto_connect: Whether to connect automatically
        **config: Additional RPyC configuration

    Returns:
        Configured RPyC client with Unix socket connection

    Example:
        client = rpyc_client_unix("/tmp/myapp.sock")
        remote_resource = client.get_remote_resource(spec)
    """
    # Create Unix connection spec
    connection_spec = RPyCUnixConnectionSpec(
        factory=RPyCUnixConnection,
        socket_path=socket_path,
        config=config,
    )

    # Create client spec
    client_spec = RPyCUnixClientSpec(
        connection=connection_spec,
    )

    return RPyCClient(client_spec)
