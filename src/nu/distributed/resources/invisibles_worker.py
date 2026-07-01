"""InvisiblesWorker - execute trees remotely via invisibles.

Alternative to RayWorker. Instead of dispatching trees over Ray,
ships them over invisibles RPC. Tree flies by value (pickle),
executes against a Worker with local Navigator on the server side.

One RPC per execute() call instead of N RPCs per proxied operation.

Server side: InvisiblesWorkerServer hosts a Worker over invisibles.
Client side: InvisiblesWorker connects and forwards execute(tree).

Usage:
    # Server (on red, hosted via Ray or standalone)
    RayActorSpec(
        inner_spec=InvisiblesWorkerServerSpec(
            address="10.0.0.1:19000",
            worker_spec=WorkerSpec(
                context=ContextSpec(
                    storage=NavigatorSpec(storage=RocksDBStorageSpec(...))
                )
            ),
        ),
        node="red",
    )

    # Client (binds as Worker for Teleport)
    worker = await runtime.create(
        InvisiblesWorkerSpec(address="10.0.0.1:19000")
    )
    ctx = ctx.bind(Worker, worker, 0)

    # Teleport sends whole tree in 1 RPC
    await first(Teleport(ebv.Transaction(...), worker=0), ctx)
"""

from __future__ import annotations

import asyncio
import threading
from typing import TYPE_CHECKING

import attrs

from composables import Resource, ResourceSpec


if TYPE_CHECKING:
    from .worker import Worker, WorkerSpec


__all__ = [
    "InvisiblesWorker",
    "InvisiblesWorkerServer",
    "InvisiblesWorkerServerSpec",
    "InvisiblesWorkerSpec",
]


# ============================================================================
# Server
# ============================================================================


class _ExecutionService:
    """Root service exposed via invisibles.

    Wraps a Worker, exposes execute(tree) as a sync method that
    runs the async tree execution on a dedicated event loop thread.
    """

    def __init__(self) -> None:
        self._worker: Worker | None = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._loop_thread: threading.Thread | None = None
        self._runtime = None

    def start(self, worker_spec: WorkerSpec) -> None:
        """Initialize Worker from spec in a dedicated event loop thread."""
        self._loop = asyncio.new_event_loop()
        self._loop_thread = threading.Thread(
            target=self._loop.run_forever, daemon=True, name="worker-loop"
        )
        self._loop_thread.start()

        # Run async setup on the dedicated loop
        future = asyncio.run_coroutine_threadsafe(self._setup(worker_spec), self._loop)
        future.result(timeout=30.0)

    async def _setup(self, worker_spec: WorkerSpec) -> None:
        import nu.distributed  # noqa: F401 - ensure value types registered
        from composables import Runtime

        self._runtime = Runtime()
        await self._runtime.__aenter__()
        self._worker = await self._runtime.create(worker_spec)

    def aexecute(self, tree: object) -> object:
        """Execute tree against worker's Context. Sync wrapper."""
        future = asyncio.run_coroutine_threadsafe(self._worker.aexecute(tree), self._loop)
        return future.result()

    def shutdown(self) -> None:
        if self._runtime and self._loop:
            future = asyncio.run_coroutine_threadsafe(
                self._runtime.__aexit__(None, None, None), self._loop
            )
            try:
                future.result(timeout=5.0)
            except Exception:  # noqa: S110
                pass
        if self._loop:
            self._loop.call_soon_threadsafe(self._loop.stop)
        if self._loop_thread:
            self._loop_thread.join(timeout=2.0)


class InvisiblesWorkerServer(Resource):
    """Hosts a Worker over invisibles. Tree execution in 1 RPC.

    Creates a Worker with local Context/Navigator, serves it via
    invisibles TCP. Clients send trees by value, they execute locally.
    """

    spec: InvisiblesWorkerServerSpec

    async def setup(self) -> None:
        """Start the execution service and invisibles server."""
        from netkit import SyncConnection, SyncServer
        from netkit.executors import SimpleExecutor
        from netkit.executors.threaded import ThreadedExecutor
        from netkit.framing import LengthPrefixedFraming
        from netkit.transports import TCPListener, UnixSocketListener

        from invisibles import InvisiblesConnection, Protocol
        from invisibles.config import AttributeAccessConfig, ConnectionConfig

        # Create the execution service with a Worker
        self._service = _ExecutionService()
        self._service.start(self.spec.worker_spec)

        # Register everybase types as value types for invisibles
        self._register_value_types()

        # Configure invisibles
        config = ConnectionConfig(
            attrs=AttributeAccessConfig(allow_all_attrs=True),
        )

        if self.spec.transport == "unix":
            listener_factory = UnixSocketListener
        else:
            listener_factory = TCPListener

        executor = ThreadedExecutor() if self.spec.threaded else SimpleExecutor()

        self._server = SyncServer(
            listener_factory=listener_factory,
            framing_factory=lambda t: LengthPrefixedFraming(
                t, max_frame_size=self.spec.max_frame_size
            ),
            executor=executor,
        )

        service = self._service

        def handle_connection(netkit_conn: SyncConnection) -> None:
            protocol = Protocol(config, service)
            conn = InvisiblesConnection(netkit_conn, protocol)
            try:
                while netkit_conn.is_connected():
                    conn._serve_one(timeout=1.0)
            except Exception:  # noqa: S110
                pass

        self._server.set_handler(handle_connection)

        if self.spec.transport == "unix":
            address = self.spec.address
            server = self._server

            def target() -> None:
                server.start(address)
        else:
            host, port = self._parse_address(self.spec.address)
            server = self._server

            def target() -> None:
                server.start(host, port)

        self._thread = threading.Thread(target=target, daemon=True, name="invisibles-worker-server")
        self._thread.start()

    async def cleanup(self) -> None:
        """Stop server and worker."""
        if hasattr(self, "_server"):
            self._server.stop(wait=False)
        if hasattr(self, "_service"):
            self._service.shutdown()

    @staticmethod
    def _register_value_types() -> None:
        """Register everybase Nu as value type if not already."""
        try:
            from invisibles.core.boxing import register_value_type
            from nu.lang import Nu

            register_value_type(Nu)
        except ImportError:
            pass

    @staticmethod
    def _parse_address(address: str) -> tuple[str, int]:
        if ":" in address:
            host, port_str = address.rsplit(":", 1)
            return host, int(port_str)
        return "127.0.0.1", int(address)


