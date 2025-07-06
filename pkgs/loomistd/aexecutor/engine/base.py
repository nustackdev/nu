"""
Base execution engine for the operations framework.

This module provides the core engine functionality with lifecycle management,
error handling, and execution coordination. It serves as the foundation
for specialized operation executors.
"""

from __future__ import annotations

import inspect
from abc import ABC, abstractmethod
from typing import Awaitable, Callable, Generic, Optional, cast

from loomi.state.interface.state import AsyncStateServiceProtocol, SyncStateServiceProtocol
from loomi.state.interface.tree import AsyncStateProtocol, SyncStateProtocol
from loomi.state.interface.type_vars import StateT

from ..context import Context
from ..operations import (
    App,
    Branch,
    Delay,
    Function,
    Loop,
    Map,
    Operation,
    Parallel,
    Retry,
    Sequence,
    Subscribe,
    Timeout,
)
from ..services.logging import LoggingService
from ..services.task_execution import TaskExecutionService
from ..services.tracing import TracingService
from .exceptions import OperationConfigError, StateAccessError, wrap_error


class EngineBase(ABC, Generic[StateT]):
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
    state_service: AsyncStateServiceProtocol | SyncStateServiceProtocol
    executor: TaskExecutionService
    tracing: TracingService
    logger: LoggingService

    @property
    def state(self) -> AsyncStateProtocol | SyncStateProtocol:
        """
        Get the state service.

        This property should be overridden by subclasses to provide the actual
        state service instance.
        """
        return self.state_service.state

    async def execute(
        self,
        operation: Operation[StateT],
        parent_context: Optional[Context[StateT]] = None,
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
            state_path = tuple()  # Default root path
        else:
            state_path = parent_context.scope.path.to_tuple()

        # Get the dictionary object
        if isinstance(self.state, AsyncStateProtocol):
            scope = await self.state.at(*state_path)
        elif isinstance(self.state, SyncStateProtocol):
            scope = self.state.at(*state_path)
        else:
            raise StateAccessError(
                f"Unsupported state type: {type(self.state)}",
                operation=operation,
            )

        # Create root context for the operation
        context = Context[StateT](
            operation,
            cast(StateT, scope),
            {},  # Empty attributes dict
        )

        # await self.tracing.start_execution(operation)

        try:
            # Execute the operation with its context
            await self.exec_operation(context)
        finally:
            # Finalize tracing
            # await self.tracing.end_execution()
            pass

    async def exec_operation(self, context: Context[StateT]) -> None:
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
        self.logger.log_operation_start(operation.metadata.name)

        # Initialize tracing if enabled
        # await self.tracing.start_span(operation, context)

        try:
            # Dispatch to the appropriate execution method based on operation type
            # This will be extended as we add more operation types
            operation_type = type(operation)

            if operation_type is Function:
                await self.exec_function(cast(Function[StateT], operation), context)
            elif operation_type is App:
                await self.exec_app(cast(App[StateT], operation), context)
            elif operation_type is Sequence:
                await self.exec_sequence(cast(Sequence[StateT], operation), context)
            elif operation_type is Parallel:
                await self.exec_parallel(cast(Parallel[StateT], operation), context)
            elif operation_type is Branch:
                await self.exec_branch(cast(Branch[StateT], operation), context)
            elif operation_type is Loop:
                await self.exec_loop(cast(Loop[StateT], operation), context)
            elif operation_type is Delay:
                await self.exec_delay(cast(Delay[StateT], operation), context)
            elif operation_type is Retry:
                await self.exec_retry(cast(Retry[StateT], operation), context)
            elif operation_type is Timeout:
                await self.exec_timeout(cast(Timeout[StateT], operation), context)
            elif operation_type is Map:
                await self.exec_map(cast(Map[StateT], operation), context)
            elif operation_type is Subscribe:
                await self.exec_subscribe(cast(Subscribe[StateT], operation), context)
            else:
                await self._exec_unknown(operation, context)

            # Log operation completion
            self.logger.log_operation_end(operation.metadata.name)

            # Finalize tracing
            # await self.tracing.end_span(operation, context)

        except Exception as e:
            # Log the error
            self.logger.log_operation_error(operation.metadata.name, e)

            # Record error in tracing
            # await self.tracing.record_exception(operation, context, e)

            # Handle on_fail operation if specified
            if operation._on_fail:
                fail_context = context.derive(operation._on_fail)
                try:
                    await self.exec_operation(fail_context)
                except Exception as fail_e:
                    # Log error in on_fail handler
                    self.logger.log_operation_error(f"{operation.metadata.name}.on_fail", fail_e)

            # Handle error based on configured behavior
            if operation._error_behavior == "fail":
                wrapped = wrap_error(e, operation, context)
                raise wrapped

    async def execute_task(
        self,
        func: Callable[[Context[StateT]], Awaitable[None] | None],
        context: Context[StateT],
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
    async def exec_function(self, operation: Function[StateT], context: Context[StateT]) -> None:
        """
        Execute a Function operation.

        Abstract method to be implemented by specialized engines.

        Args:
            operation: The Function operation to execute
            context: The execution context
        """
        pass

    @abstractmethod
    async def exec_app(self, operation: App[StateT], context: Context[StateT]) -> None:
        """
        Execute a App operation.

        Abstract method to be implemented by specialized engines.

        Args:
            operation: The App operation to execute
            context: The execution context
        """
        pass

    @abstractmethod
    async def exec_sequence(self, operation: Sequence[StateT], context: Context[StateT]) -> None:
        """
        Execute a Sequence operation.

        Abstract method to be implemented by specialized engines.

        Args:
            operation: The Sequence operation to execute
            context: The execution context
        """
        pass

    @abstractmethod
    async def exec_parallel(self, operation: Parallel[StateT], context: Context[StateT]) -> None:
        """
        Execute a Parallel operation.

        Abstract method to be implemented by specialized engines.

        Args:
            operation: The Parallel operation to execute
            context: The execution context
        """
        pass

    @abstractmethod
    async def exec_branch(self, operation: Branch[StateT], context: Context[StateT]) -> None:
        """
        Execute a Branch operation.

        Abstract method to be implemented by specialized engines.

        Args:
            operation: The Branch operation to execute
            context: The execution context
        """
        pass

    @abstractmethod
    async def exec_loop(self, operation: Loop[StateT], context: Context[StateT]) -> None:
        """
        Execute a Loop operation.

        Abstract method to be implemented by specialized engines.

        Args:
            operation: The Loop operation to execute
            context: The execution context
        """
        pass

    @abstractmethod
    async def exec_delay(self, operation: Delay[StateT], context: Context[StateT]) -> None:
        """
        Execute a Delay operation.

        Abstract method to be implemented by specialized engines.

        Args:
            operation: The Delay operation to execute
            context: The execution context
        """
        pass

    @abstractmethod
    async def exec_retry(self, operation: Retry[StateT], context: Context[StateT]) -> None:
        """
        Execute a Retry operation.

        Abstract method to be implemented by specialized engines.

        Args:
            operation: The Retry operation to execute
            context: The execution context
        """
        pass

    @abstractmethod
    async def exec_timeout(self, operation: Timeout[StateT], context: Context[StateT]) -> None:
        """
        Execute a Timeout operation.

        Abstract method to be implemented by specialized engines.

        Args:
            operation: The Timeout operation to execute
            context: The execution context
        """
        pass

    @abstractmethod
    async def exec_map(self, operation: Map[StateT], context: Context[StateT]) -> None:
        """
        Execute a Map operation.

        Abstract method to be implemented by specialized engines.

        Args:
            operation: The Map operation to execute
            context: The execution context
        """
        pass

    @abstractmethod
    async def exec_subscribe(self, operation: Subscribe[StateT], context: Context[StateT]) -> None:
        """
        Execute a Subscribe operation.

        Abstract method to be implemented by specialized engines.

        Args:
            operation: The Subscribe operation to execute
            context: The execution context
        """
        pass

    async def _exec_unknown(self, operation: Operation[StateT], context: Context[StateT]) -> None:
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
