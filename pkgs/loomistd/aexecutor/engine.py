"""
ExecutionEngine for the operations framework.

This module provides the ExecutionEngine, which is the central orchestrator
for operation execution.
"""

import inspect
from typing import TYPE_CHECKING, Awaitable, Callable, Generic, cast

import anytree

from loomi import AsyncService, Attach
from loomi.interfaces.executor.executor import AsyncExecutorProtocol
from loomi.interfaces.state.type_vars import StateDictT, StateT

from .context import Context
from .errors import OperationConfigError, wrap_error
from .logger import logger
from .operations.base import Operation
from .operations.function import Function
from .operations.sequence import Sequence
from .services.logging import LoggingService
from .services.task_execution import TaskExecutionService
from .services.tracing import TracingService


class ExecutionEngine(AsyncService, Generic[StateT, StateDictT]):
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

    # Services
    state: StateT = Attach()
    executor = Attach(TaskExecutionService)
    tracing = Attach(TracingService)
    logger = Attach(LoggingService)

    async def execute(
        self,
        operation: Operation[StateDictT],
        parent_context: Context[StateDictT] | None = None,
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
            state_path = ("_",)
        else:
            state_path = parent_context.scope.path

        if inspect.iscoroutinefunction(self.state.dict):
            scope = await self.state.dict(*state_path)
        else:
            scope = self.state.dict(*state_path)

        # Create root context
        context = Context[StateDictT](
            operation,
            cast(StateDictT, scope),
            {},
        )

        # Execute the operation
        await self.exec_operation(context)

    async def execute_task(
        self,
        func: (
            Callable[[Context[StateDictT]], Awaitable[None]] | Callable[[Context[StateDictT]], None]
        ),
        context: Context[StateDictT],
        timeout: float | None = None,
    ) -> None:
        """
        Execute a Python function as a managed task through the executor service.

        This helper method allows operations to delegate function execution to the
        task executor, ensuring proper task management, tracking, and lifecycle.

        Args:
            context: The execution context
            func: The async function to execute
            timeout: Optional timeout for the task execution

        Raises:
            RuntimeError: If no executor is available in the context
        """
        # Ensure executor is available
        # Execute the function through the task executor
        if inspect.iscoroutinefunction(func):
            await self.executor.execute(func=func, context=context, timeout=timeout, wait=True)
        else:
            func(context)

    async def exec_operation(self, context: Context[StateDictT]) -> None:
        """
        Execute the operation within the given context.

        This method handles the execution lifecycle, including logging,
        tracing, and error handling. Subclasses should implement the
        _execute method to define their specific behavior.

        Args:
            context: Execution context providing access to state and services
        """
        node = context.operation

        self.logger.log_operation_start(node.metadata.name, context.operation.structural_path_str)
        # tracing...

        try:
            # Execute the operation
            execs = {
                Function: self.exec_function,
                Sequence: self.exec_sequence,
                None: self.exec_pass,
            }
            exec_fn = execs.get(type(node), self.exec_function)
            await exec_fn(node, context)

            # Log and trace successful completion
            self.logger.log_operation_end(node.metadata.name, context.operation.structural_path_str)
            # tracing...

        except Exception as e:
            # Log and trace error
            self.logger.log_operation_error(
                node.metadata.name, e, context.operation.structural_path_str
            )
            # tracing...

            # Execute on_fail operation if set
            if node._on_fail:
                fail_context = context.derive(node._on_fail)
                try:
                    await self.exec_operation(fail_context)
                except Exception as fail_e:
                    # Log and trace error in on_fail operation
                    self.logger.log_operation_error(
                        f"{node.metadata.name}.on_fail",
                        fail_e,
                        node._on_fail.structural_path_str,
                    )
                    # tracing...

            # Handle error based on error_behavior
            if node._error_behavior == "fail":
                # Wrap and re-raise error
                wrapped = wrap_error(e, self, context)
                raise wrapped

    async def exec_function(
        self, operation: Function[StateDictT], context: Context[StateDictT]
    ) -> None:
        """
        Execute the function with the provided context.

        Args:
            context: Execution context providing access to state and services
        """

        logger.debug(f"Executing function {getattr(operation._func, '__name__', '<anonymous>')}")
        # func_context = context.with_structural_path("Function")
        await self.execute_task(operation._func, context)

    async def exec_sequence(
        self, operation: Sequence[StateDictT], context: Context[StateDictT]
    ) -> None:
        """
        Execute each operation in sequence.

        This method waits for each operation to complete before executing
        the next. If an operation raises an exception, the sequence stops
        (unless error_behavior is "continue").

        Args:
            context: Execution context providing access to state and services
        """

        logger.debug(f"Executing sequence of {len(operation.children)} operations")

        # Execute operations in sequence
        for i, op in enumerate(operation.children):
            # Create a new context for each operation
            op_context = context.derive(operation=op)

            # Execute the operation
            await self.exec_operation(op_context)

    async def exec_pass(self, operation: Operation[StateDictT], context: Context[StateDictT]):
        raise TypeError("Operation unknown")

    def render(self, tree: Operation[StateDictT]) -> None:
        """
        Render the execution tree.

        Args:
            tree: The execution tree to render
        """
        for pre, fill, node in anytree.RenderTree(tree):
            print(
                "%s%s %s"
                % (
                    pre,
                    node.__class__.__name__,
                    node._func.__name__ if hasattr(node, "_func") else "",
                )
            )


if TYPE_CHECKING:
    _: type[AsyncExecutorProtocol] = ExecutionEngine
