"""
Loop operation.

This module provides the Loop operation, which repeatedly executes
an operation while a condition is true or until a maximum number
of iterations is reached.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Awaitable, Callable, Optional, Tuple

from loomi.evaluator.interface.operations import LoopOperationProtocol
from loomi.evaluator.interface.types import ErrorBehavior
from loomi.state.interface.type_vars import StateT

from ..base import Operation

if TYPE_CHECKING:
    from ...context import Context


class Loop(Operation[StateT]):
    """
    Repeatedly executes an operation while a condition is true.

    This operation runs a child operation repeatedly until a condition
    becomes false or a maximum number of iterations is reached. The
    condition can be specified as a function or as a path to a value
    in the state.

    Args:
        op: The operation to execute repeatedly
        condition: Function that returns a boolean indicating whether to continue
        condition_path: Path to a boolean value in the state
        max_iterations: Maximum number of iterations (None means no limit)
        on_finish: Operation to execute after all iterations are complete
        error_behavior: How to handle errors that occur during execution
        on_fail: Operation to execute when an error occurs

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
        op: Operation[StateT],
        /,
        *,
        condition: Optional[Callable[[Context[StateT]], Awaitable[bool] | bool]] = None,
        condition_path: Optional[Tuple[str, ...] | str] = None,
        max_iterations: Optional[int] = None,
        on_finish: Optional[Operation[StateT]] = None,
        error_behavior: ErrorBehavior = "fail",
        on_fail: Optional[Operation[StateT]] = None,
    ):
        """
        Initialize the Loop operation.

        Args:
            op: The operation to execute repeatedly
            condition: Function that returns a boolean indicating whether to continue
            condition_path: Path to a boolean value in the state
            max_iterations: Maximum number of iterations (None means no limit)
            on_finish: Operation to execute after all iterations are complete
            error_behavior: How to handle errors that occur during execution
            on_fail: Operation to execute when an error occurs

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

        self._op = op
        self._condition = condition

        # Normalize condition_path to tuple if string
        if isinstance(condition_path, str):
            self._condition_path = (condition_path,)
        else:
            self._condition_path = condition_path

        self._max_iterations = max_iterations
        self._on_finish = on_finish

        # Set child operations - main operation and optional on_finish
        children = [op]
        if on_finish:
            children.append(on_finish)
        self.children = tuple(children)

    @property
    def loop_op(self) -> Operation[StateT]:
        """
        Get the operation to execute in the loop.

        Returns:
            The operation to execute repeatedly
        """
        return self._op

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
    def on_finish(self) -> Optional[Operation[StateT]]:
        """
        Get the operation to execute after all iterations are complete.

        Returns:
            The on_finish operation or None if not specified
        """
        return self._on_finish


if TYPE_CHECKING:
    _: type[LoopOperationProtocol[Operation, "Context"]] = Loop
