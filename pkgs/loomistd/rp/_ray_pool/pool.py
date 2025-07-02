from __future__ import annotations

from typing import Any, Dict, List

import ray

from loomi.service import SyncService
from loomi.spec import Spec, SpecField

from .._base import BaseWorkerPool
from ..exceptions import WorkerPoolOperationError
from .logger import logger
from .ray_actor import RayWorkerActor

__all__ = [
    "RayWorkerPool",
    "RayWorkerPoolSpec",
]


class RayWorkerPool(BaseWorkerPool, SyncService):
    """
    Ray-based worker pool implementation.
    Each worker is a Ray actor running a Loomi server.
    """

    spec: RayWorkerPoolSpec

    def setup(self) -> None:
        self._workers: List[ray.ObjectRef] = []
        super().setup()

    @property
    def max_workers(self) -> int:
        """Maximum number of worker processes."""
        return self.spec.max_workers

    @property
    def worker_count(self) -> int:
        """Number of workers in the pool."""
        return len(self._workers)

    def _connect_impl(self) -> None:
        """Initialize Ray and create worker actors."""
        try:
            # Initialize Ray if not already initialized
            if not ray.is_initialized():
                ray.init(
                    address=self.spec.ray_address,
                    **self.spec.ray_init_kwargs,
                )

            # Create worker actors
            self._workers = []
            for idx, spec in enumerate(self.spec.worker_server_specs):
                # Create server spec for this worker
                # server_spec = self._create_server_spec_for_endpoint(endpoint)

                # Create Ray actor
                worker_actor = RayWorkerActor.remote(idx, spec)

                self._workers.append(worker_actor)

            # Start all servers
            start_futures = [worker.start_server.remote() for worker in self._workers]
            results = ray.get(start_futures)

            logger.info(f"Started Ray worker pool with {len(self._workers)} workers")
            logger.debug(f"Worker start results: {results}")

        except Exception as e:
            raise WorkerPoolOperationError(f"Failed to initialize Ray worker pool: {e}")

    def _disconnect_impl(self) -> None:
        """Stop all workers and shutdown Ray."""
        try:
            if self._workers:
                # Stop all servers
                stop_futures = [worker.stop_server.remote() for worker in self._workers]
                ray.get(stop_futures)

                # Kill the actors
                for worker in self._workers:
                    ray.kill(worker)

                self._workers.clear()

            # Optionally shutdown Ray if we initialized it
            if self.spec.shutdown_ray_on_disconnect and ray.is_initialized():
                ray.shutdown()

            logger.debug("Disconnected from Ray worker pool")

        except Exception as e:
            logger.error(f"Error during Ray pool shutdown: {e}")

    def get_worker_info(self) -> List[Dict[str, Any]]:
        """Get information about all workers."""
        if not self._workers:
            return []

        info_futures = [worker.get_worker_info.remote() for worker in self._workers]
        return ray.get(info_futures)

    def health_check(self) -> Dict[str, Any]:
        """Check health of all workers."""
        if not self._workers:
            return {"healthy": False, "reason": "no_workers"}

        health_futures = [worker.health_check.remote() for worker in self._workers]
        health_results = ray.get(health_futures)

        healthy_workers = sum(1 for result in health_results if result.get("healthy", False))

        return {
            "healthy": healthy_workers == len(self._workers),
            "healthy_workers": healthy_workers,
            "total_workers": len(self._workers),
            "worker_health": health_results,
        }

    def restart_worker(self, worker_index: int) -> bool:
        """Restart a specific worker."""
        try:
            if worker_index >= len(self._workers):
                raise ValueError(f"Worker index {worker_index} out of range")

            # Kill the old worker
            old_worker = self._workers[worker_index]
            ray.kill(old_worker)

            new_worker = RayWorkerActor.remote(
                worker_index=worker_index,
                server_spec=self.spec.worker_server_specs[worker_index],
            )

            # Start the new worker
            result = ray.get(new_worker.start_server.remote())

            # Replace in the list
            self._workers[worker_index] = new_worker

            logger.info(f"Restarted worker {worker_index}: {result}")
            return True

        except Exception as e:
            logger.error(f"Failed to restart worker {worker_index}: {e}")
            return False


class RayWorkerPoolSpec(Spec):
    """Specification for Ray worker pool."""

    name: str = SpecField(default="ray_worker_pool")
    factory: type = SpecField(default=RayWorkerPool)

    # Ray configuration
    max_workers: int = SpecField(default=4)
    ray_address: str | None = SpecField(default=None)  # None for local cluster
    ray_init_kwargs: dict[str, Any] = SpecField(default_factory=dict)
    shutdown_ray_on_disconnect: bool = SpecField(default=False)

    # Connection configuration
    worker_server_specs: list[Spec] = SpecField()
    worker_client_specs: list[Spec] = SpecField()
