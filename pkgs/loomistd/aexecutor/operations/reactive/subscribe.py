"""
Reactive operations.

This module provides operations that react to state changes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Tuple, Union

from loomi.interfaces.executor.operations import SubscribeOperationProtocol
from loomi.interfaces.executor.types import ErrorBehavior
from loomi.interfaces.state.type_vars import StateDictT

from ..base import Operation
from ..metadata import OperationMetadata

if TYPE_CHECKING:
    from ...context import Context

__all__ = [
    "Subscribe",
]


class Subscribe(Operation[StateDictT]):
    """
    Executes an operation when state changes occur.

    This operation monitors a path in the state store and executes the
    specified operation when changes are detected. It can be configured
    to execute only once or continuously monitor for changes.

    Args:
        op: The operation to execute when changes occur
        watch_path: Path to watch for changes
        depth: Depth of monitoring (0=exact match, 1=direct children, -1=any descendant)
        once: If True, execute once then complete
        max_concurrency: Maximum number of concurrent operation executions
        error_behavior: How to handle errors that occur during execution
        on_fail: Operation to execute when an error occurs

    Examples:
        >>> # Execute log_change when user status changes
        >>> subscribe = Subscribe(
        ...     Function(log_change),
        ...     watch_path=("users", "status"),
        ...     depth=0,
        ... )
        >>>
        >>> # Execute update_ui once when preferences change
        >>> subscribe = Subscribe(
        ...     Function(update_ui),
        ...     watch_path=("preferences"),
        ...     once=True,
        ... )
    """

    def __init__(
        self,
        op: Operation[StateDictT],
        /,
        *,
        watch_path: Union[Tuple[str, ...], str],
        depth: int = 0,
        once: bool = False,
        max_concurrency: int = 1,
        error_behavior: ErrorBehavior = "fail",
        on_fail: Optional[Operation[StateDictT]] = None,
    ):
        """
        Initialize the Subscribe operation.

        Args:
            op: The operation to execute when changes occur
            watch_path: Path to watch for changes
            depth: Depth of monitoring (0=exact match, 1=direct children, -1=any descendant)
            once: If True, execute once then complete
            max_concurrency: Maximum number of concurrent operation executions
            error_behavior: How to handle errors that occur during execution
            on_fail: Operation to execute when an error occurs

        Raises:
            ValueError: If watch_path is empty or max_concurrency is invalid
        """
        super().__init__(error_behavior=error_behavior, on_fail=on_fail)

        if not watch_path:
            raise ValueError("watch_path must be provided")

        if max_concurrency < -1:
            raise ValueError(f"Invalid max_concurrency: {max_concurrency}. Must be >= -1")

        self._op = op

        # Normalize watch_path to tuple
        if isinstance(watch_path, str):
            self._watch_path = (watch_path,)
        else:
            self._watch_path = watch_path

        self._depth = depth
        self._once = once
        self._max_concurrency = max_concurrency

        # Set child operation
        self.children = (op,)

    @property
    def subscribe_op(self) -> Operation[StateDictT]:
        """
        Get the operation to execute when changes occur.

        Returns:
            The operation to execute
        """
        return self._op

    @property
    def watch_path(self) -> Tuple[str, ...]:
        """
        Get the path to watch for changes.

        Returns:
            The path to watch
        """
        return self._watch_path

    @property
    def depth(self) -> int:
        """
        Get the depth of monitoring.

        Returns:
            The depth
        """
        return self._depth

    @property
    def once(self) -> bool:
        """
        Get whether to execute once then complete.

        Returns:
            True if execute once, False if continuous
        """
        return self._once

    @property
    def max_concurrency(self) -> int:
        """
        Get the maximum number of concurrent operation executions.

        Returns:
            The maximum number of concurrent executions
        """
        return self._max_concurrency

    @property
    def metadata(self) -> OperationMetadata:
        """
        Get the operation's metadata.

        Returns:
            The operation metadata
        """
        metadata = super().metadata

        custom_properties = {
            "watch_path": self._watch_path,
            "depth": self._depth,
            "once": self._once,
            "max_concurrency": self._max_concurrency,
        }

        return metadata.with_properties(**custom_properties)


if TYPE_CHECKING:
    _: type[SubscribeOperationProtocol[Operation, "Context"]] = Subscribe
