"""
Proxy Specs - Remote communication utilities

Provides utility functions for creating common proxy and RPC configurations
with sensible defaults for distributed system communication.
"""

from __future__ import annotations

from typing import Any, Tuple

from loomistd.rpc.rpyc import (
    RPyCTCPClientSpec,
    RPyCTCPConnectionSpec,
    RPyCTCPServerSpec,
    RPyCUnixClientSpec,
    RPyCUnixConnectionSpec,
    RPyCUnixServerSpec,
)

__all__ = [
    "get_rpyc_specs",
]


def get_rpyc_specs(
    rpc_type: str,
    address: str,
    *,
    client_name: str = "rpyc_client",
    server_name: str = "rpyc_server",
    **config,
) -> Tuple[Any, Any]:
    """
    Create matching RPyC client and server specs for distributed communication.

    Returns both client and server specs configured for the same communication
    endpoint, ensuring they can connect to each other.

    Args:
        rpc_type: Communication type ("unix" for Unix sockets, "tcp" for TCP)
        address: Address for communication:
                - For "unix": socket file path (e.g., "/tmp/service.sock")
                - For "tcp": host:port (e.g., "localhost:8080")
        client_name: Client service name
        server_name: Server service name
        **config: Additional configuration parameters

    Returns:
        Tuple of (client_spec, server_spec) ready for use

    Examples:
        ```python
        # Unix socket communication
        client, server = get_rpyc_specs("unix", "/tmp/state.sock")

        # TCP communication
        client, server = get_rpyc_specs("tcp", "localhost:8080")

        # Named specs for identification
        client, server = get_rpyc_specs(
            "unix",
            "/tmp/worker_1.sock",
            client_name="worker_1_client",
            server_name="worker_1_server"
        )

        # Use with SpecBuilder
        proxy = SpecBuilder(state_spec).as_proxy(client).build()
        launcher = get_multiprocessing_launcher_spec(host=server)
        ```
    """
    if rpc_type == "unix":
        # Unix socket communication
        connection = RPyCUnixConnectionSpec(socket_path=address, **config)

        client_spec = RPyCUnixClientSpec(
            name=client_name,
            connection=connection,
        )

        server_spec = RPyCUnixServerSpec(
            name=server_name,
            socket_path=address,
        )

        return client_spec, server_spec

    elif rpc_type == "tcp":
        # TCP communication
        host, port = address.split(":")
        port = int(port)

        client_spec = RPyCTCPClientSpec(
            name=client_name,
            connection=RPyCTCPConnectionSpec(host=host, port=port, **config),
        )

        server_spec = RPyCTCPServerSpec(
            name=server_name,
            bind_address=host,
            bind_port=port,
        )

        return client_spec, server_spec
    else:
        raise ValueError(f"Unknown RPC type: {rpc_type}. Supported: 'unix', 'tcp'")
