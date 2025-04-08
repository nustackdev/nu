from __future__ import annotations

from typing import Any, List, Optional

from loomi.app.state import AsyncStateProtocol
from loomi.service import AsyncService, Attach

from .context import RuntimeContext
from .ops.protocol import Operation
from .services.executor import ExecutionService
from .services.tracing import TracingService


class ExecutionEngine(AsyncService):
    """
    Central orchestrator for operation execution.

    Manages the execution of operations, providing them with context
    and access to services. Does not directly implement execution logic
    but delegates to services.
    """

    state = Attach(AsyncStateProtocol)
    executor = Attach(ExecutionService)
    tracing = Attach(TracingService)

    async def execute(
        self,
        operation: Operation,
        path: Optional[List[str]] = None,
        parent_context: Optional[RuntimeContext] = None,
    ) -> Any:
        """
        Execute an operation.

        Creates a new context if no parent context is provided, or derives
        a child context from the parent if one is provided.

        Args:
            operation: The operation to execute
            path: Optional execution path, defaults to ["root"]
            parent_context: Optional parent context to derive from

        Returns:
            The result of the operation execution
        """
        # Set default path
        if path is None:
            path = ["_"]

        # Create or derive context
        if parent_context is None:
            context = RuntimeContext(
                path=path,
                state=await self.state.dict("_"),
                tracing=self.tracing,
            )
        else:
            context = parent_context.derive(path=path)

        # Execute the operation
        return await self.executor.execute(operation, context)
