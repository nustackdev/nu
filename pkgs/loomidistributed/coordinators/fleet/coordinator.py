"""
AttachFleet - Fleet Coordinator for Distributed Execution

This module implements an AttachFleet that extends AttachMany
with execution coordination capabilities for distributed resource fleets.
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
    Coordinator for managing a fleet of resources with execution coordination.

    Extends ListCoordinator with distributed execution capabilities:
    - map(): Execute method on all resources with different arguments (1:1 mapping)
    - distribute(): Distribute N jobs across available workers (N can be != fleet size)
    - submit(): Execute method on one available resource
    - broadcast(): Execute method on all resources with same arguments
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

            def process_batch(self, items: list[str]) -> list[str]:
                # Distribute variable number of jobs across workers
                jobs = [(item,) for item in items]  # Convert to job format
                futures = self.fleet.distribute(Worker.process, jobs)
                return [f.result() for f in futures]
        ```
    """

    def __init__(self, resources: list[ResourceType]) -> None:
        """
        Initialize fleet coordinator with resources.

        Args:
            resources: List of resource instances to manage
        """
        super().__init__(resources)
        self._executor = ThreadPoolExecutor(max_workers=len(resources))
        self._lock = threading.Lock()
        self._pending_futures: set[Future] = set()

    def map(
        self, method: Callable, args_list: list[Any], kwargs_list: list[dict] | None = None
    ) -> list[Future]:
        """
        Execute method on all resources with different arguments.

        Args:
            method: Method to execute (unbound method or callable)
            args_list: List of argument tuples, one per resource
            kwargs_list: Optional list of keyword arguments, one per resource

        Returns:
            List of Future objects for results

        Raises:
            ValueError: If args_list length doesn't match resource count

        Examples:
            ```python
            # Execute different data on each worker
            futures = fleet.map(Worker.process, ["data1", "data2", "data3"])
            results = [f.result() for f in futures]

            # With kwargs
            futures = fleet.map(
                Worker.process,
                ["data1", "data2", "data3"],
                [{"timeout": 10}, {"timeout": 20}, {"timeout": 30}]
            )
            ```
        """
        if len(args_list) != len(self._resources):
            raise ValueError(
                f"args_list length ({len(args_list)}) must match resource count ({len(self._resources)})"
            )

        if kwargs_list is not None and len(kwargs_list) != len(self._resources):
            raise ValueError(
                f"kwargs_list length ({len(kwargs_list)}) must match resource count ({len(self._resources)})"
            )

        futures: list[Future] = []

        for i, resource in enumerate(self._resources):
            args = args_list[i] if isinstance(args_list[i], (tuple, list)) else (args_list[i],)
            kwargs = kwargs_list[i] if kwargs_list else {}

            future = self._submit_to_resource(resource, method, *args, **kwargs)
            futures.append(future)

        return futures

    def submit(self, method: Callable, *args, **kwargs) -> Future:
        """
        Execute method on one available resource.

        Args:
            method: Method to execute
            *args: Arguments for method
            **kwargs: Keyword arguments for method

        Returns:
            Future object for result

        Examples:
            ```python
            # Execute on any available worker
            future = fleet.submit(Worker.process, "some_data")
            result = future.result()
            ```
        """
        # Simple round-robin selection for PoC
        # In production, could use more sophisticated load balancing
        with self._lock:
            resource_index = len(self._pending_futures) % len(self._resources)
            resource = self._resources[resource_index]

        return self._submit_to_resource(resource, method, *args, **kwargs)

    def broadcast(self, method: Callable, *args, **kwargs) -> list[Future]:
        """
        Execute method on all resources with same arguments.

        Args:
            method: Method to execute
            *args: Arguments for method (same for all resources)
            **kwargs: Keyword arguments for method (same for all resources)

        Returns:
            List of Future objects for results

        Examples:
            ```python
            # Execute same operation on all workers
            futures = fleet.broadcast(Worker.initialize, config="prod")
            results = [f.result() for f in futures]
            ```
        """
        futures: list[Future] = []

        for resource in self._resources:
            future = self._submit_to_resource(resource, method, *args, **kwargs)
            futures.append(future)

        return futures

    def distribute(
        self,
        method: Callable,
        args_list: list[tuple[Any, ...]] | None = None,
        kwargs_list: list[dict[str, Any]] | None = None,
    ) -> list[Future[Any]]:
        """
        Distribute N jobs across available workers (N can be != fleet size).

        This method handles the common case where you have a variable number of jobs
        that need to be distributed across your fleet of workers. Jobs are distributed
        using round-robin scheduling.

        Args:
            method: Method to execute on each job
            args_list: List of argument tuples for each job
            kwargs_list: Optional list of keyword arguments for each job

        Returns:
            List of Future objects for results (one per job)

        Examples:
            ```python
            # 5 workers, 3 jobs - some workers idle
            args_list = [("data1",), ("data2",), ("data3",)]
            futures = fleet.distribute(Worker.process, args_list)

            # 3 workers, 7 jobs - workers get multiple args_list
            args_list = [("data1",), ("data2",), ("data3",), ("data4",), ("data5",), ("data6",), ("data7",)]
            futures = fleet.distribute(Worker.process, args_list)
            results = [f.result() for f in futures]

            # With kwargs
            args_list = [("data1",), ("data2",), ("data3",)]
            kwargs = [{"timeout": 10}, {"timeout": 20}, {"timeout": 30}]
            futures = fleet.distribute(Worker.process, args_list, kwargs)
            ```
        """
        if args_list is None and kwargs_list is None:
            return []

        if args_list is not None and kwargs_list is not None and len(kwargs_list) != len(args_list):
            raise ValueError(
                f"kwargs_list length ({len(kwargs_list)}) must match args_list length ({len(args_list)})"
            )

        futures: list[Future] = []

        jobs_args = args_list if args_list is not None else [()] * len(self._resources)
        jobs_kwargs = kwargs_list if kwargs_list is not None else [{}] * len(self._resources)
        jobs_params = zip(jobs_args, jobs_kwargs)

        # Distribute jobs across workers using round-robin
        for i, job_params in enumerate(jobs_params):
            # Select worker using round-robin
            worker_index = i % len(self._resources)
            resource = self._resources[worker_index]

            future = self._submit_to_resource(
                resource,
                method,
                *job_params[0],
                **job_params[1],
            )
            futures.append(future)

        return futures

    def cancel_all(self) -> None:
        """
        Cancel all pending operations.

        Examples:
            ```python
            fleet.cancel_all()  # Cancel all running operations
            ```
        """
        with self._lock:
            for future in self._pending_futures:
                future.cancel()
            self._pending_futures.clear()

    def shutdown(self) -> None:
        """
        Shutdown the fleet coordinator and cleanup resources.

        This should be called when the coordinator is no longer needed.
        """
        self.cancel_all()
        self._executor.shutdown(wait=True)

    def _submit_to_resource(
        self, resource: ResourceType, method: Callable, *args, **kwargs
    ) -> Future:
        """
        Submit method execution to a specific resource.

        Args:
            resource: Resource to execute method on
            method: Method to execute
            *args: Arguments for method
            **kwargs: Keyword arguments for method

        Returns:
            Future object for result
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

        # Track pending futures for cancellation
        with self._lock:
            self._pending_futures.add(future)

        # Remove from pending when done
        def cleanup_future(f):
            with self._lock:
                self._pending_futures.discard(f)

        future.add_done_callback(cleanup_future)
        return future

    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"<FleetCoordinator: {len(self._resources)} resources, {len(self._pending_futures)} pending>"
