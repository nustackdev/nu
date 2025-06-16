from __future__ import annotations

import multiprocessing as mp
import threading
from concurrent.futures import Future, ProcessPoolExecutor
from typing import TYPE_CHECKING, Any
from uuid import uuid4

from loomi.service import SyncService
from loomi.spec import Spec, SpecField

from .._base import BaseTask, BaseWorkerPool
from .._exceptions import TaskCancellationError, WorkerPoolOperationError
from .._protocols import TaskProtocol
from .._types import TaskStatus, WorkerFunction
from .logger import logger

__all__ = [
    "MultiprocessingWorkerPool",
    "MultiprocessingWorkerPoolSpec",
    "MultiprocessingTask",
]


class MultiprocessingTask(BaseTask):
    """Task implementation for multiprocessing worker pool."""

    def __init__(self, future: Future[Any]):
        """Initialize task with a concurrent.futures.Future."""
        self._future = future
        self._uuid = uuid4()

    def get(self) -> Any:
        """Get task result, blocking until complete."""
        if self.is_cancelled():
            raise TaskCancellationError("Task was cancelled")

        try:
            return self._future.result()
        except Exception as e:
            # Re-raise the original exception from the task
            raise e

    def cancel(self) -> bool:
        """Attempt to cancel task."""
        return self._future.cancel()

    def is_done(self) -> bool:
        """Check if task is complete."""
        return self._future.done()

    def is_cancelled(self) -> bool:
        """Check if task was cancelled."""
        return self._future.cancelled()

    @property
    def status(self) -> TaskStatus:
        """Get current task status."""
        if self.is_cancelled():
            return TaskStatus.CANCELLED
        elif self.is_done():
            # Check if it completed with exception
            if self._future.exception() is not None:
                return TaskStatus.FAILED
            else:
                return TaskStatus.COMPLETED
        else:
            # For ProcessPoolExecutor, we can't easily distinguish PENDING vs RUNNING
            # so we'll just return PENDING for not-done tasks
            return TaskStatus.PENDING

    def __hash__(self) -> int:
        return hash(str(self._uuid))

    def __eq__(self, other: Any) -> bool:
        if other is None:
            return False
        return isinstance(other, type(self)) and self._uuid == other._uuid


class MultiprocessingWorkerPool(BaseWorkerPool, SyncService):
    """
    Multiprocessing-based worker pool implementation.
    Uses ProcessPoolExecutor for cross-platform compatibility.
    """

    spec: MultiprocessingWorkerPoolSpec

    def setup(self) -> None:
        self._executor: ProcessPoolExecutor | None = None
        self._active_tasks: set[MultiprocessingTask] = set()
        self._tasks_lock = threading.Lock()
        super().setup()

    def cleanup(self) -> None:
        super().cleanup()
        with self._tasks_lock:
            self._active_tasks.clear()

    @property
    def max_workers(self) -> int:
        """Maximum number of worker processes."""
        return self.spec.max_workers

    @property
    def worker_count(self) -> int:
        """Number of workers in the pool."""
        return self.max_workers

    def _connect_impl(self) -> None:
        """Initialize the process pool."""
        try:
            # Set start method if specified
            if self.spec.start_method:
                ctx = mp.get_context(self.spec.start_method)
                self._executor = ProcessPoolExecutor(
                    max_workers=self.spec.max_workers, mp_context=ctx
                )
            else:
                self._executor = ProcessPoolExecutor(max_workers=self.spec.max_workers)

            logger.debug(f"Connected multiprocessing pool with {self.max_workers} workers")

        except Exception as e:
            raise WorkerPoolOperationError(f"Failed to initialize process pool: {e}")

    def _disconnect_impl(self) -> None:
        """Shutdown the process pool."""
        if self._executor is not None:
            try:
                # Cancel all pending tasks
                with self._tasks_lock:
                    for task in self._active_tasks.copy():
                        task.cancel()

                # Shutdown executor
                self._executor.shutdown(wait=True)
                logger.debug("Disconnected from multiprocessing pool")

            except Exception as e:
                logger.error(f"Error during pool shutdown: {e}")
            finally:
                self._executor = None

    def _submit_impl(self, func: WorkerFunction, *args: Any, **kwargs: Any) -> TaskProtocol:
        """Submit task to process pool."""
        if self._executor is None:
            raise WorkerPoolOperationError("Process pool is not initialized")

        try:
            # Submit to ProcessPoolExecutor
            future = self._executor.submit(func, *args, **kwargs)

            # Wrap in our task object
            task = MultiprocessingTask(future)

            # Track active task
            with self._tasks_lock:
                self._active_tasks.add(task)

            # Set up callback to remove from active tasks when done
            def cleanup_task(fut: Future[Any]) -> None:
                with self._tasks_lock:
                    self._active_tasks.discard(task)

            future.add_done_callback(cleanup_task)

            return task

        except Exception as e:
            raise WorkerPoolOperationError(f"Failed to submit task: {e}")


class MultiprocessingWorkerPoolSpec(Spec):
    """Specification for multiprocessing worker pool."""

    name: str = SpecField(default="multiprocessing_worker_pool")
    factory: type = SpecField(default=MultiprocessingWorkerPool)
    max_workers: int = SpecField(default_factory=lambda: mp.cpu_count())
    start_method: str | None = SpecField(default=None)  # None, 'fork', 'spawn', 'forkserver'


if TYPE_CHECKING:
    _: type[TaskProtocol] = MultiprocessingTask
