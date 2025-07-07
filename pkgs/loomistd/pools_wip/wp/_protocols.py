from __future__ import annotations

from typing import Any, Protocol

from ._types import TaskStatus, WorkerFunction

__all__ = [
    "TaskProtocol",
    "WorkerPoolProtocol",
]


class TaskProtocol(Protocol):
    """Protocol for task objects returned by worker pools."""

    def get(self) -> Any:
        """
        Get the result of this task, blocking until complete.

        Returns:
            The task result value

        Raises:
            TaskCancellationError: If task was cancelled
            Any exception raised by the task function
        """
        ...

    def cancel(self) -> bool:
        """
        Attempt to cancel this task.

        Returns:
            True if cancellation was successful, False otherwise

        Note:
            Cancellation is best-effort. Already running tasks may not be cancellable.
        """
        ...

    def is_done(self) -> bool:
        """
        Check if task is complete (success, failure, or cancelled).

        Returns:
            True if task is finished, False if still pending/running
        """
        ...

    def is_cancelled(self) -> bool:
        """
        Check if task was cancelled.

        Returns:
            True if task was cancelled, False otherwise
        """
        ...

    @property
    def status(self) -> TaskStatus:
        """Current status of the task."""
        ...


class WorkerPoolProtocol(Protocol):
    """Protocol for worker pool implementations."""

    def submit(self, func: WorkerFunction, *args: Any, **kwargs: Any) -> TaskProtocol:
        """
        Submit a function for execution.

        Args:
            func: Function to execute
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function

        Returns:
            Task object representing the pending execution

        Raises:
            WorkerPoolError: If submission fails
        """
        ...

    def connect(self) -> None:
        """
        Connect to the worker pool backend and start workers.

        Raises:
            WorkerPoolConnectionError: If connection/startup fails
        """
        ...

    def disconnect(self) -> None:
        """
        Disconnect from worker pool and clean up resources.

        This will attempt to complete running tasks and clean shutdown.
        """
        ...

    @property
    def is_connected(self) -> bool:
        """True if worker pool is connected and ready."""
        ...

    @property
    def worker_count(self) -> int:
        """Number of worker processes/threads."""
        ...
