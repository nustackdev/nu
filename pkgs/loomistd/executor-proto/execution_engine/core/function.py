"""
Function operation.

This module defines the Function operation, which executes a callable function
or coroutine as part of a workflow.
"""

import asyncio
import inspect
from typing import Any, Callable, List, Optional, Union

from ..context import RuntimeContext
from ..operation import BaseOperation, ErrorBehavior, Operation, OperationMetadata

__all__ = ["Function", "handle_function_operation"]


class Function(BaseOperation):
    """Operation that executes a callable function or coroutine.

    The Function operation is the most basic building block in the operations
    library. It wraps a Python callable (either a regular function or a
    coroutine) and executes it within the workflow.

    Attributes:
        func: The function or coroutine to execute
        error_behavior: How to handle errors in the function
    """

    def __init__(
        self,
        func: Callable[[RuntimeContext], Any],
        error_behavior: Union[ErrorBehavior, str] = ErrorBehavior.FAIL,
        operation_id: Optional[str] = None,
        description: Optional[str] = None,
    ):
        """Initialize the Function operation.

        Args:
            func: The function or coroutine to execute. It must accept a
                RuntimeContext as its only argument.
            error_behavior: How to handle errors in the function.
            operation_id: Optional ID for this operation.
            description: Optional description of what this function does.
        """
        super().__init__(operation_id)

        # Validate the function signature
        sig = inspect.signature(func)
        if len(sig.parameters) != 1:
            raise ValueError(
                f"Function must accept exactly one parameter (context), got {len(sig.parameters)}"
            )

        self.func = func

        # Convert string error_behavior to enum
        if isinstance(error_behavior, str):
            try:
                error_behavior = ErrorBehavior[error_behavior.upper()]
            except KeyError:
                valid_values = ", ".join(e.name for e in ErrorBehavior)
                raise ValueError(
                    f"Invalid error_behavior: {error_behavior}. "
                    f"Valid values are: {valid_values}"
                )

        self.error_behavior = error_behavior

        # Store the description for metadata
        self._description = description or getattr(func, "__doc__", None)

    @property
    def metadata(self) -> OperationMetadata:
        """Get the operation's metadata."""
        return OperationMetadata(
            operation_type="function",
            description=self._description,
            custom_metadata={
                "function_name": getattr(self.func, "__name__", str(self.func)),
                "error_behavior": self.error_behavior.name,
                "is_coroutine": asyncio.iscoroutinefunction(self.func),
            },
        )

    def get_children(self) -> List[Operation]:
        """Get child operations (none for Function operation)."""
        return []


async def handle_function_operation(operation: Function, context: RuntimeContext) -> Any:
    """Execute a Function operation.

    This handler is registered with the execution engine to execute
    Function operations.

    Args:
        operation: The Function operation to execute
        context: The execution context

    Returns:
        The result of the function call

    Raises:
        OperationError: If the function raises an exception and
            error_behavior is FAIL
    """
    func = operation.func

    # Check if we've been cancelled before starting
    if context.is_cancelled:
        raise asyncio.CancelledError()

    try:
        # Execute the function
        if asyncio.iscoroutinefunction(func):
            # Async function - await it
            return await func(context)
        else:
            # Sync function - execute it directly
            return func(context)

    except Exception as e:
        # Handle errors based on error_behavior
        if operation.error_behavior == ErrorBehavior.CONTINUE:
            # Log the error but return None instead of propagating
            await context.trace_error(e)
            return None
        elif operation.error_behavior == ErrorBehavior.RETRY:
            # In a real implementation, we would implement retry logic here
            # For now, just treat it as FAIL
            raise
        else:  # ErrorBehavior.FAIL
            # Re-raise the error (will be caught by the execution engine)
            raise
