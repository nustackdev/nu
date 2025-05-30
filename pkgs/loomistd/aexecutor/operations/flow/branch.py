"""
Branch operation.

This module provides the Branch operation, which conditionally executes
operations based on the result of a condition.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Awaitable, Callable, Dict, Optional, Tuple

from loomi.interfaces.executor.operations import BranchOperationProtocol
from loomi.interfaces.executor.types import ErrorBehavior
from loomi.interfaces.state.type_vars import StateT

from ..base import Operation

if TYPE_CHECKING:
    from ...context import Context

# Type for branch condition values
BranchConditionValue = str | bool | int | float | None


class Branch(Operation[StateT]):
    """
    Conditionally executes operations based on a condition.

    This operation evaluates a condition and executes the operation
    corresponding to the condition's result value. The condition can be
    specified as a function or as a path to a value in the state.

    Args:
        ops: Dictionary mapping condition values to operations
        condition: Function that returns a condition value
        condition_path: Path to a value in the state to use as condition
        error_behavior: How to handle errors that occur during execution
        on_fail: Operation to execute when an error occurs

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
        ops: Dict[BranchConditionValue, Operation[StateT]],
        /,
        *,
        condition: Optional[Callable[[Context[StateT]], Awaitable[Any] | Any]] = None,
        condition_path: Optional[Tuple[str, ...] | str] = None,
        error_behavior: ErrorBehavior = "fail",
        on_fail: Optional[Operation[StateT]] = None,
    ):
        """
        Initialize the Branch operation.

        Args:
            ops: Dictionary mapping condition values to operations
            condition: Function that returns a condition value
            condition_path: Path to a value in the state to use as condition
            error_behavior: How to handle errors that occur during execution
            on_fail: Operation to execute when an error occurs

        Raises:
            ValueError: If both condition and condition_path are None, or if ops is empty
        """
        super().__init__(error_behavior=error_behavior, on_fail=on_fail)

        if not ops:
            raise ValueError("At least one operation must be provided in the ops dictionary")

        if condition is None and condition_path is None:
            raise ValueError("Either condition or condition_path must be provided")

        self._ops = ops
        self._condition = condition

        # Normalize condition_path to tuple if string
        if isinstance(condition_path, str):
            self._condition_path = (condition_path,)
        else:
            self._condition_path = condition_path

        # Set child operations
        self.children = tuple(ops.values())

    @property
    def branch_ops(self) -> Dict[BranchConditionValue, Operation[StateT]]:
        """
        Get the branch operations dictionary.

        Returns:
            Dictionary mapping condition values to operations
        """
        return self._ops

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
    _: type[BranchOperationProtocol[Operation, "Context"]] = Branch
