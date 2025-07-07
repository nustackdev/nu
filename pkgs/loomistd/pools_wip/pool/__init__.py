"""
Loomi Pool System - End-to-End Proof of Concept (Fixed Version)

This implements a complete pool system for Loomi with:
- AttachPool descriptor following Loomi patterns
- PoolCoordinator for task submission and worker management
- Multiprocessing backend implementation
- Task lifecycle management
- Spec-based configuration
"""

from __future__ import annotations

import multiprocessing as mp
import threading
import time
from abc import ABC, abstractmethod
from concurrent.futures import Future, ProcessPoolExecutor
from enum import Enum, auto
from typing import Any, Protocol, cast, runtime_checkable
from uuid import uuid4

import attrs

from loomi import SyncService
from loomi.spec import Spec
from loomicore.attach import AttachError, BaseResourceDescriptor
from loomicore.common.descriptor import StorageStrategy, ValidationStrategy
from loomicore.resource import Resource
from loomicore.runtime import DependencyManager

# =============================================================================
# TEST SERVICE (Since we need ComputeService)
# =============================================================================


class ComputeService(SyncService):
    """Example compute service for demonstration."""

    def setup(self):
        self.counter = 0

    def process_item(self, item: dict) -> dict:
        """Process a single item."""
        time.sleep(0.1)  # Simulate work
        self.counter += 1
        return {
            "input": item,
            "result": item.get("value", 0) * 2,
            "worker_counter": self.counter,
            "processed_by": f"worker_{mp.current_process().pid}",
        }

    def heavy_computation(self, n: int) -> int:
        """Example heavy computation."""
        time.sleep(0.2)  # Simulate heavy work
        return sum(i * i for i in range(n))


@attrs.define(frozen=True, slots=True, kw_only=True)
class ComputeServiceSpec(Spec):
    """Specification for compute service."""

    name: str = "compute_service"
    factory: type = ComputeService


# =============================================================================
# TYPES AND EXCEPTIONS
# =============================================================================


class TaskStatus(Enum):
    """Status of a task in the pool."""

    PENDING = auto()
    RUNNING = auto()
    COMPLETED = auto()
    FAILED = auto()
    CANCELLED = auto()


class PoolError(Exception):
    """Base exception for pool-related errors."""

    pass


class TaskError(PoolError):
    """Base exception for task-related errors."""

    pass


class TaskCancellationError(TaskError):
    """Raised when accessing result of cancelled task."""

    pass


# =============================================================================
# TASK IMPLEMENTATION
# =============================================================================


class Task(ABC):
    """Abstract base class for tasks."""

    @abstractmethod
    def get(self, timeout: float | None = None) -> Any:
        """Get task result, blocking until complete."""
        ...

    @abstractmethod
    def cancel(self) -> bool:
        """Attempt to cancel task."""
        ...

    @abstractmethod
    def is_done(self) -> bool:
        """Check if task is complete."""
        ...

    @abstractmethod
    def is_cancelled(self) -> bool:
        """Check if task was cancelled."""
        ...

    @property
    @abstractmethod
    def status(self) -> TaskStatus:
        """Get current task status."""
        ...


class MultiprocessingTask(Task):
    """Task implementation for multiprocessing backend."""

    def __init__(self, future: Future[Any]):
        self._future = future
        self._uuid = uuid4()

    def get(self, timeout: float | None = None) -> Any:
        """Get task result, blocking until complete."""
        if self.is_cancelled():
            raise TaskCancellationError("Task was cancelled")

        try:
            return self._future.result(timeout=timeout)
        except Exception as e:
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
            if self._future.exception() is not None:
                return TaskStatus.FAILED
            else:
                return TaskStatus.COMPLETED
        else:
            return TaskStatus.PENDING

    def __hash__(self) -> int:
        return hash(str(self._uuid))

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, MultiprocessingTask) and self._uuid == other._uuid


# =============================================================================
# BACKEND INTERFACES
# =============================================================================


