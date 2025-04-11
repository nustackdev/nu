"""
ExecutionEngine for the operations framework.

This module provides the ExecutionEngine, which is the central orchestrator
for operation execution.
"""

from typing import TYPE_CHECKING

from loomi.app.tasks.protocols.operations import AppOperationProtocol, FunctionOperationProtocol
from loomi.service import AsyncService, Attach

from .context import Context
from .errors import OperationConfigError
from .ops import Operation
from .ops.atom import App, Function
from .services.task_execution import TaskExecutionService
from .services.tracing import TracingService

if TYPE_CHECKING:
    from loomi.app.state.protocols import AsyncStateProtocol
    from loomi.app.tasks.protocols import AsyncEngineProtocol


class ExecutionEngine(AsyncService):
    """
    Central orchestrator for operation execution.

    Manages the execution of operations, providing them with context
    and access to services. The engine is the primary entry point for
    executing operations within the framework.

    Attributes:
        state: The state store to use for operations
        executor: Service for executing operations
        tracing: Service for tracing operation execution
    """

    # State
    state: "AsyncStateProtocol"

    # Services
    executor = Attach(TaskExecutionService)
    tracing = Attach(TracingService)

    async def execute(
        self,
        operation: Operation,
        parent_context: Context | None = None,
    ) -> None:
        """
        Execute an operation.

        Creates a new context if no parent context is provided, or derives
        a child context from the parent if one is provided.

        Args:
            operation: The operation to execute
            structural_path: Optional structural path, defaults to default_root_path
            state_path: Optional state path, defaults to None (will use structural_path)
            parent_context: Optional parent context to derive from
            timeout: Optional timeout for this operation execution

        Returns:
            The execution task ID

        Raises:
            OperationConfigError: If the operation is invalid
            OperationError: If the operation execution fails
        """
        # Validate operation
        if not isinstance(operation, Operation):
            raise OperationConfigError(f"Expected Operation instance, got {type(operation)}")

        # Set default structural path
        if parent_context is None:
            structural_path = tuple()
            state_path = ("_",)
        else:
            structural_path = parent_context.structural_path
            state_path = parent_context.state_path

        scoped = await self.state.dict(*state_path)

        # Create root context
        context = Context(
            state=self.state,
            executor=self.executor,
            tracing=self.tracing,
            scoped=scoped,
            structural_path=structural_path,
            state_path=state_path,
        )

        # Execute the operation
        await operation.execute(context)

    Function: type[FunctionOperationProtocol[Context]] = Function
    App: type[AppOperationProtocol[Context]] = App
    # Sequence = Sequence
    # other ops


if TYPE_CHECKING:
    _: type["AsyncEngineProtocol[Operation, Context]"] = ExecutionEngine
