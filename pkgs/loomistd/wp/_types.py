from __future__ import annotations

from enum import Enum
from typing import Any, Callable, Literal, TypeVar

__all__ = [
    "WorkerFunction",
    "WorkerInitFunction",
    "WorkerCleanupFunction",
    "TaskStatus",
    "WorkerPoolMode",
    "TaskT",
]

# Type variables
TaskT = TypeVar("TaskT")

# Core types
WorkerFunction = Callable[..., Any]
WorkerInitFunction = Callable[..., Any]
WorkerCleanupFunction = Callable[..., Any]
WorkerPoolMode = Literal["active", "inactive"]


class TaskStatus(Enum):
    """Status of a task in the worker pool."""

    PENDING = "pending"  # Queued but not started
    RUNNING = "running"  # Currently executing
    COMPLETED = "completed"  # Finished successfully
    FAILED = "failed"  # Finished with exception
    CANCELLED = "cancelled"  # Cancelled before/during execution
