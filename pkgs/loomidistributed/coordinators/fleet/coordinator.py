"""
FleetCoordinator - Fleet Management for Distributed Execution

This module implements a FleetCoordinator that extends ListCoordinator with
thread-safe execution coordination capabilities for distributed resource fleets.
"""

from __future__ import annotations

import inspect
import threading
from concurrent.futures import Future, ThreadPoolExecutor
from typing import TYPE_CHECKING, Any, Callable, Generic, TypeVar

from loomicore.attach.many import ListCoordinator

if TYPE_CHECKING:
    from loomicore.resource import Resource

__all__ = [
    "FleetCoordinator",
]

ResourceType = TypeVar("ResourceType", bound="Resource")


class FleetCoordinator(ListCoordinator, Generic[ResourceType]):
    """
    Thread-safe coordinator for managing a fleet of resources with execution coordination.

    Extends ListCoordinator with distributed execution capabilities using round-robin
    task distribution. Provides a simple, tight interface focused on the most common
    fleet operations.

    Core Methods:
        - submit(): Execute method on next available resource (round-robin)
        - distribute(): Distribute N jobs across available workers (N can be != fleet size)
        - cancel_all(): Cancel all pending operations

    Examples:
        ```python
        class Worker(SyncResource):
            def process(self, data: str) -> str:
                return f"processed: {data}"

        class Service(SyncResource):
            fleet = AttachFleet([
                WorkerSpec(name="worker-1"),
                WorkerSpec(name="worker-2"),
                WorkerSpec(name="worker-3"),
            ])

            def process_single(self, item: str) -> str:
                # Execute on next available worker
                future = self.fleet.submit(Worker.process, item)
                return future.result()

            def process_batch(self, items: list[str]) -> list[str]:
                # Distribute jobs across workers using round-robin
                args_list = [(item,) for item in items]
                futures = self.fleet.distribute(Worker.process, args_list)
                return [f.result() for f in futures]
        ```

    Thread Safety:
        All methods are thread-safe and can be called concurrently from multiple threads.
        Uses RLock for reentrant safety and minimal lock scope for optimal performance.
    """

    def __init__(self, resources: list[ResourceType]) -> None:
        """
        Initialize fleet coordinator with resources.

        Args:
            resources: List of resource instances to manage

        Raises:
            AttachError: If resources list is empty (inherited from ListCoordinator)
        """
        super().__init__(resources)
        self._executor = ThreadPoolExecutor(max_workers=len(resources))
        self._lock = threading.RLock()
        self._pending_futures: set[Future] = set()
        self._next_resource_index = 0

    @property
    def pending_count(self) -> int:
        """
        Get the number of currently pending operations.

        Returns:
            Number of futures that are still running or pending

        Examples:
            ```python
            print(f"Active operations: {fleet.pending_count}")
            ```
        """
        with self._lock:
            return len(self._pending_futures)

    def submit(self, method: Callable, *args, **kwargs) -> Future[Any]:
        """
        Execute method on next available resource using round-robin selection.

        Thread-safe method that distributes load evenly across all resources in the fleet.
        Uses atomic round-robin selection to ensure fair distribution under concurrent access.

        Args:
            method: Method to execute (bound or unbound method)
            *args: Arguments for method
            **kwargs: Keyword arguments for method

        Returns:
            Future object for result

        Examples:
            ```python
            # Execute on next available worker
            future = fleet.submit(Worker.process, "some_data")
            result = future.result()

            # With keyword arguments
            future = fleet.submit(Worker.process, "data", timeout=30)
            ```

        Thread Safety:
            Safe for concurrent calls from multiple threads. Resource selection
            and index increment are atomic operations.
        """
        # Atomic resource selection with round-robin
        with self._lock:
            resource = self._resources[self._next_resource_index % len(self._resources)]
            self._next_resource_index += 1

        return self._submit_to_resource(resource, method, *args, **kwargs)

    def distribute(
        self,
        method: Callable,
        args_list: list[tuple[Any, ...]] | None = None,
        kwargs_list: list[dict[str, Any]] | None = None,
    ) -> list[Future[Any]]:
        """
        Distribute N jobs across available workers using round-robin (N can be != fleet size).

        This method handles the common case where you have a variable number of jobs
        that need to be distributed across your fleet of workers. Jobs are distributed
        using round-robin scheduling for optimal load balancing.

        Args:
            method: Method to execute on each job
            args_list: List of argument tuples for each job
            kwargs_list: Optional list of keyword arguments for each job

        Returns:
            List of Future objects for results (one per job)

        Raises:
            ValueError: If kwargs_list is provided but has different length than args_list

        Examples:
            ```python
            # 3 workers, 7 jobs - workers get multiple jobs via round-robin
            args_list = [("data1",), ("data2",), ("data3,"), ("data4",), ("data5",)]
            futures = fleet.distribute(Worker.process, args_list)
            results = [f.result() for f in futures]

            # With kwargs (must match args_list length)
            args_list = [("data1",), ("data2",), ("data3",)]
            kwargs_list = [{"timeout": 10}, {"timeout": 20}, {"timeout": 30}]
            futures = fleet.distribute(Worker.process, args_list, kwargs_list)

            # No arguments - useful for initialization tasks
            futures = fleet.distribute(Worker.initialize)
            ```

        Thread Safety:
            Safe for concurrent calls. Each job submission is atomic and thread-safe.
        """
        if args_list is None and kwargs_list is None:
            return []

        if args_list is None:
            args_list = [() for _ in range(len(kwargs_list or []))]

        if kwargs_list is None:
            kwargs_list = [{} for _ in range(len(args_list))]

        if len(kwargs_list) != len(args_list):
            raise ValueError(
                f"kwargs_list length ({len(kwargs_list)}) must match "
                f"args_list length ({len(args_list)})"
            )

        futures: list[Future[Any]] = []

        # Distribute jobs across workers using round-robin
        for i, (job_args, job_kwargs) in enumerate(zip(args_list, kwargs_list)):
            # Atomic resource selection
            with self._lock:
                worker_index = (self._next_resource_index + i) % len(self._resources)

            resource = self._resources[worker_index]
            future = self._submit_to_resource(resource, method, *job_args, **job_kwargs)
            futures.append(future)

        # Update round-robin counter atomically
        with self._lock:
            self._next_resource_index += len(args_list)

        return futures

    def cancel_all(self) -> None:
        """
        Cancel all pending operations.

        Attempts to cancel all currently running futures. Note that cancellation
        may not be possible for futures that have already started execution.

        Examples:
            ```python
            # Cancel all running operations
            fleet.cancel_all()
            print(f"Remaining operations: {fleet.pending_count}")
            ```

        Thread Safety:
            Safe for concurrent calls. Uses atomic operations to prevent race conditions.
        """
        with self._lock:
            pending_futures = self._pending_futures.copy()

        # Cancel outside the lock to avoid blocking other operations
        for future in pending_futures:
            future.cancel()

        # Clear the set atomically
        with self._lock:
            self._pending_futures.clear()

    def _submit_to_resource(
        self, resource: ResourceType, method: Callable, *args, **kwargs
    ) -> Future[Any]:
        """
        Submit method execution to a specific resource.

        Handles both bound and unbound methods with proper error propagation
        and automatic cleanup of completed futures.

        Args:
            resource: Resource to execute method on
            method: Method to execute (bound or unbound)
            *args: Arguments for method
            **kwargs: Keyword arguments for method

        Returns:
            Future object for result

        Raises:
            TypeError: If method is not a valid method type
        """

        def execute():
            try:
                if not inspect.ismethod(method):
                    raise TypeError(
                        f"{method} is not a method, must be a bound method to a loomi resource"
                    )

                remote_method = getattr(resource, method.__name__)
                return remote_method(*args, **kwargs)
            except Exception as e:
                # In production, might want more sophisticated error handling
                raise e

        future = self._executor.submit(execute)

        # Track pending futures for cancellation (atomic operation)
        with self._lock:
            self._pending_futures.add(future)

        # Automatic cleanup when future completes
        def cleanup_future(completed_future: Future[Any]) -> None:
            """Remove completed future from tracking set."""
            with self._lock:
                self._pending_futures.discard(completed_future)

        future.add_done_callback(cleanup_future)
        return future

    def __del__(self) -> None:
        """
        Cleanup resources when coordinator is garbage collected.

        Automatically cancels pending operations and shuts down the thread pool
        to prevent resource leaks. Uses non-blocking shutdown to avoid blocking
        garbage collection.
        """
        try:
            self.cancel_all()
            self._executor.shutdown(wait=False)
        except Exception:
            # Ignore errors during cleanup to prevent issues during garbage collection
            pass

    def __repr__(self) -> str:
        """
        String representation for debugging.

        Returns:
            Detailed string showing fleet status and resource information
        """
        with self._lock:
            pending_count = len(self._pending_futures)

        resource_names = [
            getattr(r, "readable_name", getattr(r, "name", str(r))) for r in self._resources
        ]

        return (
            f"<FleetCoordinator: {len(self._resources)} resources, "
            f"{pending_count} pending, resources={resource_names}>"
        )
