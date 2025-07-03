"""
Multiprocessing adapter for resource pools.

This adapter uses Python's multiprocessing to start worker processes
that run Loomi servers at specified endpoints.
"""

from __future__ import annotations

import multiprocessing as mp
import time
from typing import Any, Dict, List, Optional

from loomi.service import SyncService
from loomi.spec import Spec, SpecField

from .exceptions import ResourcePoolError
from .logger import logger
from .worker import WorkerEndpoint

__all__ = [
    "MultiprocessingAdapter",
    "MultiprocessingAdapterSpec",
]


def _run_worker_server(endpoint: WorkerEndpoint) -> None:
    """
    Worker function that runs in each multiprocessing process.

    Creates and starts a Loomi server at the specified endpoint.
    This function runs indefinitely until the process is terminated.

    Args:
        endpoint: Worker endpoint configuration
    """
    try:
        logger.info(f"Starting worker server {endpoint.worker_id} at {endpoint.address}")

        # Import here to avoid issues with multiprocessing and imports
        from loomistd.remote import (
            RPyCTCPServer,
            RPyCTCPServerSpec,
            RPyCUnixServer,
            RPyCUnixServerSpec,
        )

        # Create server based on protocol
        if endpoint.protocol == "tcp":
            host, port = endpoint.address.split(":")
            server_spec = RPyCTCPServerSpec(
                bind_address=host,
                bind_port=int(port),
                auto_register=False,  # We don't need RPyC registry for worker servers
            )
            server = RPyCTCPServer(server_spec)

        elif endpoint.protocol == "unix":
            server_spec = RPyCUnixServerSpec(
                socket_path=endpoint.address,
                auto_register=False,
            )
            server = RPyCUnixServer(server_spec)

        else:
            raise ValueError(f"Unsupported protocol: {endpoint.protocol}")

        # Initialize and start server
        server.initialize()

        logger.info(f"Worker {endpoint.worker_id} server initialized, starting...")

        # Start server - this blocks until process is terminated
        server.start()

    except Exception as e:
        logger.error(f"Worker {endpoint.worker_id} failed to start: {e}")
        raise


class MultiprocessingAdapter(SyncService):
    """
    Adapter that uses multiprocessing to manage worker processes.

    Each worker process runs a Loomi server at its assigned endpoint.
    The adapter manages the lifecycle of these processes.
    """

    spec: MultiprocessingAdapterSpec

    def setup(self) -> None:
        """Initialize the multiprocessing adapter."""
        self._processes: List[mp.Process] = []
        self._endpoints: List[WorkerEndpoint] = []

        # Set multiprocessing start method if specified
        if self.spec.start_method:
            try:
                mp.set_start_method(self.spec.start_method, force=True)
                logger.debug(f"Set multiprocessing start method to {self.spec.start_method}")
            except RuntimeError as e:
                # Start method might already be set
                logger.warning(f"Could not set start method: {e}")

    def cleanup(self) -> None:
        """Clean up the adapter and stop all workers."""
        self.stop_workers()

    def start_workers(self, endpoints: List[WorkerEndpoint]) -> None:
        """
        Start worker processes for the given endpoints.

        Args:
            endpoints: List of worker endpoints to start

        Raises:
            ResourcePoolError: If workers fail to start
        """
        if self._processes:
            raise ResourcePoolError("Workers already started")

        logger.info(f"Starting {len(endpoints)} worker processes")

        self._endpoints = endpoints

        for endpoint in endpoints:
            try:
                # Create process for this worker
                process = mp.Process(
                    target=_run_worker_server,
                    args=(endpoint,),
                    name=f"worker_{endpoint.worker_id}",
                    daemon=False,  # We want clean shutdown
                )

                # Start the process
                process.start()
                self._processes.append(process)

                logger.info(f"Started worker process {endpoint.worker_id} (PID: {process.pid})")

            except Exception as e:
                logger.error(f"Failed to start worker {endpoint.worker_id}: {e}")
                # Clean up any processes we've already started
                self.stop_workers()
                raise ResourcePoolError(f"Failed to start worker {endpoint.worker_id}: {e}")

        # Give workers a moment to start up
        time.sleep(self.spec.startup_delay)

        # Check that all processes are still alive
        failed_workers = []
        for i, process in enumerate(self._processes):
            if not process.is_alive():
                failed_workers.append(self._endpoints[i].worker_id)

        if failed_workers:
            self.stop_workers()
            raise ResourcePoolError(f"Workers failed to start: {failed_workers}")

        logger.info(f"All {len(self._processes)} workers started successfully")

    def stop_workers(self) -> None:
        """Stop all worker processes."""
        if not self._processes:
            return

        logger.info(f"Stopping {len(self._processes)} worker processes")

        # First, try graceful termination
        for process in self._processes:
            if process.is_alive():
                process.terminate()

        # Wait for processes to terminate gracefully
        for process in self._processes:
            try:
                process.join(timeout=self.spec.shutdown_timeout)
            except Exception as e:
                logger.warning(f"Error joining process {process.name}: {e}")

        # Force kill any remaining processes
        for process in self._processes:
            if process.is_alive():
                logger.warning(f"Force killing worker process {process.name}")
                process.kill()
                try:
                    process.join(timeout=1.0)
                except Exception:
                    pass

        self._processes.clear()
        self._endpoints.clear()

        logger.info("All worker processes stopped")

    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the worker processes.

        Returns:
            Dictionary containing adapter statistics
        """
        alive_count = sum(1 for p in self._processes if p.is_alive())

        process_stats = []
        for i, process in enumerate(self._processes):
            endpoint = self._endpoints[i] if i < len(self._endpoints) else None
            process_stats.append(
                {
                    "worker_id": endpoint.worker_id if endpoint else f"worker_{i}",
                    "pid": process.pid,
                    "alive": process.is_alive(),
                    "exitcode": process.exitcode,
                }
            )

        return {
            "adapter_type": "multiprocessing",
            "total_workers": len(self._processes),
            "alive_workers": alive_count,
            "start_method": self.spec.start_method,
            "processes": process_stats,
        }

    def is_healthy(self) -> bool:
        """Check if all worker processes are healthy."""
        if not self._processes:
            return False

        # All processes should be alive
        return all(p.is_alive() for p in self._processes)


class MultiprocessingAdapterSpec(Spec):
    """Specification for MultiprocessingAdapter."""

    name: str = SpecField(default="multiprocessing_adapter")
    factory: type = SpecField(default=MultiprocessingAdapter)

    # Multiprocessing configuration
    start_method: Optional[str] = SpecField(default="spawn")  # "spawn", "fork", "forkserver"
    startup_delay: float = SpecField(default=2.0)  # Seconds to wait after starting workers
    shutdown_timeout: float = SpecField(default=5.0)  # Seconds to wait for graceful shutdown


# Factory function for easy configuration
def create_multiprocessing_adapter_spec(
    start_method: str = "spawn",
    startup_delay: float = 2.0,
    shutdown_timeout: float = 5.0,
) -> MultiprocessingAdapterSpec:
    """
    Create a MultiprocessingAdapterSpec with common configuration.

    Args:
        start_method: Multiprocessing start method
        startup_delay: Time to wait after starting workers
        shutdown_timeout: Time to wait for graceful shutdown

    Returns:
        Configured MultiprocessingAdapterSpec
    """
    return MultiprocessingAdapterSpec(
        start_method=start_method,
        startup_delay=startup_delay,
        shutdown_timeout=shutdown_timeout,
    )
