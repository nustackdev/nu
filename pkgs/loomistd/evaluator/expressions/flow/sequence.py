"""
Sequence expression.

This module provides the Sequence expression, which executes expressions
in sequential order.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from loomi.evaluator.interface.operations import SequenceOperationProtocol
from loomi.evaluator.interface.types import ErrorBehavior
from loomi.state.interface.type_vars import StateT

from ..base import Expression

if TYPE_CHECKING:
    from ...context import Context


class Sequence(Expression[StateT]):
    """
    Executes expressions in sequential order.

    This expression runs each child expression in sequence, waiting for
    each to complete before executing the next.

    Args:
        expr: The first expression to execute
        *exprs: Additional expressions to execute in sequence
        error_behavior: How to handle errors that occur during execution
        on_fail: Expression to execute when an error occurs

    Examples:
        >>> expr1 = Function(func1)
        >>> expr2 = Function(func2)
        >>> expr3 = Function(func3)
        >>> sequence = Sequence(expr1, expr2, expr3)
    """

    def __init__(
        self,
        expr: Expression[StateT],
        /,
        *exprs: Expression[StateT],
        error_behavior: ErrorBehavior = "fail",
        on_fail: Optional[Expression[StateT]] = None,
    ):
        """
        Initialize the Sequence expression.

        Args:
            expr: The first expression to execute
            *exprs: Additional expressions to execute in sequence
            error_behavior: How to handle errors that occur during execution
            on_fail: Expression to execute when an error occurs

        Raises:
            OperationConfigError: If no expressions are provided
        """
        super().__init__(error_behavior=error_behavior, on_fail=on_fail)

        self.children = (expr,) + exprs


if TYPE_CHECKING:
    _: type[SequenceOperationProtocol[Expression, "Context"]] = Sequence
