"""
Retry operation.

This module provides the Retry operation, which attempts to execute
an operation multiple times with configurable backoff.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional, Type

from loomi.evaluator.interface.operations import RetryOperationProtocol
from loomi.evaluator.interface.types import ErrorBehavior
from loomi.state.interface.type_vars import StateT

from ..base import Operation

if TYPE_CHECKING:
    from ...context import Context


class Retry(Operation[StateT]):
    """
    Retries an operation with configurable backoff.

    This operation attempts to execute a child operation multiple times,
    with exponential backoff between attempts. It can be configured to
    retry only on specific exception types.

    Args:
        op: The operation to retry
        max_attempts: Maximum number of attempts (including the first)
        backoff_factor: Factor to multiply delay by after each failure
        initial_delay: Initial delay in seconds before first retry
        max_delay: Maximum delay in seconds between retries
        retry_on: Exception types to retry on (None means retry on any exception)
        error_behavior: How to handle errors after all retries fail
        on_fail: Operation to execute when all retries fail

    Examples:
        >>> # Retry a network operation with exponential backoff
        >>> retry_op = Retry(
        ...     Function(network_request),
        ...     max_attempts=5,
        ...     backoff_factor=2.0,
        ...     initial_delay=1.0,
        ...     retry_on=[NetworkError, TimeoutError]
        ... )
    """

    def __init__(
        self,
        op: Operation[StateT],
        /,
        *,
        max_attempts: int = 3,
        backoff_factor: float = 2.0,
        initial_delay: float = 1.0,
        max_delay: float = 30.0,
        retry_on: Optional[List[Type[Exception]]] = None,
        error_behavior: ErrorBehavior = "fail",
        on_fail: Optional[Operation[StateT]] = None,
    ):
        """
        Initialize the Retry operation.

        Args:
            op: The operation to retry
            max_attempts: Maximum number of attempts (including the first)
            backoff_factor: Factor to multiply delay by after each failure
            initial_delay: Initial delay in seconds before first retry
            max_delay: Maximum delay in seconds between retries
            retry_on: Exception types to retry on (None means retry on any exception)
            error_behavior: How to handle errors after all retries fail
            on_fail: Operation to execute when all retries fail

        Raises:
            ValueError: If max_attempts is less than 1 or other parameters are invalid
        """
        super().__init__(error_behavior=error_behavior, on_fail=on_fail)

        if max_attempts < 1:
            raise ValueError(f"max_attempts must be at least 1, got {max_attempts}")
        if backoff_factor <= 0:
            raise ValueError(f"backoff_factor must be positive, got {backoff_factor}")
        if initial_delay < 0:
            raise ValueError(f"initial_delay must be non-negative, got {initial_delay}")
        if max_delay < initial_delay:
            raise ValueError("max_delay must be greater than or equal to initial_delay")

        self._op = op
        self._max_attempts = max_attempts
        self._backoff_factor = backoff_factor
        self._initial_delay = initial_delay
        self._max_delay = max_delay
        self._retry_on = retry_on

        # Set child operation
        self.children = (op,)

    @property
    def retry_op(self) -> Operation[StateT]:
        """
        Get the operation to retry.

        Returns:
            The operation to retry
        """
        return self._op

    @property
    def max_attempts(self) -> int:
        """
        Get the maximum number of attempts.

        Returns:
            The maximum number of attempts
        """
        return self._max_attempts

    @property
    def backoff_factor(self) -> float:
        """
        Get the backoff factor.

        Returns:
            The backoff factor
        """
        return self._backoff_factor

    @property
    def initial_delay(self) -> float:
        """
        Get the initial delay in seconds.

        Returns:
            The initial delay
        """
        return self._initial_delay

    @property
    def max_delay(self) -> float:
        """
        Get the maximum delay in seconds.

        Returns:
            The maximum delay
        """
        return self._max_delay

    @property
    def retry_on(self) -> Optional[List[Type[Exception]]]:
        """
        Get the exception types to retry on.

        Returns:
            The exception types or None if retrying on any exception
        """
        return self._retry_on


if TYPE_CHECKING:
    _: type[RetryOperationProtocol[Operation, "Context"]] = Retry