@runtime_checkable
class PoolBackendProtocol(Protocol):
    """Protocol for pool backend implementations."""

    def submit_task(
        self,
        worker: Resource,
        spec: Spec,
        method: str,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> Task:
        """Submit a task to a specific worker."""
        ...

    def select_worker(self, workers: list[Resource], strategy: str = "round_robin") -> Resource:
        """Select a worker based on load balancing strategy."""
        ...

    def shutdown(self) -> None:
        """Shutdown the backend."""
        ...


# =============================================================================
# WORKER EXECUTION FUNCTION
# =============================================================================


def execute_remote_method(spec: Spec, method: str, args: tuple, kwargs: dict) -> Any:
    """
    Execute a method on a resource created from spec.

    This function runs in worker processes and recreates the resource
    from its spec, then calls the requested method.
    """
    try:
        # Create resource instance from spec
        resource = spec.factory(spec)

        # Initialize if it's a Loomi resource
        if hasattr(resource, "initialize"):
            resource.initialize()

        try:
            # Get and call the method
            method_func = getattr(resource, method)
            result = method_func(*args, **kwargs)
            return result
        finally:
            # Cleanup if it's a Loomi resource
            if hasattr(resource, "shutdown"):
                resource.shutdown()

    except Exception as e:
        raise e


# =============================================================================
# MULTIPROCESSING BACKEND
# =============================================================================


class MultiprocessingPoolBackend(SyncService):
    """Multiprocessing-based pool backend implementation."""

    spec: MultiprocessingBackendSpec

    def setup(self) -> None:
        """Initialize the multiprocessing backend."""
        self._executor: ProcessPoolExecutor | None = None
        self._active_tasks: set[MultiprocessingTask] = set()
        self._tasks_lock = threading.Lock()
        self._worker_index = 0  # For round-robin

        # Initialize executor
        self._executor = ProcessPoolExecutor(
            max_workers=self.spec.max_workers,
            mp_context=mp.get_context(self.spec.start_method) if self.spec.start_method else None,
        )

    def cleanup(self) -> None:
        """Clean up the backend."""
        self.shutdown()

    def submit_task(
        self,
        worker: Resource,
        spec: Spec,
        method: str,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> Task:
        """Submit a task to the multiprocessing pool."""
        if self._executor is None:
            raise PoolError("Backend not initialized")

        try:
            # Submit to executor - specs are pickleable since they're frozen
            future = self._executor.submit(execute_remote_method, spec, method, args, kwargs)

            # Wrap in our task object
            task = MultiprocessingTask(future)

            # Track active task
            with self._tasks_lock:
                self._active_tasks.add(task)

            # Set up cleanup callback
            def cleanup_task(fut: Future[Any]) -> None:
                with self._tasks_lock:
                    self._active_tasks.discard(task)

            future.add_done_callback(cleanup_task)

            return task

        except Exception as e:
            raise PoolError(f"Failed to submit task: {e}")

    def select_worker(self, workers: list[Resource], strategy: str = "round_robin") -> Resource:
        """Select a worker based on strategy."""
        if not workers:
            raise PoolError("No workers available")

        if strategy == "round_robin":
            worker = workers[self._worker_index % len(workers)]
            self._worker_index += 1
            return worker
        elif strategy == "random":
            import random

            return random.choice(workers)
        else:
            # Default to first worker
            return workers[0]

    def shutdown(self) -> None:
        """Shutdown the backend."""
        if self._executor is not None:
            try:
                # Cancel active tasks
                with self._tasks_lock:
                    for task in self._active_tasks.copy():
                        task.cancel()

                # Shutdown executor
                self._executor.shutdown(wait=True)
            finally:
                self._executor = None


# =============================================================================
# POOL COORDINATOR
# =============================================================================


class PoolCoordinator:
    """
    Coordinator for managing worker pools and task submission.

    Similar to ListCoordinator but with task submission capabilities.
    """

    def __init__(self, workers: list[Resource], backend: PoolBackendProtocol):
        """Initialize pool coordinator."""
        if not workers:
            raise PoolError("Pool requires at least one worker")

        self._workers = list(workers)
        self._backend = backend

    # Task submission API
    def submit(self, spec: Spec, method: str, *args: Any, **kwargs: Any) -> Task:
        """
        Submit a task to the pool.

        Args:
            spec: Resource specification to create for task execution
            method: Method name to call on the resource
            *args: Arguments for the method
            **kwargs: Keyword arguments for the method

        Returns:
            Task object representing the pending execution
        """
        # Select worker using backend strategy
        worker = self._backend.select_worker(self._workers)

        # Submit task to backend
        return self._backend.submit_task(worker, spec, method, args, kwargs)

    def map(self, spec: Spec, method: str, items: list[Any], **kwargs: Any) -> list[Task]:
        """
        Submit multiple tasks for a list of items.

        Args:
            spec: Resource specification for each task
            method: Method name to call
            items: List of items to process (each becomes first arg)
            **kwargs: Common keyword arguments for all tasks

        Returns:
            List of Task objects
        """
        tasks = []
        for item in items:
            task = self.submit(spec, method, item, **kwargs)
            tasks.append(task)
        return tasks

    # Pool management
    def get_worker(self, strategy: str = "round_robin") -> Resource:
        """Get a worker using specified strategy."""
        return self._backend.select_worker(self._workers, strategy)

    def health_check(self) -> dict[str, Any]:
        """Check health of all workers."""
        # For multiprocessing backend, we check if executor is alive
        healthy_count = (
            len(self._workers)
            if hasattr(self._backend, "_executor") and self._backend._executor
            else 0
        )

        worker_health = []
        for i, worker in enumerate(self._workers):
            worker_health.append(
                {
                    "worker_index": i,
                    "worker_name": getattr(worker, "name", f"worker_{i}"),
                    "healthy": healthy_count > 0,
                }
            )

        return {
            "healthy": healthy_count == len(self._workers),
            "healthy_workers": healthy_count,
            "total_workers": len(self._workers),
            "worker_health": worker_health,
        }

    # List-like interface
    def get(self, index: int) -> Resource:
        """Get worker at specified index."""
        return self._workers[index]

    @property
    def workers(self) -> list[Resource]:
        """Get all workers."""
        return list(self._workers)  # Return copy for safety

    def __len__(self) -> int:
        """Get number of workers."""
        return len(self._workers)

    def __iter__(self):
        """Iterate over workers."""
        return iter(self._workers)

    def __getitem__(self, index: int) -> Resource:
        """Get worker using bracket notation."""
        return self.get(index)

    def __repr__(self) -> str:
        """String representation for debugging."""
        worker_names = [getattr(w, "name", str(w)) for w in self._workers]
        return f"<PoolCoordinator: {len(self._workers)} workers: {worker_names}>"


# =============================================================================
# ATTACH DESCRIPTOR
# =============================================================================


class PoolDescriptor(BaseResourceDescriptor):
    """
    Descriptor for pool attachment via AttachPool().

    Similar to ManyListDescriptor but creates PoolCoordinator.
    """

    def __init__(
        self,
        backend_spec: Spec | None = None,
        worker_specs: list[Spec] | None = None,
        load_balancer: str = "round_robin",
        alias: str | None = None,
    ):
        super().__init__(
            storage=StorageStrategy.WEAKREF,
            validation_strategy=ValidationStrategy.STRICT,
            allow_none=True,
        )
        self.backend_spec = backend_spec
        self.worker_specs = worker_specs or []
        self.load_balancer = load_balancer
        self.alias = alias

    def _validate_type(self, value: Any) -> bool:
        """Validate that value is a PoolCoordinator."""
        return value is None or isinstance(value, PoolCoordinator)

    def _get_default(self) -> None:
        """Default value is None until resolved."""
        return None

    def resolve(
        self, parent: Resource, name: str, dependency_manager: DependencyManager
    ) -> PoolCoordinator:
        """
        Resolve pool coordinator with workers and backend.

        This follows the same pattern as ManyListDescriptor.resolve()
        """
        # Get worker specs using priority system
        worker_specs = self._get_worker_specs(parent, name)

        if not worker_specs:
            raise AttachError(
                f"No worker specs found for AttachPool '{name}' in '{parent.readable_name}'"
            )

        # Get backend spec
        backend_spec = self._get_backend_spec(parent, name)

        if not backend_spec:
            # Default to multiprocessing backend
            backend_spec = MultiprocessingBackendSpec()

        # Create workers
        workers: list[Resource] = []
        for i, spec in enumerate(worker_specs):
            try:
                worker = dependency_manager.resolve_dependency(parent, f"{name}_worker_{i}", spec)
                workers.append(worker)
            except Exception as e:
                raise AttachError(f"Failed to resolve worker {i} for pool '{name}': {e}") from e

        # Create backend
        try:
            backend = dependency_manager.resolve_dependency(parent, f"{name}_backend", backend_spec)
        except Exception as e:
            raise AttachError(f"Failed to resolve backend for pool '{name}': {e}") from e

        backend = cast(PoolBackendProtocol, backend)

        # Create coordinator
        try:
            coordinator = PoolCoordinator(workers, backend)
            return coordinator
        except Exception as e:
            raise AttachError(f"Failed to create PoolCoordinator for '{name}': {e}") from e

    def _get_worker_specs(self, parent: Resource, name: str) -> list[Spec]:
        """Get worker specs using priority: parent spec > descriptor specs."""
        # Priority 1: From parent resource spec
        if hasattr(parent.spec, name):
            parent_value = getattr(parent.spec, name)
            if hasattr(parent_value, "worker_specs"):
                return parent_value.worker_specs

        # Priority 2: From descriptor
        if self.worker_specs:
            return self.worker_specs

        # No specs found
        return []

    def _get_backend_spec(self, parent: Resource, name: str) -> Spec | None:
        """Get backend spec using priority: parent spec > descriptor spec."""
        # Priority 1: From parent resource spec
        if hasattr(parent.spec, name):
            parent_value = getattr(parent.spec, name)
            if hasattr(parent_value, "backend_spec"):
                return parent_value.backend_spec

        # Priority 2: From descriptor
        if self.backend_spec:
            return self.backend_spec

        return None


def AttachPool(
    backend_spec: Spec | None = None,
    worker_specs: list[Spec] | None = None,
    *,
    load_balancer: str = "round_robin",
    alias: str | None = None,
) -> Any:
    """
    Create a pool attachment descriptor.

    This follows the same pattern as AttachMany() but creates a PoolCoordinator
    for task submission rather than just resource access.

    Args:
        backend_spec: Specification for the pool backend (multiprocessing, ray, etc.)
        worker_specs: List of worker resource specifications
        load_balancer: Load balancing strategy ("round_robin", "random")
        alias: Optional alias for the pool

    Returns:
        PoolDescriptor that resolves to a PoolCoordinator
    """
    return PoolDescriptor(backend_spec, worker_specs, load_balancer, alias)


# =============================================================================
# SPECS
# =============================================================================


@attrs.define(frozen=True, slots=True, kw_only=True)
class MultiprocessingBackendSpec(Spec):
    """Specification for multiprocessing pool backend."""

    name: str = "multiprocessing_backend"
    factory: type = MultiprocessingPoolBackend
    max_workers: int = attrs.field(factory=lambda: max(2, mp.cpu_count() // 2))
    start_method: str | None = None  # 'spawn', 'fork', 'forkserver'


@attrs.define(frozen=True, slots=True, kw_only=True)
class PoolSpec(Spec):
    """Specification for complete pool configuration."""

    name: str = "worker_pool"
    factory: type | None = None  # Not directly instantiated
    backend_spec: Spec = attrs.field(factory=MultiprocessingBackendSpec)
    worker_specs: list[Spec] = attrs.field(factory=list)
    load_balancer: str = "round_robin"


# =============================================================================
# EXAMPLE USAGE
# =============================================================================


class DataProcessor(SyncService):
    """Example service that uses worker pool."""

    # Pool attachment - workers defined in spec
    compute_pool = AttachPool()

    def process_batch(self, items: list[dict]) -> list[dict]:
        """Process a batch of items using the worker pool."""
        print(f"Processing {len(items)} items with pool...")

        # Submit all tasks
        tasks = []
        for item in items:
            task = self.compute_pool.submit(
                spec=ComputeServiceSpec(), method="process_item", args=(item,)
            )
            tasks.append(task)

        # Collect results
        results = []
        for i, task in enumerate(tasks):
            try:
                result = task.get(timeout=10.0)
                results.append(result)
                print(f"  ✓ Task {i + 1} completed")
            except Exception as e:
                results.append({"error": str(e)})
                print(f"  ✗ Task {i + 1} failed: {e}")

        return results

    def parallel_computation(self, numbers: list[int]) -> list[int]:
        """Perform heavy computations in parallel."""
        print(f"Computing {len(numbers)} heavy operations in parallel...")

        tasks = self.compute_pool.map(
            spec=ComputeServiceSpec(), method="heavy_computation", items=numbers
        )

        results = []
        for i, task in enumerate(tasks):
            result = task.get(timeout=10.0)
            results.append(result)
            print(f"  ✓ Computation {i + 1} completed: {result}")

        return results


@attrs.define(frozen=True, slots=True, kw_only=True)
class DataProcessorSpec(Spec):
    """Specification for data processor with pool configuration."""

    name: str = "data_processor"
    factory: type = DataProcessor

    # Pool configuration
    compute_pool: PoolSpec = PoolSpec(
        backend_spec=MultiprocessingBackendSpec(max_workers=2),
        worker_specs=[
            ComputeServiceSpec(name="worker_1"),
            ComputeServiceSpec(name="worker_2"),
        ],
        load_balancer="round_robin",
    )


# =============================================================================
# DEMO FUNCTION
# =============================================================================


def demo():
    """Demonstrate the pool system."""
    print("=== Loomi Pool System Demo ===\n")

    # Create data processor with pool
    spec = DataProcessorSpec()

    try:
        with DataProcessor(spec) as processor:
            print(f"✓ Created DataProcessor with pool: {processor.compute_pool}")
            print(f"✓ Pool has {len(processor.compute_pool)} workers")

            # Test health check
            health = processor.compute_pool.health_check()
            print(f"✓ Pool health: {health['healthy_workers']}/{health['total_workers']} healthy")

            # Test batch processing
            print("\n--- Testing Batch Processing ---")
            items = [
                {"id": 1, "value": 10},
                {"id": 2, "value": 20},
                {"id": 3, "value": 30},
                {"id": 4, "value": 40},
            ]

            start_time = time.time()
            results = processor.process_batch(items)
            end_time = time.time()

            print(f"\n✓ Processed {len(items)} items in {end_time - start_time:.2f}s")
            for i, result in enumerate(results):
                if "error" not in result:
                    print(
                        f"  • Item {i + 1}: {result['input']['value']} -> {result['result']} (by {result['processed_by']})"
                    )
                else:
                    print(f"  • Item {i + 1}: ERROR - {result['error']}")

            # Test parallel computation
            print("\n--- Testing Parallel Computation ---")
            numbers = [50, 75, 100]

            start_time = time.time()
            computation_results = processor.parallel_computation(numbers)
            end_time = time.time()

            print(f"\n✓ Computed {len(numbers)} heavy operations in {end_time - start_time:.2f}s")
            for i, result in enumerate(computation_results):
                print(f"  • sum(i²) for i in range({numbers[i]}) = {result}")

        print("\n✓ Demo completed successfully!")

    except Exception as e:
        print(f"\n✗ Demo failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    # Handle multiprocessing on Windows
    mp.set_start_method("spawn", force=True)
    demo()
