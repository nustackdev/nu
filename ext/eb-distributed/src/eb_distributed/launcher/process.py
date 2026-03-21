"""ProcessLauncher - spawns a subprocess running an InvisiblesServer.

The subprocess creates an InvisiblesServer via Runtime. The server's
Attach chain resolves ResourceFactory automatically.
Clients connect and request resources through the factory.
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
    server_spec_data: object,
    ready_queue: mp.Queue,
    shutdown_event: mp.Event,
) -> None:
    """Worker subprocess: create InvisiblesServer from spec, serve."""
    import asyncio
    import os
    import signal

    signal.signal(signal.SIGINT, signal.SIG_IGN)

    try:
        from composables import Runtime

        async def run() -> None:
            async with Runtime() as runtime:
                await runtime.create(server_spec_data)

                ready_queue.put(
                    {
                        "status": "ready",
                        "pid": os.getpid(),
                        "address": server_spec_data.address,
                    }
                )

                while not shutdown_event.is_set():
                    await asyncio.sleep(0.1)

        asyncio.run(run())

    except Exception:
        import os
        import traceback

        ready_queue.put({"status": "error", "error": traceback.format_exc(), "pid": os.getpid()})


class ProcessLauncher(Resource):
    """Spawns a subprocess with an InvisiblesServer.

    The subprocess creates an InvisiblesServer via Runtime.
    The server hosts a ResourceFactory (via Attach) that clients
    use to create resources on demand.
    """

    spec: ProcessLauncherSpec

    async def setup(self) -> None:
        """Start the worker subprocess and wait for it to be ready."""
        from eb_distributed.rpc.server import InvisiblesServerSpec

        server_spec = InvisiblesServerSpec(
            transport=self.spec.transport,
            address=self.spec.address,
        )

        ctx = mp.get_context("fork")
        self._ready_queue: mp.Queue = ctx.Queue()
        self._shutdown_event: mp.Event = ctx.Event()

        self._process = ctx.Process(
            target=_worker_main,
            args=(
                server_spec,
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
        """Stop the worker subprocess."""
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
        """Address the worker is listening on."""
        return self._worker_address

    @property
    def pid(self) -> int:
        """PID of the worker subprocess."""
        return self._worker_pid

    def _kill_process(self) -> None:
        if hasattr(self, "_process") and self._process.is_alive():
            self._process.kill()
            self._process.join(timeout=2.0)


@attrs.define(frozen=True, slots=True, kw_only=True)
class ProcessLauncherSpec(ResourceSpec):
    """Spec for ProcessLauncher."""

    factory: type = ProcessLauncher
    name: str = "process-launcher"

    transport: str = "unix"
    address: str = "/tmp/eb_worker.sock"  # noqa: S108
    startup_timeout: float = 10.0
