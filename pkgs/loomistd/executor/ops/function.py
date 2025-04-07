from __future__ import annotations

import asyncio
from typing import Any, Callable, Dict, Optional

from ..context import RuntimeContext
from ..errors import ErrorBehavior
from .base import BaseOperation


class Function(BaseOperation):
    """
    Executes a callable function or coroutine.

    The most basic building block that wraps a Python callable.
    """

    def __init__(
        self,
        func: Callable[[RuntimeContext], Any],
        error_behavior: ErrorBehavior = ErrorBehavior.FAIL,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize the Function operation.

        Args:
            func: The function to execute (must accept a RuntimeContext)
            error_behavior: How to handle errors in the function
            metadata: Optional custom metadata
        """
        super().__init__(metadata or {})
        self.func = func
        self.error_behavior = error_behavior

        # Add function-specific metadata
        self._metadata.custom_metadata.update(
            {
                "function_name": getattr(func, "__name__", str(func)),
                "error_behavior": error_behavior.name,
                "is_coroutine": asyncio.iscoroutinefunction(func),
            }
        )

    async def execute(self, context: RuntimeContext) -> Any:
        """
        Execute the function with the given context.

        Args:
            context: Execution context

        Returns:
            The result of the function call
        """
        try:
            # Execute the function based on its type
            if asyncio.iscoroutinefunction(self.func):
                return await self.func(context)
            else:
                return self.func(context)

        except Exception as e:
            # Handle errors based on the configured behavior
            if self.error_behavior == ErrorBehavior.CONTINUE:
                # Log the error but continue
                tracing = context.tracing
                if tracing:
                    await tracing.operation_failed(self, context, e)
                return None
            else:
                # Re-raise the error
                raise
