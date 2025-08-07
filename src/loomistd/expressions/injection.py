from __future__ import annotations

from typing import Awaitable, Callable, Optional

from loomi.expression import Context, ErrorBehavior, Expression, ExpressionError
from loomistd.app import SyncAppProtocol

from .logger import logger

__all__ = [
    "Function",
]


class Function(Expression[SyncAppProtocol]):
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
        app,
        func: Callable[[Context], Awaitable[None] | None],
        /,
        *,
        error_behavior: ErrorBehavior = "fail",
        on_fail: Optional[Expression] = None,
    ):
        """
        Initialize the Function expression.

        Args:
            func: The function to execute
            error_behavior: How to handle errors that occur during execution
            on_fail: Expression to execute when an error occurs

        Raises:
            ExpressionError: If func is not a callable
        """
        # Validate that func is callable
        if not callable(func):
            error_msg = f"func must be callable, got {type(func).__name__}"
            logger.error(
                "Invalid function provided to Function expression",
                extra={
                    "func_type": type(func).__name__,
                    "func_repr": repr(func),
                },
            )
            raise ExpressionError(error_msg)

        super().__init__(app, error_behavior=error_behavior, on_fail=on_fail)

        self._func = func

    def do_evaluate(self, context: "Context") -> None:
        """
        Evaluate the Function expression by executing the wrapped function.

        Args:
            app: The application environment
            context: The execution context
        """
        function_name = getattr(self._func, "__name__", "anonymous")

        try:
            # Execute the function using the app's runtime
            future = self.app.runtime.execute(self._func, context)

            # Wait for completion and get result
            result = future.result()

            logger.info(
                "Function expression completed successfully",
                extra={
                    "function_name": function_name,
                    "result_type": type(result).__name__ if result is not None else "None",
                },
            )

        except Exception as e:
            logger.error(
                "Function expression execution failed",
                extra={
                    "function_name": function_name,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                },
                exc_info=True,
            )
            # Re-raise the exception to be handled by the evaluator
            raise
