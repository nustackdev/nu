"""
Function expression.

This module provides the Function expression, which executes a callable
function or method.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Awaitable, Callable, Optional

from loomi.interfaces.executor.operations import FunctionOperationProtocol
from loomi.interfaces.executor.types import ErrorBehavior
from loomi.interfaces.state.type_vars import StateT

from ..base import Expression
from ..metadata import ExpressionMetadata

if TYPE_CHECKING:
    from ...context import Context

__all__ = [
    "Function",
]


class Function(Expression[StateT]):
    """
    Executes a callable function or method.

    This is the most basic expression, allowing arbitrary async callables
    to be used within the expressions framework.

    Args:
        func: The function to execute
        error_behavior: How to handle errors that occur during execution
        on_fail: Expression to execute when an error occurs

    Examples:
        >>> async def greet(context):
        ...     print(f"Hello from path {context.path}")
        ...
        >>> expr = Function(greet)
    """

    def __init__(
        self,
        func: Callable[[Context[StateT]], Awaitable[None] | None],
        /,
        *,
        error_behavior: ErrorBehavior = "fail",
        on_fail: Optional[Expression[StateT]] = None,
    ):
        """
        Initialize the Function expression.

        Args:
            func: The function to execute
            error_behavior: How to handle errors that occur during execution
            on_fail: Expression to execute when an error occurs

        Raises:
            OperationConfigError: If func is not a callable
        """
        super().__init__(error_behavior=error_behavior, on_fail=on_fail)

        self._func = func

    @property
    def metadata(self) -> ExpressionMetadata:
        """
        Get the expression's metadata.

        Includes the function name in the metadata.

        Returns:
            The expression metadata
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
    _: type[FunctionOperationProtocol[Expression, "Context"]] = Function
