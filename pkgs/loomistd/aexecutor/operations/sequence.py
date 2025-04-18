"""
Sequence operation.

This module provides the Sequence operation, which executes operations
in sequential order.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from loomi.interfaces.executor.operations import SequenceOperationProtocol
from loomi.interfaces.executor.types import ErrorBehavior
from loomi.interfaces.state.type_vars import StateDictT

from .base import Operation

if TYPE_CHECKING:
    from ..context.context import Context


class Sequence(Operation[StateDictT]):
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
        op: Operation[StateDictT],
        /,
        *ops: Operation[StateDictT],
        error_behavior: ErrorBehavior = "fail",
        on_fail: Operation[StateDictT] | None = None,
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

        self.children = (op,) + ops


if TYPE_CHECKING:
    _: type[SequenceOperationProtocol[Operation, "Context"]] = Sequence
