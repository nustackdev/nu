"""
Execution engine for operations.

This module defines the ExecutionEngine, which is responsible for executing
operations and managing their lifecycle.
"""

import asyncio
import logging
import uuid
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, TypeVar

from .context import RuntimeContext
from .errors import enrich_error
from .operation import Operation
from .services import AsyncStateInterface, CancellationToken, ServiceRegistry, TracingService

__all__ = ["ExecutionEngine", "ExecutionBuilder", "ExecutionState", "ExecutionStatus"]

logger = logging.getLogger(__name__)

T = TypeVar("T")

# Type alias for operation handlers
OperationHandler = Callable[[Operation, RuntimeContext], Any]


class ExecutionStatus(Enum):
    """Status of an execution."""

    PENDING = auto()  # Not yet started
    RUNNING = auto()  # Currently running
    COMPLETED = auto()  # Completed successfully
    FAILED = auto()  # Failed with an error
    CANCELLED = auto()  # Cancelled before completion


class ExecutionState:
    """State of an execution.

    This class tracks the state of an execution, including its status,
    result or error, and timing information.

    Attributes:
        execution_id: Unique identifier for the execution
        status: Current status of the execution
        start_time: Time when the execution started (seconds since epoch)
        end_time: Time when the execution ended (seconds since epoch)
        result: Result of the execution (if completed successfully)
        error: Error from the execution (if failed)
        operation_id: ID of the root operation
        context_id: ID of the root context
    """

    def __init__(
        self,
        execution_id: str,
        operation_id: str,
        context_id: str,
    ):
        """Initialize the execution state.

        Args:
            execution_id: Unique identifier for the execution
            operation_id: ID of the root operation
            context_id: ID of the root context
        """
        self.execution_id = execution_id
        self.operation_id = operation_id
        self.context_id = context_id
        self.status = ExecutionStatus.PENDING
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.result: Any = None
        self.error: Optional[Exception] = None
        self._task: Optional[asyncio.Task] = None

    def set_running(self, task: asyncio.Task, start_time: float) -> None:
        """Set the execution as running.

        Args:
            task: The asyncio task for the execution
            start_time: Time when the execution started
        """
        self.status = ExecutionStatus.RUNNING
        self.start_time = start_time
        self._task = task

    def set_completed(self, result: Any, end_time: float) -> None:
        """Set the execution as completed successfully.

        Args:
            result: Result of the execution
            end_time: Time when the execution ended
        """
        self.status = ExecutionStatus.COMPLETED
        self.result = result
        self.end_time = end_time
        self._task = None

    def set_failed(self, error: Exception, end_time: float) -> None:
        """Set the execution as failed.

        Args:
            error: Error from the execution
            end_time: Time when the execution ended
        """
        self.status = ExecutionStatus.FAILED
        self.error = error
        self.end_time = end_time
        self._task = None

    def set_cancelled(self, end_time: float) -> None:
        """Set the execution as cancelled.

        Args:
            end_time: Time when the execution was cancelled
        """
        self.status = ExecutionStatus.CANCELLED
        self.end_time = end_time
        self._task = None

    def cancel(self) -> bool:
        """Cancel the execution if it's running.

        Returns:
            True if the execution was running and was cancelled,
            False if it wasn't running or couldn't be cancelled.
        """
        if self.status == ExecutionStatus.RUNNING and self._task is not None:
            self._task.cancel()
            return True
        return False

    @property
    def is_active(self) -> bool:
        """Check if the execution is still active.

        Returns:
            True if the execution is pending or running, False otherwise.
        """
        return self.status in (ExecutionStatus.PENDING, ExecutionStatus.RUNNING)

    @property
    def duration(self) -> Optional[float]:
        """Get the duration of the execution in seconds.

        Returns:
            Duration in seconds, or None if the execution hasn't started
            or hasn't ended.
        """
        if self.start_time is None:
            return None
        if self.end_time is None:
            return None
        return self.end_time - self.start_time


