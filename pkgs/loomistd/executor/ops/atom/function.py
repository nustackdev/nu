"""
Function operation.

This module provides the Function operation, which executes a callable
function or method.
"""

from __future__ import annotations

from typing import Any, Awaitable, Callable

from ...context import Context
from ...logger import logger
from ...types import error_behaviors
from ..base import Operation
from ..metadata import OperationMetadata

__all__ = [
    "Function",
]


class Function(Operation):
    """
    Executes a callable function or method.

    This is the most basic operation, allowing arbitrary async callables
    to be used within the operations framework.

    Args:
        func: The function to execute
        error_behavior: How to handle errors that occur during execution
        on_fail: Operation to execute when an error occurs

    Examples:
        >>> async def greet(context):
        ...     print(f"Hello from path {context.path}")
        ...
        >>> op = Function(greet)
    """

    def __init__(
        self,
        func: Callable[[Context], Awaitable[None]],
        /,
        *,
        error_behavior: error_behaviors = "fail",
        on_fail: Operation | None = None,
    ):
        """
        Initialize the Function operation.

        Args:
            func: The function to execute
            error_behavior: How to handle errors that occur during execution
            on_fail: Operation to execute when an error occurs

        Raises:
            OperationConfigError: If func is not a callable
        """
        super().__init__(error_behavior=error_behavior, on_fail=on_fail)

        self._func = func

    @property
    def metadata(self) -> OperationMetadata:
        """
        Get the operation's metadata.

        Includes the function name in the metadata.

        Returns:
            The operation metadata
        """
        metadata = super().metadata

        custom_properties: dict[str, Any] = {}
        try:
            func_name = getattr(self._func, "__name__", str(self._func))
            custom_properties = {"function": func_name}
        except Exception:
            # In case of error, just use the default metadata
            pass
        return metadata.with_properties(**custom_properties)

    async def _execute(self, context: Context) -> None:
        """
        Execute the function with the provided context.

        Args:
            context: Execution context providing access to state and services
        """
        logger.debug(f"Executing function {getattr(self._func, '__name__', '<anonymous>')}")
        await self.execute_task(self._func, context)
