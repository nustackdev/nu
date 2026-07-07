"""``InvisiblesServer``: host a bound fabric over TCP / Unix socket.

FabricLifecycle. On ``asetup`` reads the root fabric from ctx by ``target``
type + tag, starts a background netkit server on ``address``, and serves it
via the invisibles protocol. On ``acleanup`` stops the server.

Pure transport - no new refs, no new interactions. The server just exposes
whatever bound fabric you name.

Two orthogonal axes:
- executor (netkit): how connections are accepted -- "simple" (one at a time),
  "threaded" (thread per connection).
- dispatcher (invisibles): how method calls run -- "inline" (sync in serve
  thread), "async" (event loop for async methods), "threaded" (thread pool),
  "shared" (serialized across connections).

Usage::

    Provide(Navigator, {"..."},
        Provide(InvisiblesServer, {"target": Navigator,
                                   "address": "10.0.0.1:19000"},
            body,
        ),
    )
"""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING

from netkit import SyncConnection, SyncServer
from netkit.executors import SimpleExecutor
from netkit.executors.threaded import ThreadedExecutor
from netkit.framing import LengthPrefixedFraming
from netkit.transports import TCPListener, UnixSocketListener

from invisibles import (
    AsyncDispatcher,
    InlineDispatcher,
    InvisiblesConnection,
    Protocol,
    SharedDispatcher,
    ThreadedDispatcher,
)
from invisibles.config import AttributeAccessConfig, ConnectionConfig


if TYPE_CHECKING:
    from nu.lang.runtime import Context


__all__ = ["InvisiblesServer"]


_EXECUTORS = {"simple": SimpleExecutor, "threaded": ThreadedExecutor}
_DISPATCHERS = {
    "inline": InlineDispatcher,
    "async": AsyncDispatcher,
    "threaded": ThreadedDispatcher,
    "shared": SharedDispatcher,
}


def _framing_factory(transport: object) -> LengthPrefixedFraming:
    return LengthPrefixedFraming(transport, max_frame_size=1024 * 1024)


class InvisiblesServer:
    """Serves the bound ``target`` fabric on ``address`` over invisibles."""

    def __init__(
        self,
        target: type,
        address: str,
        *,
        target_tag: object = None,
        transport: str = "tcp",
        executor: str = "simple",
        dispatcher: str = "inline",
    ) -> None:
        if transport not in ("tcp", "unix"):
            msg = f"transport must be 'tcp' or 'unix', got {transport!r}"
            raise ValueError(msg)
        if executor not in _EXECUTORS:
            msg = f"executor must be one of {list(_EXECUTORS)}, got {executor!r}"
            raise ValueError(msg)
        if dispatcher not in _DISPATCHERS:
            msg = f"dispatcher must be one of {list(_DISPATCHERS)}, got {dispatcher!r}"
            raise ValueError(msg)
        self.target = target
        self.address = address
        self.target_tag = target_tag
        self.transport = transport
        self.executor = executor
        self.dispatcher = dispatcher
        self._server: SyncServer | None = None
        self._thread: threading.Thread | None = None

    async def asetup(self, ctx: Context) -> None:
        tag = (self.target_tag,) if self.target_tag is not None else ()
        root = ctx.get(self.target, *tag)

        config = ConnectionConfig(attrs=AttributeAccessConfig(allow_all_attrs=True))
        listener_factory = UnixSocketListener if self.transport == "unix" else TCPListener
        executor_cls = _EXECUTORS[self.executor]
        dispatcher_cls = _DISPATCHERS[self.dispatcher]

        server = SyncServer(
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

        server.set_handler(handle_connection)
        self._server = server

        if self.transport == "unix":
            def target() -> None:
                server.start(self.address)
        else:
            host, port = self._parse_tcp_address(self.address)
            def target() -> None:
                server.start(host, port)

        self._thread = threading.Thread(target=target, daemon=True, name="invisibles-server")
        self._thread.start()

    async def acleanup(self) -> None:
        if self._server is not None:
            self._server.stop(wait=False)
            self._server = None

    @staticmethod
    def _parse_tcp_address(address: str) -> tuple[str, int]:
        if ":" in address:
            host, port_str = address.rsplit(":", 1)
            return host, int(port_str)
        return "127.0.0.1", int(address)
