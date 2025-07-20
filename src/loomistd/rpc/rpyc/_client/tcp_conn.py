"""
TCP-based RPyC connection implementation.

This module provides TCP socket RPyC connection using RPyC's built-in
TCP support. It implements the BaseRPyCConnection interface for
network-based remote resource connections.
"""

from __future__ import annotations

import attrs
import rpyc
from rpyc.core import Connection as RPyCConnection

from loomi import SyncService

from .base_conn import BaseRPyCConnection, BaseRPyCConnectionSpec
from .logger import logger

__all__ = [
    "RPyCTCPConnection",
    "RPyCTCPConnectionSpec",
]


class RPyCTCPConnection(BaseRPyCConnection, SyncService):
    """
    TCP-based RPyC connection implementation.

    This class provides RPyC connectivity over TCP/IP networks using
    RPyC's built-in TCP connection capabilities. It inherits all common
    functionality from BaseRPyCConnection and implements TCP-specific
    connection creation.

    Attributes:
        host (str): Server hostname or IP address
        port (int): Server port number

    Example:
        tcp_conn = RPyCTCPConnection(Spec(
            factory=RPyCTCPConnection,
            host="server.example.com",
            port=18812
        ))

        with tcp_conn:
            remote_resource = tcp_conn.get_remote_resource(resource_spec)
    """

    spec: RPyCTCPConnectionSpec

    def _create_connection_impl(self) -> RPyCConnection:
        """
        Create TCP connection to RPyC server.

        Uses RPyC's built-in TCP connection with configured host and port.

        Returns:
            RPyC connection instance

        Raises:
            Exception: If TCP connection fails
        """
        logger.debug(f"Connecting to RPyC server at {self.spec.host}:{self.spec.port}")

        connection = rpyc.connect(self.spec.host, self.spec.port, config=self._get_rpyc_config())

        return connection

    @property
    def endpoint(self) -> str:
        """Get string representation of the TCP endpoint."""
        return f"{self.spec.host}:{self.spec.port}"


@attrs.define(frozen=True, slots=True, kw_only=True)
class RPyCTCPConnectionSpec(BaseRPyCConnectionSpec):
    factory: type = RPyCTCPConnection
    name: str = "rpyc_tcp_connection"
    host: str = "localhost"
    port: int = 18812
