"""ProcessLauncher - spawns a subprocess running an InvisiblesServer.

The subprocess creates a Resource from inner_spec, serves it via InvisiblesServer.
"""

from __future__ import annotations

import multiprocessing as mp
from pathlib import Path

import attrs
from composables import Resource, ResourceSpec


__all__ = [
    "ProcessLauncher",
    "ProcessLauncherSpec",
]


def _worker_main(
    inner_spec: ResourceSpec,
    transport: str,
    address: str,
    ready_queue: mp.Queue,
    shutdown_event: mp.Event,
) -> None:
    """Worker subprocess: create resource from inner_spec, serve via invisibles."""
    import asyncio
    import os
    import signal

    signal.signal(signal.SIGINT, signal.SIG_IGN)

    try:
        from composables import Runtime

        from eb_distributed.rpc.server import InvisiblesServer, InvisiblesServerSpec

        async def run() -> None:
            async with Runtime() as runtime:
                # Create the resource from inner_spec
                resource = await runtime.create(inner_spec)

                # Serve it via invisibles
                server_spec = InvisiblesServerSpec(transport=transport, address=address)
                server = InvisiblesServer(server_spec, root_service=resource)
                await runtime.adopt(server)

                ready_queue.put({"status": "ready", "pid": os.getpid(), "address": address})

                while not shutdown_event.is_set():
                    await asyncio.sleep(0.1)

        asyncio.run(run())

    except Exception:
        import os
        import traceback

        ready_queue.put({"status": "error", "error": traceback.format_exc(), "pid": os.getpid()})


class ProcessLauncher(Resource):
    """Spawns a subprocess with an InvisiblesServer serving a Resource."""

    spec: ProcessLauncherSpec

    async def setup(self) -> None:
        """Start the worker subprocess and wait for it to be ready."""
        ctx = mp.get_context("fork")
        self._ready_queue: mp.Queue = ctx.Queue()
        self._shutdown_event: mp.Event = ctx.Event()

        self._process = ctx.Process(
            target=_worker_main,
            args=(
                self.spec.inner_spec,
                self.spec.transport,
                self.spec.address,
                self._ready_queue,
                self._shutdown_event,
            ),
            daemon=True,
            name=f"worker-{self.spec.name}",
        )
        self._process.start()

        try:
            result = self._ready_queue.get(timeout=self.spec.startup_timeout)
        except Exception as err:
            self._kill_process()
            raise TimeoutError(
                f"Worker '{self.spec.name}' didn't start within {self.spec.startup_timeout}s"
            ) from err

        if result["status"] == "error":
            self._kill_process()
            raise RuntimeError(f"Worker '{self.spec.name}' failed:\n{result['error']}")

        self._worker_pid = result["pid"]
        self._worker_address = result["address"]

    async def cleanup(self) -> None:
        """Stop the worker subprocess and clean up resources."""
        if hasattr(self, "_shutdown_event"):
            self._shutdown_event.set()

        if hasattr(self, "_process") and self._process.is_alive():
            self._process.join(timeout=5.0)
            if self._process.is_alive():
                self._process.terminate()
                self._process.join(timeout=2.0)
                if self._process.is_alive():
                    self._process.kill()

        if self.spec.transport == "unix":
            sock_path = Path(self.spec.address)
            if sock_path.exists():
                sock_path.unlink()

    @property
    def address(self) -> str:
        """Return the address the worker is listening on."""
        return self._worker_address

    @property
    def pid(self) -> int:
        """Return the PID of the worker subprocess."""
        return self._worker_pid

    def _kill_process(self) -> None:
        if hasattr(self, "_process") and self._process.is_alive():
            self._process.kill()
            self._process.join(timeout=2.0)


@attrs.define(frozen=True, slots=True, kw_only=True)
class ProcessLauncherSpec(ResourceSpec):
    """Spec for ProcessLauncher - configures subprocess worker parameters."""

    factory: type = ProcessLauncher
    name: str = "process-launcher"

    inner_spec: ResourceSpec = None  # what Resource to create and serve
    transport: str = "unix"
    address: str = "/tmp/eb_worker.sock"  # noqa: S108
    startup_timeout: float = 10.0
