"""InvisiblesServer - composables Resource wrapping an Invisibles RPC server.

Starts a NetKit server that serves a root service object via Invisibles protocol.
Supports TCP and Unix socket transports. Root service is resolved via Attach.
"""

from __future__ import annotations

import threading

import attrs
from composables import Attach, Resource, ResourceSpec
from invisibles import InvisiblesConnection
from invisibles.codec.pickle_codec import PickleCodec
from invisibles.config import AttributeAccessConfig, ConnectionConfig
from invisibles.core.protocol import Protocol
from netkit import SyncConnection, SyncServer
from netkit.executors import SimpleExecutor
from netkit.framing import LengthPrefixedFraming
from netkit.transports import TCPListener, UnixSocketListener

from .factory import ResourceFactorySpec


__all__ = [
    "InvisiblesServer",
    "InvisiblesServerSpec",
]


def _framing_factory(transport: object) -> LengthPrefixedFraming:
    return LengthPrefixedFraming(transport, max_frame_size=1024 * 1024)


class InvisiblesServer(Resource):
    """Composables Resource that runs an Invisibles RPC server.

    Serves a root service (resolved via Attach) over TCP or Unix socket.
    Default root service is a ResourceFactory.
    """

    spec: InvisiblesServerSpec
    root_service = Attach()

    async def setup(self) -> None:
        """Start the RPC server in a background thread."""
        config = ConnectionConfig(attrs=AttributeAccessConfig(allow_all_attrs=True))
        codec = PickleCodec()
        root = self.root_service

        if self.spec.transport == "unix":
            listener_factory = UnixSocketListener
        else:
            listener_factory = TCPListener

        self._server = SyncServer(
            listener_factory=listener_factory,
            framing_factory=_framing_factory,
            executor=SimpleExecutor(),
        )

        def handle_connection(netkit_conn: SyncConnection) -> None:
            protocol = Protocol(codec, config, root)
            conn = InvisiblesConnection(netkit_conn, protocol)
            while netkit_conn.is_connected():
                conn._serve_one(timeout=1.0)

        self._server.set_handler(handle_connection)

        if self.spec.transport == "unix":
            address = self.spec.address
            server = self._server

            def target() -> None:
                server.start(address)
        else:
            host, port = self._parse_tcp_address(self.spec.address)
            server = self._server

            def target() -> None:
                server.start(host, port)

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
    """Spec for InvisiblesServer."""

    factory: type = InvisiblesServer
    name: str = "invisibles-server"

    transport: str = "tcp"  # "tcp" or "unix"
    address: str = "127.0.0.1:18812"

    root_service: ResourceSpec = attrs.Factory(ResourceFactorySpec)