@attrs.define(frozen=True, slots=True, kw_only=True)
class InvisiblesWorkerServerSpec(ResourceSpec):
    """Spec for InvisiblesWorkerServer."""

    factory: type = InvisiblesWorkerServer
    name: str = "invisibles-worker-server"

    worker_spec: WorkerSpec = attrs.field()
    transport: str = "tcp"
    address: str = "127.0.0.1:19000"
    threaded: bool = False
    max_frame_size: int = 16 * 1024 * 1024  # 16MB for large trees


# ============================================================================
# Client
# ============================================================================


class InvisiblesWorker(Resource):
    """Connects to InvisiblesWorkerServer, forwards execute(tree).

    Bindable as Worker in Context for Teleport resolution:
        ctx.bind(Worker, worker, 0)
        Teleport(..., worker=0)  # resolves to this, calls execute()
    """

    spec: InvisiblesWorkerSpec

    async def setup(self) -> None:
        """Connect to the remote worker server."""
        from netkit import SyncConnector
        from netkit.framing import LengthPrefixedFraming
        from netkit.transports import TCPTransport, UnixSocketTransport

        from invisibles import BgServingThread, InvisiblesConnection, Protocol
        from invisibles.config import AttributeAccessConfig, ConnectionConfig
        from invisibles.core.consts import HANDLE_GET_ROOT

        # Register value types on client side too
        self._register_value_types()

        config = ConnectionConfig(
            attrs=AttributeAccessConfig(allow_all_attrs=True),
        )

        if self.spec.transport == "unix":
            transport_factory = UnixSocketTransport
        else:
            transport_factory = TCPTransport

        connector = SyncConnector(
            transport_factory=transport_factory,
            framing_factory=lambda t: LengthPrefixedFraming(
                t, max_frame_size=self.spec.max_frame_size
            ),
        )

        last_error = None
        for attempt in range(self.spec.max_retries):
            try:
                if self.spec.transport == "unix":
                    netkit_conn = connector.connect(self.spec.address, timeout=self.spec.timeout)
                else:
                    host, port = self._parse_address(self.spec.address)
                    netkit_conn = connector.connect(host, port, timeout=self.spec.timeout)
                break
            except Exception as e:
                last_error = e
                if attempt < self.spec.max_retries - 1:
                    await asyncio.sleep(0.1 * (attempt + 1))
        else:
            raise ConnectionError(
                f"Failed to connect to worker at {self.spec.address} "
                f"after {self.spec.max_retries} attempts"
            ) from last_error

        protocol = Protocol(config)
        self._connection = InvisiblesConnection(netkit_conn, protocol)
        self._remote = self._connection.sync_request(HANDLE_GET_ROOT)

        self._bg_serve = None
        if self.spec.bg_serve:
            self._bg_serve = BgServingThread(self._connection)

    async def aexecute(self, tree: object) -> object:
        """Send tree to remote worker for execution. 1 RPC.

        The underlying invisibles call is synchronous; run it in a thread so
        concurrent `Teleport | Teleport | ...` calls don't serialize
        on the event loop.
        """
        import asyncio

        return await asyncio.to_thread(self._remote.aexecute, tree)

    async def cleanup(self) -> None:
        """Close connection."""
        if hasattr(self, "_bg_serve") and self._bg_serve is not None:
            self._bg_serve.stop()
        if hasattr(self, "_connection"):
            self._connection.close()

    @staticmethod
    def _register_value_types() -> None:
        try:
            from invisibles.core.boxing import register_value_type
            from nu.lang import Nu

            register_value_type(Nu)
        except ImportError:
            pass

    @staticmethod
    def _parse_address(address: str) -> tuple[str, int]:
        if ":" in address:
            host, port_str = address.rsplit(":", 1)
            return host, int(port_str)
        return "127.0.0.1", int(address)


@attrs.define(frozen=True, slots=True, kw_only=True)
class InvisiblesWorkerSpec(ResourceSpec):
    """Spec for InvisiblesWorker (client)."""

    factory: type = InvisiblesWorker
    name: str = "invisibles-worker"

    transport: str = "tcp"
    address: str = "127.0.0.1:19000"
    timeout: float = 5.0
    max_retries: int = 3
    bg_serve: bool = False
    max_frame_size: int = 16 * 1024 * 1024
