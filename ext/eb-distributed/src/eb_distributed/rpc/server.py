"""InvisiblesServer - composables Resource wrapping an Invisibles RPC server.

Starts a NetKit server that serves a root service object via Invisibles protocol.
Supports TCP and Unix socket transports.
"""

from __future__ import annotations

import threading
from typing import Any

import attrs
from composables import Resource, ResourceSpec
from invisibles import InvisiblesConnection
from invisibles.codec.pickle_codec import PickleCodec
from invisibles.config import AttributeAccessConfig, ConnectionConfig
from invisibles.core.protocol import Protocol
from netkit import SyncConnection, SyncServer
from netkit.executors import SimpleExecutor
from netkit.framing import LengthPrefixedFraming
from netkit.transports import TCPListener, UnixSocketListener


__all__ = [
    "InvisiblesServer",
    "InvisiblesServerSpec",
]


class InvisiblesServer(Resource):
    """Composables Resource that runs an Invisibles RPC server.

    Serves a root service object over TCP or Unix socket.
    Set root_service on the instance before initialization (or via the worker).
    """

    spec: InvisiblesServerSpec
    root_service: Any

    def __init__(
        self, spec: InvisiblesServerSpec | None = None, /, root_service: object = None
    ) -> None:
        """Initialize with spec and optional root service."""
        super().__init__(spec)
        self.root_service = root_service

    async def setup(self) -> None:
        """Start the RPC server in a background thread."""
        if self.root_service is None:
            raise ValueError("root_service must be set before initialization")

        config = ConnectionConfig(attrs=AttributeAccessConfig(allow_all_attrs=True))
        codec = PickleCodec()

        if self.spec.transport == "unix":

            def listener_factory() -> UnixSocketListener:
                return UnixSocketListener()
        else:

            def listener_factory() -> TCPListener:
                return TCPListener()

        self._server = SyncServer(
            listener_factory=listener_factory,
            framing_factory=lambda t: LengthPrefixedFraming(t, max_frame_size=1024 * 1024),
            executor=SimpleExecutor(),
        )

        root = self.root_service

        def handle_connection(netkit_conn: SyncConnection) -> None:
            protocol = Protocol(codec, config, root)
            conn = InvisiblesConnection(netkit_conn, protocol)
            while netkit_conn.is_connected():
                conn._serve_one(timeout=1.0)

        self._server.set_handler(handle_connection)

        # Start in background thread
        if self.spec.transport == "unix":

            def target() -> None:
                self._server.start(self.spec.address)
        else:
            host, port = self._parse_tcp_address(self.spec.address)

            def target() -> None:
                self._server.start(host, port)

        self._thread = threading.Thread(target=target, daemon=True, name="invisibles-server")
        self._thread.start()

    async def cleanup(self) -> None:
        """Stop the RPC server."""
        if hasattr(self, "_server"):
            self._server.stop(wait=False)

    @staticmethod
    def _parse_tcp_address(address: str) -> tuple[str, int]:
        if ":" in address:
            host, port_str = address.rsplit(":", 1)
            return host, int(port_str)
        return "127.0.0.1", int(address)


@attrs.define(frozen=True, slots=True, kw_only=True)
class InvisiblesServerSpec(ResourceSpec):
    """Spec for InvisiblesServer - configures transport and address."""

    factory: type = InvisiblesServer
    name: str = "invisibles-server"

    transport: str = "tcp"  # "tcp" or "unix"
    address: str = "127.0.0.1:18812"  # "host:port" for TCP, path for Unix
