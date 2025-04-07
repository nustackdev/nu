from __future__ import annotations

from typing import Any

from loomi.service import AsyncService

from ..context import RuntimeContext
from ..ops.protocol import Operation


class ExecutionService(AsyncService):
    """
    Service responsible for executing operations.

    Handles the actual execution logic, including tracing and error handling.
    """

    async def execute(self, operation: Operation, context: RuntimeContext) -> Any:
        """
        Execute an operation with the given context.

        Handles tracing, execution, and error management.

        Args:
            operation: The operation to execute
            context: The execution context

        Returns:
            The result of the operation
        """
        # Get tracing service if available
        tracing = context.tracing

        try:
            # Record start if tracing is available
            if tracing:
                await tracing.operation_started(operation, context)

            # Execute the operation
            result = await operation.execute(context)

            # Record completion if tracing is available
            if tracing:
                await tracing.operation_completed(operation, context, result)

            return result

        except Exception as e:
            # Record error if tracing is available
            if tracing:
                await tracing.operation_failed(operation, context, e)

            # Re-raise the exception
            raise
