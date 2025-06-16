"""
Delay expression.

This module provides the Delay expression, which introduces a delay
before or after executing an expression.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Awaitable, Callable, Optional, Tuple, Union

from loomi.interfaces.executor.operations import DelayOperationProtocol
from loomi.interfaces.executor.types import ErrorBehavior
from loomi.interfaces.state.type_vars import StateT

from ..base import Expression

if TYPE_CHECKING:
    from ...context import Context


class Delay(Expression[StateT]):
    """
    Introduces a delay in the execution flow.

    This expression pauses execution for a specified duration. The delay
    can be a fixed value, derived from a function, or from a state path.

    Args:
        delay: Fixed delay in seconds, or function that returns the delay
        delay_path: Path to a value in the state to use as delay
        error_behavior: How to handle errors that occur during execution
        on_fail: Expression to execute when an error occurs

    Examples:
        >>> # Fixed delay of 2 seconds
        >>> delay_expr = Delay(2.0)
        >>>
        >>> # Dynamic delay from a function
        >>> delay_expr = Delay(lambda ctx: random.uniform(1.0, 5.0))
        >>>
        >>> # Delay from state path
        >>> delay_expr = Delay(delay_path=("config", "retry_delay"))
    """

    def __init__(
        self,
        delay: Optional[Union[float, Callable[[Context[StateT]], Awaitable[float] | float]]] = None,
        *,
        delay_path: Optional[Union[Tuple[str, ...], str]] = None,
        error_behavior: ErrorBehavior = "fail",
        on_fail: Optional[Expression[StateT]] = None,
    ):
        """
        Initialize the Delay expression.

        Args:
            delay: Fixed delay in seconds, or function that returns the delay
            delay_path: Path to a value in the state to use as delay
            error_behavior: How to handle errors that occur during execution
            on_fail: Expression to execute when an error occurs

        Raises:
            ValueError: If both delay and delay_path are None, or if delay is negative
        """
        super().__init__(error_behavior=error_behavior, on_fail=on_fail)

        if delay is None and delay_path is None:
            raise ValueError("Either delay or delay_path must be provided")

        if isinstance(delay, (int, float)) and delay < 0:
            raise ValueError(f"Delay must be non-negative, got {delay}")

        self._delay = delay

        # Normalize delay_path to tuple if string
        if isinstance(delay_path, str):
            self._delay_path = (delay_path,)
        else:
            self._delay_path = delay_path

    @property
    def delay(
        self,
    ) -> Optional[Union[float, Callable[[Context[StateT]], Awaitable[float] | float]]]:
        """
        Get the delay value or function.

        Returns:
            The delay value, function, or None if using delay_path
        """
        return self._delay

    @property
    def delay_path(self) -> Optional[Tuple[str, ...]]:
        """
        Get the delay path.

        Returns:
            Tuple representing the path to the delay value or None if using delay
        """
        return self._delay_path


if TYPE_CHECKING:
    _: type[DelayOperationProtocol[Expression, "Context"]] = Delay
