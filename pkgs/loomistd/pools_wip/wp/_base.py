from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, final

from ._exceptions import WorkerPoolConnectionError, WorkerPoolOperationError
from ._protocols import TaskProtocol
from ._types import TaskStatus, WorkerFunction

__all__ = [
    "BaseTask",
    "BaseWorkerPool",
]


class BaseTask(ABC):
    """Base class for task implementations."""

    @abstractmethod
    def get(self) -> Any:
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


class BaseWorkerPool(ABC):
    """Base class for worker pool implementations."""

    def setup(self) -> None:
        """Initialize the worker pool."""
        self._connected = False
        self.connect()

    def cleanup(self) -> None:
        """Clean up the worker pool."""
        self.disconnect()

    @property
    def is_connected(self) -> bool:
        """True if worker pool is connected."""
        return self._connected

    def _ensure_connected(self) -> None:
        """Verify connection state."""
        if not self._connected:
            raise WorkerPoolConnectionError("Worker pool is not connected")

    # Connection Management
    @abstractmethod
    def _connect_impl(self) -> None:
        """Implementation-specific connect logic."""
        ...

    @final
    def connect(self) -> None:
        """Connect to worker pool backend."""
        if self._connected:
            return
        try:
            self._connect_impl()
            self._connected = True
        except Exception as e:
            raise WorkerPoolConnectionError(f"Failed to connect: {e}") from e

    @abstractmethod
    def _disconnect_impl(self) -> None:
        """Implementation-specific disconnect logic."""
        ...

    @final
    def disconnect(self) -> None:
        """Disconnect from worker pool."""
        if not self._connected:
            return
        try:
            self._disconnect_impl()
        finally:
            self._connected = False

    # Core Operations
    @abstractmethod
    def _submit_impl(self, func: WorkerFunction, *args: Any, **kwargs: Any) -> TaskProtocol:
        """Implementation-specific submit logic."""
        ...

    @final
    def submit(self, func: WorkerFunction, *args: Any, **kwargs: Any) -> TaskProtocol:
        """Submit function for execution."""
        self._ensure_connected()
        try:
            return self._submit_impl(func, *args, **kwargs)
        except Exception as e:
            raise WorkerPoolOperationError(f"Failed to submit task: {e}") from e

    @property
    @abstractmethod
    def worker_count(self) -> int:
        """Number of workers in the pool."""
        ...
