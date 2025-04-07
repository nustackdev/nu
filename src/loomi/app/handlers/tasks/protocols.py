from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

if TYPE_CHECKING:
    from loomi.app.base import AsyncApp, SyncApp
    from loomi.app.handlers.state.protocols_tree import AsyncStateDictProtocol


__all__ = [
    "AsyncOperationProtocol",
    "SyncOperationProtocol",
]


@runtime_checkable
class AsyncOperationProtocol(Protocol):
    """Protocol defining executable operations."""

    async def execute(self, app: "AsyncApp", loc: "AsyncStateDictProtocol") -> None:
        """
        Execute the operation.

        Args:
            app: App instance for context
            loc: Local state dictionary storage for the operation
                This is a dictionary-like object that allows for asynchronous
                operations and state management.

        Returns:
            Operation result

        Raises:
            OperationError: If execution fails
        """
        ...

    @property
    def context(self) -> dict[str, Any]:
        """
        Get the context of the operation.

        Returns:
            Context dictionary for the operation
        """
        ...

    @context.setter
    def context(self, value: dict[str, Any]) -> None:
        """
        Set the context of the operation.

        Args:
            value: Context dictionary for the operation
        """
        ...

    def update_context(self, context: dict[str, Any]) -> None:
        """
        Update the context of the operation.

        Args:
            context: Context dictionary for the operation
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
