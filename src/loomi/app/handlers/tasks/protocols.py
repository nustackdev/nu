from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from loomi.app.base import AsyncApp, SyncApp


__all__ = [
    "AsyncOperationProtocol",
    "SyncOperationProtocol",
]


@runtime_checkable
class AsyncOperationProtocol(Protocol):
    """Protocol defining executable operations."""

    async def execute(self, app: "AsyncApp") -> None:
        """
        Execute the operation.

        Args:
            app: App instance for context

        Returns:
            Operation result

        Raises:
            OperationError: If execution fails
        """
        ...


@runtime_checkable
class SyncOperationProtocol(Protocol):
    """Protocol defining executable operations."""

    def execute(self, app: "SyncApp") -> None:
        """
        Execute the operation.

        Args:
            app: App instance for context

        Returns:
            Operation result

        Raises:
            OperationError: If execution fails
        """
        ...