class ExecutionRegistry:
    """Registry of all executions.

    This class tracks all executions that have been created by the
    execution engine, allowing for introspection and control.
    """

    def __init__(self):
        """Initialize the execution registry."""
        self._executions: Dict[str, ExecutionState] = {}
        self._lock = asyncio.Lock()

    async def register(self, execution: ExecutionState) -> None:
        """Register an execution.

        Args:
            execution: The execution state to register
        """
        async with self._lock:
            self._executions[execution.execution_id] = execution

    async def unregister(self, execution_id: str) -> None:
        """Unregister an execution.

        Args:
            execution_id: ID of the execution to unregister
        """
        async with self._lock:
            if execution_id in self._executions:
                del self._executions[execution_id]

    async def get(self, execution_id: str) -> Optional[ExecutionState]:
        """Get an execution by ID.

        Args:
            execution_id: ID of the execution to get

        Returns:
            The execution state, or None if not found
        """
        async with self._lock:
            return self._executions.get(execution_id)

    async def list_all(self) -> List[ExecutionState]:
        """List all executions.

        Returns:
            List of all execution states
        """
        async with self._lock:
            return list(self._executions.values())

    async def list_active(self) -> List[ExecutionState]:
        """List all active executions.

        Returns:
            List of all active execution states
        """
        async with self._lock:
            return [e for e in self._executions.values() if e.is_active]

    async def cancel_all(self) -> int:
        """Cancel all active executions.

        Returns:
            Number of executions that were cancelled
        """
        cancelled = 0
        async with self._lock:
            for execution in self._executions.values():
                if execution.cancel():
                    cancelled += 1
        return cancelled


class ExecutionEngine:
    """Engine for executing operations.

    The execution engine is responsible for:
    - Managing the operation lifecycle
    - Handling concurrency and task management
    - Providing services for tracing, cancellation, etc.

    This is the central component of the operations framework.
    """

    def __init__(self):
        """Initialize the execution engine."""
        self._registry = ExecutionRegistry()
        self._operation_handlers: Dict[str, OperationHandler] = {}

    def register_handler(self, operation_type: str, handler: OperationHandler) -> None:
        """Register a handler for an operation type.

        Args:
            operation_type: Type of operation to handle
            handler: Function that handles the operation
        """
        self._operation_handlers[operation_type] = handler

    async def execute(self, operation: Operation, context: RuntimeContext) -> Any:
        """Execute an operation with the given context.

        This is the main entry point for executing operations.

        Args:
            operation: The operation to execute
            context: The runtime context for execution

        Returns:
            The result of the operation

        Raises:
            OperationError: If the operation fails and error_behavior is FAIL
        """
        # Create an execution state
        execution_id = context.context_id
        execution = ExecutionState(
            execution_id=execution_id,
            operation_id=operation.id,
            context_id=context.context_id,
        )

        # Register the execution
        await self._registry.register(execution)

        # Create a task for the execution
        import time

        task = asyncio.create_task(
            self._execute_operation(operation, context),
            name=f"operation-{operation.id}",
        )
        execution.set_running(task, time.time())

        try:
            # Wait for the task to complete
            result = await task

            # Record successful completion
            execution.set_completed(result, time.time())

            return result

        except asyncio.CancelledError:
            # Handle cancellation
            logger.info(f"Operation {operation.id} was cancelled")
            execution.set_cancelled(time.time())

            # Trace the cancellation
            await context.trace_cancel()

            # Re-raise to propagate the cancellation
            raise

        except Exception as e:
            # Handle operation errors
            error = enrich_error(
                e,
                operation_id=operation.id,
                operation_type=operation.metadata.operation_type,
            )

            # Log the error
            logger.error(
                f"Operation {operation.id} failed: {str(error)}",
                exc_info=error,
            )

            # Record the failure
            execution.set_failed(error, time.time())

            # Trace the error
            await context.trace_error(error)

            # Re-raise to propagate the error
            raise error

        finally:
            # Unregister the execution
            await self._registry.unregister(execution_id)

    async def _execute_operation(
        self,
        operation: Operation,
        context: RuntimeContext,
    ) -> Any:
        """Execute a single operation.

        This internal method handles the actual execution of an operation,
        delegating to the appropriate handler based on the operation type.

        Args:
            operation: The operation to execute
            context: The runtime context for execution

        Returns:
            The result of the operation

        Raises:
            OperationError: If the operation fails
            NotImplementedError: If no handler is registered for the operation type
        """
        # Start operation tracing
        await context.trace_start()

        try:
            # Check if we've been cancelled before starting
            if context.is_cancelled:
                raise asyncio.CancelledError()

            # Get the appropriate handler for the operation type
            handler = self._get_handler_for_operation(operation)

            # Execute the operation with the handler
            result = await handler(operation, context)

            # Record successful completion
            await context.trace_complete(result)

            return result

        except Exception:
            # Let the execute method handle the error
            raise

    def _get_handler_for_operation(self, operation: Operation) -> OperationHandler:
        """Get the appropriate handler for an operation type.

        Args:
            operation: The operation to get a handler for

        Returns:
            Handler function for the operation

        Raises:
            NotImplementedError: If no handler is registered for the operation type
        """
        operation_type = operation.metadata.operation_type

        if operation_type in self._operation_handlers:
            return self._operation_handlers[operation_type]

        raise NotImplementedError(f"No handler registered for operation type: {operation_type}")

    async def cancel(self, execution_id: str) -> bool:
        """Cancel an ongoing execution.

        Args:
            execution_id: ID of the execution to cancel

        Returns:
            True if the execution was found and cancelled, False otherwise
        """
        execution = await self._registry.get(execution_id)
        if execution:
            return execution.cancel()
        return False

    async def cancel_all(self) -> int:
        """Cancel all ongoing executions.

        Returns:
            Number of executions that were cancelled
        """
        return await self._registry.cancel_all()

    async def get_execution(self, execution_id: str) -> Optional[ExecutionState]:
        """Get information about an execution.

        Args:
            execution_id: ID of the execution to get

        Returns:
            Execution state if found, None otherwise
        """
        return await self._registry.get(execution_id)

    async def list_executions(self, active_only: bool = False) -> List[ExecutionState]:
        """List all executions.

        Args:
            active_only: Whether to only include active executions

        Returns:
            List of execution states
        """
        if active_only:
            return await self._registry.list_active()
        return await self._registry.list_all()


