"""
Loop expression.

This module provides the Loop expression, which repeatedly executes
an expression while a condition is true or until a maximum number
of iterations is reached.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Awaitable, Callable, Optional, Tuple

from loomi.evaluator.interface.operations import LoopOperationProtocol
from loomi.evaluator.interface.types import ErrorBehavior
from loomi.state.interface.type_vars import StateT

from ..base import Expression

if TYPE_CHECKING:
    from ...context import Context


class Loop(Expression[StateT]):
    """
    Repeatedly executes an expression while a condition is true.

    This expression runs a child expression repeatedly until a condition
    becomes false or a maximum number of iterations is reached. The
    condition can be specified as a function or as a path to a value
    in the state.

    Args:
        expr: The expression to execute repeatedly
        condition: Function that returns a boolean indicating whether to continue
        condition_path: Path to a boolean value in the state
        max_iterations: Maximum number of iterations (None means no limit)
        on_finish: Expression to execute after all iterations are complete
        error_behavior: How to handle errors that occur during execution
        on_fail: Expression to execute when an error occurs

    Examples:
        >>> # Loop with condition function
        >>> loop = Loop(
        ...     Function(process_item),
        ...     condition=lambda ctx: ctx.scope.get("has_more_items", False),
        ...     max_iterations=100,
        ... )
        >>>
        >>> # Loop with condition path
        >>> loop = Loop(
        ...     Function(process_item),
        ...     condition_path=("queue", "has_more_items"),
        ...     on_finish=Function(finalize),
        ... )
    """

    def __init__(
        self,
        expr: Expression[StateT],
        /,
        *,
        condition: Optional[Callable[[Context[StateT]], Awaitable[bool] | bool]] = None,
        condition_path: Optional[Tuple[str, ...] | str] = None,
        max_iterations: Optional[int] = None,
        on_finish: Optional[Expression[StateT]] = None,
        error_behavior: ErrorBehavior = "fail",
        on_fail: Optional[Expression[StateT]] = None,
    ):
        """
        Initialize the Loop expression.

        Args:
            expr: The expression to execute repeatedly
            condition: Function that returns a boolean indicating whether to continue
            condition_path: Path to a boolean value in the state
            max_iterations: Maximum number of iterations (None means no limit)
            on_finish: Expression to execute after all iterations are complete
            error_behavior: How to handle errors that occur during execution
            on_fail: Expression to execute when an error occurs

        Raises:
            ValueError: If both condition and condition_path are None and max_iterations is None
        """
        super().__init__(error_behavior=error_behavior, on_fail=on_fail)

        if condition is None and condition_path is None and max_iterations is None:
            raise ValueError(
                "At least one of condition, condition_path, or max_iterations must be provided"
            )

        if max_iterations is not None and max_iterations <= 0:
            raise ValueError(f"Invalid max_iterations: {max_iterations}. Must be > 0")

        self._expr = expr
        self._condition = condition

        # Normalize condition_path to tuple if string
        if isinstance(condition_path, str):
            self._condition_path = (condition_path,)
        else:
            self._condition_path = condition_path

        self._max_iterations = max_iterations
        self._on_finish = on_finish

        # Set child expressions - main expression and optional on_finish
        children = [expr]
        if on_finish:
            children.append(on_finish)
        self.children = tuple(children)

    @property
    def loop_expr(self) -> Expression[StateT]:
        """
        Get the expression to execute in the loop.

        Returns:
            The expression to execute repeatedly
        """
        return self._expr

    @property
    def condition(self) -> Optional[Callable[[Context[StateT]], Awaitable[bool] | bool]]:
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

    @property
    def max_iterations(self) -> Optional[int]:
        """
        Get the maximum number of iterations.

        Returns:
            Maximum number of iterations or None for no limit
        """
        return self._max_iterations

    @property
    def on_finish(self) -> Optional[Expression[StateT]]:
        """
        Get the expression to execute after all iterations are complete.

        Returns:
            The on_finish expression or None if not specified
        """
        return self._on_finish


if TYPE_CHECKING:
    _: type[LoopOperationProtocol[Expression, "Context"]] = Loop
