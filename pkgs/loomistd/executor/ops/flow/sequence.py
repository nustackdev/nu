"""
Sequence operation.

This module provides the Sequence operation, which executes operations
in sequential order.
"""

from __future__ import annotations

from loomi.interfaces.executor.protocols import SequenceOperationProtocol

from ...context import Context
from ...logger import logger
from ...types import error_behaviors
from ..base import Operation


class Sequence(Operation, SequenceOperationProtocol[Context]):
    """
    Executes operations in sequential order.

    This operation runs each child operation in sequence, waiting for
    each to complete before executing the next.

    Args:
        *ops: The operations to execute in sequence
        error_behavior: How to handle errors that occur during execution
        on_fail: Operation to execute when an error occurs

    Examples:
        >>> op1 = Function(func1)
        >>> op2 = Function(func2)
        >>> op3 = Function(func3)
        >>> sequence = Sequence(op1, op2, op3)
    """

    def __init__(
        self,
        op: Operation,
        /,
        *ops: Operation,
        error_behavior: error_behaviors = "fail",
        on_fail: Operation | None = None,
    ):
        """
        Initialize the Sequence operation.

        Args:
            op: The first operation to execute
            *ops: Additional operations to execute in sequence
            error_behavior: How to handle errors that occur during execution
            on_fail: Operation to execute when an error occurs

        Raises:
            OperationConfigError: If no operations are provided
        """
        super().__init__(error_behavior=error_behavior, on_fail=on_fail)

        # Store operations
        self._ops = (op,) + ops

    @property
    def children(self) -> tuple[Operation, ...]:
        """
        Get all child operations of this operation.

        Returns:
            Tuple of all operations in the sequence, plus on_fail if set
        """
        if self._on_fail:
            return self._ops + (self._on_fail,)
        return self._ops

    async def _execute(self, context: Context) -> None:
        """
        Execute each operation in sequence.

        This method waits for each operation to complete before executing
        the next. If an operation raises an exception, the sequence stops
        (unless error_behavior is "continue").

        Args:
            context: Execution context providing access to state and services
        """
        logger.debug(f"Executing sequence of {len(self._ops)} operations")

        # Execute operations in sequence
        for i, op in enumerate(self._ops):
            # Create a new context for each operation
            op_context = context.with_structural_path(str(i))

            # Execute the operation
            await op.execute(op_context)
