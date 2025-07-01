from __future__ import annotations

__all__ = [
    "WorkerPoolError",
    "WorkerPoolConnectionError",
    "WorkerPoolOperationError",
    "TaskError",
    "TaskCancellationError",
]


class WorkerPoolError(Exception):
    """Base exception for worker pool errors."""

    pass


class WorkerPoolConnectionError(WorkerPoolError):
    """Raised when worker pool connection fails."""

    pass


class WorkerPoolOperationError(WorkerPoolError):
    """Raised when worker pool operation fails."""

    pass


class TaskError(WorkerPoolError):
    """Base exception for task-related errors."""

    pass


class TaskCancellationError(TaskError):
    """Raised when accessing result of cancelled task."""

    pass
