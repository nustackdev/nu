"""Invisibles Resources - server and client for transparent proxying.

InvisiblesServer: serves a root resource over TCP or Unix socket.
InvisiblesClient: connects and returns a transparent proxy to the root.

Two orthogonal axes:
- executor (netkit level): how connections are accepted
  - "simple" - one connection at a time
  - "threaded" - thread per connection
- dispatcher (invisibles level): how method calls are executed
  - "inline" - sync, inline in serve thread
  - "async" - event loop for async methods
  - "threaded" - thread pool
  - "shared" - serialized across all connections
"""

from __future__ import annotations

import threading
import time

import attrs
from composables import Attach, Resource, ResourceSpec
from invisibles import (
    AsyncDispatcher,
    BgServingThread,
    InlineDispatcher,
    InvisiblesConnection,
    Protocol,
    SharedDispatcher,
    ThreadedDispatcher,
)
from invisibles.config import AttributeAccessConfig, ConnectionConfig
from invisibles.core.consts import HANDLE_GET_ROOT
from netkit import SyncConnection, SyncConnector, SyncServer
from netkit.executors import SimpleExecutor
from netkit.executors.threaded import ThreadedExecutor
from netkit.framing import LengthPrefixedFraming
from netkit.transports import TCPListener, TCPTransport, UnixSocketListener, UnixSocketTransport


__all__ = [
    "InvisiblesClient",
    "InvisiblesClientSpec",
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


# ============================================================================
# Server
# ============================================================================


class InvisiblesServer(Resource):
    """Serves a root resource over TCP or Unix socket via Invisibles protocol."""

    spec: InvisiblesServerSpec
    root_service = Attach()

    async def setup(self) -> None:
        """Start the server in a background thread."""
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
        """Stop the server."""
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

    root_service: ResourceSpec = attrs.field()


# ============================================================================
# Client
# ============================================================================


class InvisiblesClient(Resource):
    """Connects to an InvisiblesServer and returns the root as a transparent proxy."""

    spec: InvisiblesClientSpec

    async def setup(self) -> None:
        """Connect to the remote server with retry logic."""
        config = ConnectionConfig(
            attrs=AttributeAccessConfig(allow_all_attrs=True),
            buffered_iteration=self.spec.buffered_iteration,
        )

        if self.spec.transport == "unix":
            transport_factory = UnixSocketTransport
        else:
            transport_factory = TCPTransport

        connector = SyncConnector(
            transport_factory=transport_factory,
            framing_factory=lambda t: LengthPrefixedFraming(t, max_frame_size=1024 * 1024),
        )

        last_error = None
        for attempt in range(self.spec.max_retries):
            try:
                if self.spec.transport == "unix":
                    netkit_conn = connector.connect(self.spec.address, timeout=self.spec.timeout)
                else:
                    host, port = self._parse_tcp_address(self.spec.address)
                    netkit_conn = connector.connect(host, port, timeout=self.spec.timeout)
                break
            except Exception as e:
                last_error = e
                if attempt < self.spec.max_retries - 1:
                    time.sleep(0.1 * (attempt + 1))
        else:
            raise ConnectionError(
                f"Failed to connect to {self.spec.address} after {self.spec.max_retries} attempts"
            ) from last_error

        protocol = Protocol(config)
        self._connection = InvisiblesConnection(netkit_conn, protocol)
        self._root = self._connection.sync_request(HANDLE_GET_ROOT)

        # Start background serve thread for bidirectional callbacks
        self._bg_serve = None
        if self.spec.bg_serve:
            self._bg_serve = BgServingThread(self._connection)

    async def cleanup(self) -> None:
        """Stop background serve and close the connection."""
        if hasattr(self, "_bg_serve") and self._bg_serve is not None:
            self._bg_serve.stop()
        if hasattr(self, "_connection"):
            self._connection.close()

    @property
    def root(self) -> object:
        """The remote root object (transparent proxy)."""
        return self._root

    def get_proxy(self, spec: object = None) -> object:
        """Get the root object proxy. Spec arg kept for ProxyCoordinator compat."""
        return self._root

    @staticmethod
    def _parse_tcp_address(address: str) -> tuple[str, int]:
        if ":" in address:
            host, port_str = address.rsplit(":", 1)
            return host, int(port_str)
        return "127.0.0.1", int(address)


@attrs.define(frozen=True, slots=True, kw_only=True)
class InvisiblesClientSpec(ResourceSpec):
    """Spec for InvisiblesClient."""

    factory: type = InvisiblesClient
    name: str = "invisibles-client"

    transport: str = "tcp"  # "tcp" or "unix"
    address: str = "127.0.0.1:18812"
    timeout: float = 5.0
    max_retries: int = 3
    bg_serve: bool = False
    buffered_iteration: bool = True
