"""
Branch expression.

This module provides the Branch expression, which conditionally executes
expressions based on the result of a condition.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Awaitable, Callable, Dict, Optional, Tuple

from loomi.evaluator.interface.operations import BranchOperationProtocol
from loomi.evaluator.interface.types import ErrorBehavior
from loomi.state.interface.type_vars import StateT

from ..base import Expression

if TYPE_CHECKING:
    from ...context import Context

# Type for branch condition values
BranchConditionValue = str | bool | int | float | None


class Branch(Expression[StateT]):
    """
    Conditionally executes expressions based on a condition.

    This expression evaluates a condition and executes the expression
    corresponding to the condition's result value. The condition can be
    specified as a function or as a path to a value in the state.

    Args:
        exprs: Dictionary mapping condition values to expressions
        condition: Function that returns a condition value
        condition_path: Path to a value in the state to use as condition
        error_behavior: How to handle errors that occur during execution
        on_fail: Expression to execute when an error occurs

    Examples:
        >>> branch = Branch(
        ...     {
        ...         True: Function(handle_true),
        ...         False: Function(handle_false),
        ...         "other": Function(handle_other),
        ...     },
        ...     condition=lambda ctx: ctx.scope.get("flag"),
        ... )
    """

    def __init__(
        self,
        exprs: Dict[BranchConditionValue, Expression[StateT]],
        /,
        *,
        condition: Optional[Callable[[Context[StateT]], Awaitable[Any] | Any]] = None,
        condition_path: Optional[Tuple[str, ...] | str] = None,
        error_behavior: ErrorBehavior = "fail",
        on_fail: Optional[Expression[StateT]] = None,
    ):
        """
        Initialize the Branch expression.

        Args:
            exprs: Dictionary mapping condition values to expressions
            condition: Function that returns a condition value
            condition_path: Path to a value in the state to use as condition
            error_behavior: How to handle errors that occur during execution
            on_fail: Expression to execute when an error occurs

        Raises:
            ValueError: If both condition and condition_path are None, or if exprs is empty
        """
        super().__init__(error_behavior=error_behavior, on_fail=on_fail)

        if not exprs:
            raise ValueError("At least one expression must be provided in the exprs dictionary")

        if condition is None and condition_path is None:
            raise ValueError("Either condition or condition_path must be provided")

        self._exprs = exprs
        self._condition = condition

        # Normalize condition_path to tuple if string
        if isinstance(condition_path, str):
            self._condition_path = (condition_path,)
        else:
            self._condition_path = condition_path

        # Set child expressions
        self.children = tuple(exprs.values())

    @property
    def branch_exprs(self) -> Dict[BranchConditionValue, Expression[StateT]]:
        """
        Get the branch expressions dictionary.

        Returns:
            Dictionary mapping condition values to expressions
        """
        return self._exprs

    @property
    def condition(self) -> Optional[Callable[[Context[StateT]], Awaitable[Any] | Any]]:
        """
        Get the condition function.

        Returns:
            The condition function or None if using condition_path
        """
        return self._condition

    @property
    def condition_path(self) -> Optional[Tuple[str, ...]]:
        """
        Get the condition path.

        Returns:
            Tuple representing the path to the condition value or None if using condition
        """
        return self._condition_path


if TYPE_CHECKING:
    _: type[BranchOperationProtocol[Expression, "Context"]] = Branch
