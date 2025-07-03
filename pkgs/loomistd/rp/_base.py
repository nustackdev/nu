from __future__ import annotations

from abc import ABC, abstractmethod
from typing import final

from .exceptions import WorkerPoolConnectionError

__all__ = [
    "BaseWorkerPool",
]


class BaseWorkerPool(ABC):
    """Base class for worker pool implementations."""

    def setup(self) -> None:
        """Initialize the worker pool."""
        self._connected = False
        self._workers = []
        self._resources = []
        self.connect()

    def cleanup(self) -> None:
        """Clean up the worker pool."""
        self.disconnect()

    @property
    def workers(self) -> list:
        """List of workers in the pool."""
        self._ensure_connected()
        return self._workers

    @property
    def resources(self) -> list:
        """List of resources in the pool."""
        self._ensure_connected()
        return self._resources

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

    @property
    @abstractmethod
    def worker_count(self) -> int:
        """Number of workers in the pool."""
        ...
