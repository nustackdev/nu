"""Runtime system protocol definitions."""

from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, Callable, Protocol, runtime_checkable

if TYPE_CHECKING:
    from sonny.service import BaseService


@runtime_checkable
class ServiceExecutionFeatureProtocol(Protocol):
    """Protocol defining service operation capabilities."""

    async def execute(self, operation: OperationProtocol) -> None:
        """Execute operation."""
        ...

    def function(
        self,
        func: Callable,
        *,
        name: str | None = None,
    ) -> OperationProtocol:
        """Create function operation."""
        ...

    def sequence(
        self,
        *operations: OperationProtocol,
        delay: float = 0,
        continue_on_error: bool = False,
    ) -> OperationProtocol:
        """Create sequential operation."""
        ...


@runtime_checkable
class OperationProtocol(Protocol):
    """Protocol defining executable operations."""

    @abstractmethod
    async def execute(self, service: "BaseService") -> None:
        """
        Execute the operation.

        Args:
            service: Service instance for context

        Returns:
            Operation result

        Raises:
            OperationError: If execution fails
        """
        ...
