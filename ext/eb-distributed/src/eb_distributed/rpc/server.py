"""InvisiblesServer - composables Resource wrapping an Invisibles RPC server.

Starts a NetKit server that serves a root service object via Invisibles protocol.
Supports TCP and Unix socket transports. Root service is resolved via Attach.

Two orthogonal axes:
- executor (netkit level): how connections are accepted
  - "simple" - one connection at a time (default)
  - "threaded" - thread per connection, concurrent clients
- dispatcher (invisibles level): how method calls are executed
  - "inline" - sync, inline in serve thread (default)
  - "async" - event loop for async methods
  - "threaded" - thread pool for thread-safe objects
  - "shared" - serialized across all connections (shared lock)

See invisibles docs/scenarios.md for the full matrix.
"""

from __future__ import annotations

import threading

import attrs
from composables import Attach, Resource, ResourceSpec
from invisibles import (
    AsyncDispatcher,
    InlineDispatcher,
    InvisiblesConnection,
    Protocol,
    SharedDispatcher,
    ThreadedDispatcher,
)
from invisibles.config import AttributeAccessConfig, ConnectionConfig
from netkit import SyncConnection, SyncServer
from netkit.executors import SimpleExecutor
from netkit.executors.threaded import ThreadedExecutor
from netkit.framing import LengthPrefixedFraming
from netkit.transports import TCPListener, UnixSocketListener

from .factory import ResourceFactorySpec


__all__ = [
    "InvisiblesServer",
    "InvisiblesServerSpec",
]


def _framing_factory(transport: object) -> LengthPrefixedFraming:
    return LengthPrefixedFraming(transport, max_frame_size=1024 * 1024)


_EXECUTORS = {
    "simple": SimpleExecutor,
    "threaded": ThreadedExecutor,
}

_DISPATCHERS = {
    "inline": InlineDispatcher,
    "async": AsyncDispatcher,
    "threaded": ThreadedDispatcher,
    "shared": SharedDispatcher,
}


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
        root = self.root_service

        if self.spec.transport == "unix":
            listener_factory = UnixSocketListener
        else:
            listener_factory = TCPListener

        executor_cls = _EXECUTORS.get(self.spec.executor)
        if executor_cls is None:
            raise ValueError(
                f"Unknown executor: {self.spec.executor!r}. Choose from: {', '.join(_EXECUTORS)}"
            )

        dispatcher_cls = _DISPATCHERS.get(self.spec.dispatcher)
        if dispatcher_cls is None:
            raise ValueError(
                f"Unknown dispatcher: {self.spec.dispatcher!r}. "
                f"Choose from: {', '.join(_DISPATCHERS)}"
            )

        self._server = SyncServer(
            listener_factory=listener_factory,
            framing_factory=_framing_factory,
            executor=executor_cls(),
        )

        def handle_connection(netkit_conn: SyncConnection) -> None:
            dispatcher = dispatcher_cls()
            protocol = Protocol(config, root, dispatcher=dispatcher)
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
    executor: str = "simple"  # "simple" or "threaded"
    dispatcher: str = "inline"  # "inline", "async", "threaded", "shared"

    root_service: ResourceSpec = attrs.Factory(ResourceFactorySpec)
