"""
Function operation.

This module provides the Function operation, which executes a callable
function or method.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Awaitable, Callable

from loomi.interfaces.executor.operations import FunctionOperationProtocol
from loomi.interfaces.executor.types import ErrorBehavior
from loomi.interfaces.state.type_vars import StateDictT

from .base import Operation
from .metadata import OperationMetadata

if TYPE_CHECKING:
    from ..context.context import Context

__all__ = [
    "Function",
]


class Function(Operation[StateDictT]):
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
        func: (
            Callable[[Context[StateDictT]], Awaitable[None]] | Callable[[Context[StateDictT]], None]
        ),
        /,
        *,
        error_behavior: ErrorBehavior = "fail",
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


if TYPE_CHECKING:
    _: type[FunctionOperationProtocol[Operation, "Context"]] = Function
