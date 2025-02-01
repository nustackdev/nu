"""Runtime system protocol definitions."""

from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from scriptable.app.base import AppAsyncBase


@runtime_checkable
class OperationAsyncProtocol(Protocol):
    """Protocol defining executable operations."""

    @abstractmethod
    async def execute(self, app: "AppAsyncBase") -> None:
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
