from __future__ import annotations

from typing import Any, Callable

from loomi.app.base import SyncApp
from loomi.app.lib.operations.ops_sync import FunctionOperation, SequenceOperation

from .base import AppCommonTasks
from .protocols import SyncOperationProtocol

__all__ = [
    "SyncAppTasks",
]


class SyncAppTasks(AppCommonTasks, SyncApp):
    """
    Service feature implementing operation capabilities.
    """

    async def execute(
        self,
        operation: SyncOperationProtocol,
    ) -> Any:
        """Execute operation."""

        return operation.execute(self)

    def function(self, func: Callable, *, name: str | None = None) -> SyncOperationProtocol:
        """Create function operation."""
        return FunctionOperation(func, name=name)

    def sequence(
        self, *operations: SyncOperationProtocol, delay: float = 0, continue_on_error: bool = False
    ) -> SyncOperationProtocol:
        """Create function operation."""
        return SequenceOperation(*operations, delay=delay, continue_on_error=continue_on_error)

    # def repeat(
    #     self,
    #     operation: SyncOperationProtocol,
    #     times: int | None = None,
    #     while_key: str | tuple[str, ...] | None = None,
    #     max_iterations: int | None = None,
    #     delay: float = 0,
    #     ignore_errors: bool = False,
    # ) -> SyncOperationProtocol:
    #     """Create repeat operation."""
    #     return RepeatOperation(
    #         operation=operation,
    #         times=times,
    #         while_key=while_key,
    #         max_iterations=max_iterations,
    #         delay=delay,
    #         ignore_errors=ignore_errors,
    #     )

    # def parallel(
    #     self,
    #     *operations: SyncOperationProtocol,
    #     max_concurrent: int | None = None,
    #     timeout: float | None = None,
    #     ignore_errors: bool = False,
    # ) -> SyncOperationProtocol:
    #     """Create parallel operation."""
    #     return ParallelOperation(
    #         *operations,
    #         max_concurrent=max_concurrent,
    #         timeout=timeout,
    #         ignore_errors=ignore_errors,
    #     )