class ExecutionBuilder:
    """Builder for creating and configuring executions.

    This class provides a convenient way to set up an execution context
    and run an operation with the execution engine.
    """

    def __init__(self, engine: ExecutionEngine, state: AsyncStateInterface):
        """Initialize the builder.

        Args:
            engine: The execution engine to use
            state: The state interface to provide to operations
        """
        self.engine = engine
        self.state = state
        self.execution_id = str(uuid.uuid4())
        self.operation_path: List[str] = []
        self.trace = TracingService()
        self.cancellation = CancellationToken()
        self.services = ServiceRegistry()
        self.data: Dict[str, Any] = {}

    def with_id(self, execution_id: str) -> "ExecutionBuilder":
        """Set a custom execution ID.

        Args:
            execution_id: The execution ID to use

        Returns:
            Self for chaining
        """
        self.execution_id = execution_id
        return self

    def with_path(self, path: List[str]) -> "ExecutionBuilder":
        """Set the operation path.

        Args:
            path: The operation path to use

        Returns:
            Self for chaining
        """
        self.operation_path = path
        return self

    def with_trace(self, trace: TracingService) -> "ExecutionBuilder":
        """Set the tracing service.

        Args:
            trace: The tracing service to use

        Returns:
            Self for chaining
        """
        self.trace = trace
        return self

    def with_cancellation(self, cancellation: CancellationToken) -> "ExecutionBuilder":
        """Set the cancellation token.

        Args:
            cancellation: The cancellation token to use

        Returns:
            Self for chaining
        """
        self.cancellation = cancellation
        return self

    def with_service(self, name: str, service: Any) -> "ExecutionBuilder":
        """Register a service.

        Args:
            name: Name to register the service under
            service: The service instance

        Returns:
            Self for chaining
        """
        self.services.register(name, service)
        return self

    def with_data(self, key: str, value: Any) -> "ExecutionBuilder":
        """Add custom data to the execution context.

        Args:
            key: Data key
            value: Data value

        Returns:
            Self for chaining
        """
        self.data[key] = value
        return self

    async def execute(self, operation: Operation) -> Any:
        """Execute the operation.

        This is the final step in the builder chain, which creates the
        context and executes the operation.

        Args:
            operation: The operation to execute

        Returns:
            The result of the operation
        """
        # Create the execution context
        context = RuntimeContext(
            context_id=self.execution_id,
            state=self.state,
            operation_id=operation.id,
            operation_path=self.operation_path,
            trace=self.trace,
            cancellation=self.cancellation,
            services=self.services,
            data=self.data,
        )

        # Execute the operation
        return await self.engine.execute(operation, context)
