"""
Base execution engine for the operations framework.

This module provides the core engine functionality with lifecycle management,
error handling, and execution coordination. It serves as the foundation
for specialized operation executors.
"""

from __future__ import annotations

import inspect
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Awaitable, Callable, Generic, Optional, TypeVar, cast

from loomi.interfaces.state.type_vars import StateDictT, StateT

from ..context.context import Context
from ..operations.base import Operation
from ..services.logging import LoggingService
from ..services.task_execution import TaskExecutionService
from ..services.tracing import TracingService
from .exceptions import OperationConfigError, wrap_error

if TYPE_CHECKING:
    from ..operations.function import Function
    from ..operations.sequence import Sequence

# Type variables for static typing
T = TypeVar("T")


class EngineBase(ABC, Generic[StateT, StateDictT]):
    """
    Base class for all operation execution engines.

    Provides core execution workflow, error handling, and lifecycle management.
    Specialized engines should inherit from this class and implement specific
    operation execution methods.

    Attributes:
        state: The state store service
        executor: Task execution service for managing async tasks
        tracing: Service for tracing operation execution
        logger: Service for logging operation execution
    """

    # Services
    state: StateT
    executor: TaskExecutionService
    tracing: TracingService
    logger: LoggingService

    async def execute(
        self,
        operation: Operation[StateDictT],
        parent_context: Optional[Context[StateDictT]] = None,
    ) -> None:
        """
        Execute an operation.

        This is the main entry point for executing operations. It creates a new context
        if no parent context is provided, or derives a child context from the parent.

        Args:
            operation: The operation to execute
            parent_context: Optional parent context to derive from

        Raises:
            OperationConfigError: If the operation is invalid
            OperationError: If the operation execution fails
        """
        # Validate operation
        if not isinstance(operation, Operation):
            raise OperationConfigError(f"Expected Operation instance, got {type(operation)}")

        # Determine state path based on context
        if parent_context is None:
            state_path = ("_",)  # Default root path
        else:
            state_path = parent_context.scope.path

        # Get state dict from appropriate path
        if inspect.iscoroutinefunction(self.state.dict):
            scope = await self.state.dict(*state_path)
        else:
            scope = self.state.dict(*state_path)

        # Create root context for the operation
        context = Context[StateDictT](
            operation,
            cast(StateDictT, scope),
            {},  # Empty attributes dict
        )

        # Execute the operation with its context
        await self.exec_operation(context)

    async def exec_operation(self, context: Context[StateDictT]) -> None:
        """
        Execute an operation with its context.

        This method handles the execution lifecycle including logging, tracing,
        and error handling. It dispatches to the appropriate specialized executor
        based on the operation type.

        Args:
            context: Execution context providing access to state and services

        Raises:
            OperationError: If the operation execution fails
        """
        operation = context.operation

        # Log operation start
        self.logger.log_operation_start(operation.metadata.name, operation.structural_path_str)

        # Initialize tracing if enabled
        # self.tracing.start_span(operation, context)

        try:
            # Dispatch to the appropriate execution method based on operation type
            # This will be extended as we add more operation types
            operation_type = type(operation)

            from ..operations.function import Function
            from ..operations.sequence import Sequence

            if operation_type is Function:
                await self.exec_function(cast("Function[StateDictT]", operation), context)
            elif operation_type is Sequence:
                await self.exec_sequence(cast("Sequence[StateDictT]", operation), context)
            else:
                await self._exec_unknown(operation, context)

            # Log operation completion
            self.logger.log_operation_end(operation.metadata.name, operation.structural_path_str)

            # Finalize tracing
            # self.tracing.end_span(operation, context)

        except Exception as e:
            # Log the error
            self.logger.log_operation_error(
                operation.metadata.name, e, operation.structural_path_str
            )

            # Record error in tracing
            # self.tracing.record_exception(operation, context, e)

            # Handle on_fail operation if specified
            if operation._on_fail:
                fail_context = context.derive(operation._on_fail)
                try:
                    await self.exec_operation(fail_context)
                except Exception as fail_e:
                    # Log error in on_fail handler
                    self.logger.log_operation_error(
                        f"{operation.metadata.name}.on_fail",
                        fail_e,
                        operation._on_fail.structural_path_str,
                    )

            # Handle error based on configured behavior
            if operation._error_behavior == "fail":
                wrapped = wrap_error(e, operation, context)
                raise wrapped

    async def execute_task(
        self,
        func: (
            Callable[[Context[StateDictT]], Awaitable[None]] | Callable[[Context[StateDictT]], None]
        ),
        context: Context[StateDictT],
        timeout: Optional[float] = None,
    ) -> None:
        """
        Execute a function as a managed task.

        Delegates function execution to the task executor service, ensuring proper
        task management, tracking, and lifecycle handling.

        Args:
            func: The function to execute
            context: The execution context
            timeout: Optional timeout for the task execution

        Raises:
            RuntimeError: If no executor is available
            TaskExecutionTimeoutError: If task execution exceeds timeout
            TaskExecutionCancelledError: If task is cancelled during execution
        """
        # Execute the function through the task executor
        if inspect.iscoroutinefunction(func):
            await self.executor.execute(func=func, context=context, timeout=timeout, wait=True)
        else:
            # Call synchronous function directly
            func(context)

    @abstractmethod
    async def exec_function(
        self, operation: Function[StateDictT], context: Context[StateDictT]
    ) -> None:
        """
        Execute a Function operation.

        Abstract method to be implemented by specialized engines.

        Args:
            operation: The Function operation to execute
            context: The execution context
        """
        pass

    @abstractmethod
    async def exec_sequence(
        self, operation: Sequence[StateDictT], context: Context[StateDictT]
    ) -> None:
        """
        Execute a Sequence operation.

        Abstract method to be implemented by specialized engines.

        Args:
            operation: The Sequence operation to execute
            context: The execution context
        """
        pass

    async def _exec_unknown(
        self, operation: Operation[StateDictT], context: Context[StateDictT]
    ) -> None:
        """
        Handle unknown operation types.

        This is a fallback method for operation types that are not explicitly supported.

        Args:
            operation: The unknown operation
            context: The execution context

        Raises:
            OperationConfigError: Always raised for unknown operations
        """
        raise OperationConfigError(f"Unknown operation type: {operation.__class__.__name__}")
