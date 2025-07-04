# loomistd/rpyc/unix.py
"""
Unix socket-based RPyC connection implementation.

This module provides Unix domain socket RPyC connection using RPyC's
built-in Unix socket support. It implements the BaseRPyCConnection
interface for local IPC-based remote resource connections.
"""

from __future__ import annotations

from pathlib import Path

import attrs
import rpyc
from rpyc.core import Connection as RPyCConnection
from rpyc.core.stream import SocketStream

from loomi.service import SyncService

from ..exceptions import RPyCConnectionError
from .base_conn import BaseRPyCConnection, BaseRPyCConnectionSpec
from .logger import logger

__all__ = [
    "RPyCUnixConnection",
    "RPyCUnixConnectionSpec",
]


class RPyCUnixConnection(BaseRPyCConnection, SyncService):
    """
    Unix socket-based RPyC connection implementation.

    This class provides RPyC connectivity over Unix domain sockets using
    RPyC's built-in Unix socket connection capabilities. It inherits all
    common functionality from BaseRPyCConnection and implements Unix
    socket-specific connection creation and validation.

    Attributes:
        socket_path (str): Path to Unix socket file

    Example:
        unix_conn = RPyCUnixConnection(Spec(
            factory=RPyCUnixConnection,
            socket_path="/tmp/myapp.sock"
        ))

        with unix_conn:
            remote_resource = unix_conn.get_remote_resource(resource_spec)
    """

    spec: RPyCUnixConnectionSpec

    def _create_connection_impl(self) -> RPyCConnection:
        """
        Create Unix socket connection to RPyC server.

        Validates socket path exists and uses RPyC's built-in Unix socket
        connection with configured path.

        Returns:
            RPyC connection instance

        Raises:
            RPyCConnectionError: If socket path invalid or connection fails
        """
        if not self.spec.socket_path:
            raise RPyCConnectionError("socket_path is required for Unix socket connection")

        # Check if socket exists
        socket_file = Path(self.spec.socket_path)
        if not socket_file.exists():
            raise RPyCConnectionError(f"Unix socket {self.spec.socket_path} does not exist")

        logger.debug(f"Connecting to RPyC server at {self.spec.socket_path}")

        stream = SocketStream.unix_connect(str(socket_file.resolve()))

        conn = rpyc.connect_stream(
            stream,
            config=self._get_rpyc_config(),
        )

        return conn

    @property
    def endpoint(self) -> str:
        """Get string representation of the Unix socket endpoint."""
        return self.spec.socket_path


@attrs.define(frozen=True, slots=True, kw_only=True)
class RPyCUnixConnectionSpec(BaseRPyCConnectionSpec):
    factory: type = RPyCUnixConnection
    name: str = "rpyc_unix_connection"
    socket_path: str = "/tmp/loomi_rpyc.sock"
