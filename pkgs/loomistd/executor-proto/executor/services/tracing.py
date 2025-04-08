from __future__ import annotations

from typing import TYPE_CHECKING, Any

from loomi.app.state import AsyncStateProtocol
from loomi.service import AsyncService, Attach

from ..ops.protocol import Operation

if TYPE_CHECKING:
    from ..context import RuntimeContext


class TracingService(AsyncService):
    """
    Service for recording operation execution events.

    Provides visibility into the execution flow without affecting
    operation behavior.
    """

    state = Attach(AsyncStateProtocol)

    async def operation_started(self, operation: Operation, context: "RuntimeContext") -> None:
        """
        Record that an operation has started.

        Args:
            operation: The operation that started
            context: The execution context
        """
        pass  # Implementation details omitted for brevity

    async def operation_completed(
        self, operation: Operation, context: "RuntimeContext", result: Any = None
    ) -> None:
        """
        Record that an operation has completed successfully.

        Args:
            operation: The operation that completed
            context: The execution context
            result: The result of the operation
        """
        pass  # Implementation details omitted for brevity

    async def operation_failed(
        self, operation: Operation, context: "RuntimeContext", error: Exception
    ) -> None:
        """
        Record that an operation has failed.

        Args:
            operation: The operation that failed
            context: The execution context
            error: The exception that caused the failure
        """
        pass  # Implementation details omitted for brevity
