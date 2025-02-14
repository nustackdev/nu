from __future__ import annotations

from typing import Any, Callable

from loomi.app.base import AsyncApp
from loomi.app.lib.operations.ops_async import (
    FunctionOperation,
    ParallelOperation,
    RepeatOperation,
    SequenceOperation,
)

from .base import AppCommonTasks
from .protocols import AsyncOperationProtocol

__all__ = [
    "AsyncAppTasks",
]


class AsyncAppTasks(AppCommonTasks, AsyncApp):
    """
    Service feature implementing operation capabilities.
    """

    async def execute(
        self,
        operation: AsyncOperationProtocol,
    ) -> Any:
        """Execute operation."""

        return await operation.execute(self)

    def function(self, func: Callable, *, name: str | None = None) -> AsyncOperationProtocol:
        """Create function operation."""
        return FunctionOperation(func, name=name)

    def sequence(
        self, *operations: AsyncOperationProtocol, delay: float = 0, continue_on_error: bool = False
    ) -> AsyncOperationProtocol:
        """Create function operation."""
        return SequenceOperation(*operations, delay=delay, continue_on_error=continue_on_error)

    def repeat(
        self,
        operation: AsyncOperationProtocol,
        times: int | None = None,
        while_key: str | tuple[str, ...] | None = None,
        max_iterations: int | None = None,
        delay: float = 0,
        ignore_errors: bool = False,
    ) -> AsyncOperationProtocol:
        """Create repeat operation."""
        return RepeatOperation(
            operation=operation,
            times=times,
            while_key=while_key,
            max_iterations=max_iterations,
            delay=delay,
            ignore_errors=ignore_errors,
        )

    def parallel(
        self,
        *operations: AsyncOperationProtocol,
        max_concurrent: int | None = None,
        timeout: float | None = None,
        ignore_errors: bool = False,
    ) -> AsyncOperationProtocol:
        """Create parallel operation."""
        return ParallelOperation(
            *operations,
            max_concurrent=max_concurrent,
            timeout=timeout,
            ignore_errors=ignore_errors,
        )
