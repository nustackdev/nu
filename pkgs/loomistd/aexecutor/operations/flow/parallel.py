"""
Parallel operation.

This module provides the Parallel operation, which executes multiple operations
concurrently with configurable concurrency limits.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from loomi.evaluator.interface.operations import ParallelOperationProtocol
from loomi.evaluator.interface.types import ErrorBehavior
from loomi.state.interface.type_vars import StateT

from ..base import Operation

if TYPE_CHECKING:
    from ...context import Context


class Parallel(Operation[StateT]):
    """
    Executes operations concurrently.

    This operation runs child operations in parallel, with configurable
    maximum concurrency. When max_concurrency is 1, it behaves like
    a Sequence. When negative, it runs all operations with no limit.

    Args:
        op: The first operation to execute
        *ops: Additional operations to execute in parallel
        max_concurrency: Maximum number of concurrent operations
            - 1 means sequential execution (same as Sequence)
            - >1 means limit to N concurrent operations
            - -1 or 0 means unlimited concurrency
        error_behavior: How to handle errors that occur during execution
        on_fail: Operation to execute when an error occurs

    Examples:
        >>> op1 = Function(func1)
        >>> op2 = Function(func2)
        >>> op3 = Function(func3)
        >>> parallel = Parallel(op1, op2, op3, max_concurrency=2)
    """

    def __init__(
        self,
        op: Operation[StateT],
        /,
        *ops: Operation[StateT],
        max_concurrency: int = -1,
        error_behavior: ErrorBehavior = "fail",
        on_fail: Operation[StateT] | None = None,
    ):
        """
        Initialize the Parallel operation.

        Args:
            op: The first operation to execute
            *ops: Additional operations to execute in parallel
            max_concurrency: Maximum number of concurrent operations
                - 1 means sequential execution (same as Sequence)
                - >1 means limit to N concurrent operations
                - -1 or 0 means unlimited concurrency
            error_behavior: How to handle errors that occur during execution
            on_fail: Operation to execute when an error occurs

        Raises:
            ValueError: If max_concurrency is invalid
        """
        super().__init__(error_behavior=error_behavior, on_fail=on_fail)

        # Validate max_concurrency
        if max_concurrency < -1:
            raise ValueError(f"Invalid max_concurrency: {max_concurrency}. Must be >= -1")

        self._max_concurrency = max_concurrency
        self.children = (op,) + ops

    @property
    def max_concurrency(self) -> int:
        """
        Get the maximum number of concurrent operations.

        Returns:
            The maximum number of concurrent operations
        """
        return self._max_concurrency


if TYPE_CHECKING:
    _: type[ParallelOperationProtocol[Operation, "Context"]] = Parallel
