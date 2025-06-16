from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

from .._protocols import WorkerPoolProtocol
from .._types import WorkerFunction

__all__ = [
    "MultiprocessingWorkerPoolProtocol",
    "TaskSubmission",
]


@dataclass
class TaskSubmission:
    """Represents a task submission for multiprocessing."""

    func: WorkerFunction
    args: tuple[Any, ...]
    kwargs: dict[str, Any]


@runtime_checkable
class MultiprocessingWorkerPoolProtocol(WorkerPoolProtocol, Protocol):
    """
    Multiprocessing worker pool protocol.
    """

    @property
    def max_workers(self) -> int:
        """Maximum number of worker processes."""
        ...
