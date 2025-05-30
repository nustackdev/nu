"""
Timeout operation.

This module provides the Timeout operation, which adds a timeout
constraint to an operation's execution.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from loomi.interfaces.executor.operations import TimeoutOperationProtocol
from loomi.interfaces.executor.types import ErrorBehavior
from loomi.interfaces.state.type_vars import StateT

from ..base import Operation

if TYPE_CHECKING:
    from ...context import Context


class Timeout(Operation[StateT]):
    """
    Adds a timeout constraint to an operation.

    This operation executes a child operation with a timeout constraint,
    cancelling it if execution exceeds the specified timeout duration.
    Optionally executes an on_timeout operation if the timeout is reached.

    Args:
        op: The operation to execute with a timeout
        timeout: Timeout duration in seconds
        on_timeout: Operation to execute if the timeout is reached
        error_behavior: How to handle errors that occur during execution
        on_fail: Operation to execute when an error occurs

    Examples:
        >>> # Execute with a 5-second timeout
        >>> timeout_op = Timeout(
        ...     Function(long_running_task),
        ...     timeout=5.0,
        ...     on_timeout=Function(handle_timeout)
        ... )
    """

    def __init__(
        self,
        op: Operation[StateT],
        /,
        *,
        timeout: float = 30.0,
        on_timeout: Optional[Operation[StateT]] = None,
        error_behavior: ErrorBehavior = "fail",
        on_fail: Optional[Operation[StateT]] = None,
    ):
        """
        Initialize the Timeout operation.

        Args:
            op: The operation to execute with a timeout
            timeout: Timeout duration in seconds
            on_timeout: Operation to execute if the timeout is reached
            error_behavior: How to handle errors that occur during execution
            on_fail: Operation to execute when an error occurs

        Raises:
            ValueError: If timeout is not positive
        """
        super().__init__(error_behavior=error_behavior, on_fail=on_fail)

        if timeout <= 0:
            raise ValueError(f"Timeout must be positive, got {timeout}")

        self._op = op
        self._timeout = timeout
        self._on_timeout = on_timeout

        # Set child operations
        children = [op]
        if on_timeout:
            children.append(on_timeout)
        self.children = tuple(children)

    @property
    def timeout_op(self) -> Operation[StateT]:
        """
        Get the operation to execute with a timeout.

        Returns:
            The operation to execute
        """
        return self._op

    @property
    def timeout(self) -> float:
        """
        Get the timeout duration in seconds.

        Returns:
            The timeout duration
        """
        return self._timeout

    @property
    def on_timeout(self) -> Optional[Operation[StateT]]:
        """
        Get the operation to execute if the timeout is reached.

        Returns:
            The on_timeout operation or None if not specified
        """
        return self._on_timeout


if TYPE_CHECKING:
    _: type[TimeoutOperationProtocol[Operation, "Context"]] = Timeout
