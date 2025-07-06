"""
Flow operation execution engine.

This module provides execution capabilities for flow operations such as
Sequence, Parallel, Branch, and Loop, which control the flow of execution
through multiple operations.
"""

from __future__ import annotations

import asyncio
import inspect
from typing import TYPE_CHECKING, Any

from loomi.state.interface.tree import AsyncStateProtocol, SyncStateProtocol
from loomi.state.interface.type_vars import StateT

from ..context import Context
from ..operations import Branch, Loop, Parallel, Sequence
from .base import EngineBase
from .exceptions import OperationConfigError, OperationExecutionError, StateAccessError

if TYPE_CHECKING:
    from ..operations import Operation


class FlowEngine(EngineBase[StateT]):
    """
    Engine mixin for executing flow control operations.

    Provides implementation for executing operations like Sequence, Parallel,
    Branch, and Loop that control the flow of execution through multiple
    child operations.
    """

    async def exec_sequence(self, operation: Sequence[StateT], context: Context[StateT]) -> None:
        """
        Execute a Sequence operation.

        Executes each child operation in sequence, waiting for each to complete
        before starting the next. Propagates context appropriately to each child.

        Args:
            operation: The Sequence operation to execute
            context: The execution context

        Raises:
            Exception: Any exception raised by child operations (if error_behavior is "fail")
        """
        self.logger.debug(f"Executing sequence of {len(operation.children)} operations")

        # Execute each child operation in sequence
        for i, child_op in enumerate(operation.children):
            self.logger.debug(f"Executing sequence item {i + 1}/{len(operation.children)}")

            # Create a derived context for the child operation
            # This maintains the scope but sets the operation reference correctly
            child_context = context.derive(operation=child_op)

            # Execute the child operation
            await self.exec_operation(child_context)

    async def exec_parallel(self, operation: Parallel[StateT], context: Context[StateT]) -> None:
        """
        Execute a Parallel operation.

        Executes child operations concurrently, with respect to the max_concurrency
        parameter. When max_concurrency is 1, it behaves like a Sequence. When
        negative or zero, it runs all operations with no limit.

        Args:
            operation: The Parallel operation to execute
            context: The execution context

        Raises:
            Exception: Any exception raised by child operations (if error_behavior is "fail")
        """
        max_concurrency = operation.max_concurrency
        child_ops = operation.children

        self.logger.debug(
            f"Executing parallel operation with {len(child_ops)} operations "
            f"(max_concurrency={max_concurrency})"
        )

        # If max_concurrency is 1, execute sequentially
        if max_concurrency == 1:
            self.logger.debug("Parallel operation with max_concurrency=1, executing sequentially")

            # Execute each operation sequentially without creating a new Sequence
            for i, child_op in enumerate(child_ops):
                self.logger.debug(
                    f"Executing parallel (sequential mode) item {i + 1}/{len(child_ops)}"
                )

                # Create a derived context for the child operation
                child_context = context.derive(operation=child_op)

                # Execute the child operation
                await self.exec_operation(child_context)

            return

        # Create tasks for all child operations
        tasks = []
        errors = []

        # Create semaphore for concurrency control if needed
        semaphore = asyncio.Semaphore(max_concurrency) if max_concurrency > 0 else None

        async def execute_with_semaphore(op: Operation[StateT], ctx: Context[StateT]) -> None:
            """Execute an operation with semaphore control if enabled."""
            if semaphore:
                async with semaphore:
                    await self.exec_operation(ctx)
            else:
                await self.exec_operation(ctx)

        # Create tasks for all operations
        for i, child_op in enumerate(child_ops):
            self.logger.debug(f"Creating task for parallel item {i + 1}/{len(child_ops)}")

            # Create a derived context for the child operation
            child_context = context.derive(operation=child_op)

            # Create a task for this operation
            task = asyncio.create_task(execute_with_semaphore(child_op, child_context))
            tasks.append(task)

        # Wait for all tasks to complete, gathering errors
        if operation._error_behavior == "fail":
            # In fail mode, any error will stop all tasks
            try:
                await asyncio.gather(*tasks)
            except Exception as e:
                # Cancel all remaining tasks
                for task in tasks:
                    if not task.done():
                        task.cancel()

                # Re-raise the error
                raise e
        else:
            # In continue mode, collect all errors but don't stop execution
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Check for exceptions
            for result in results:
                if isinstance(result, Exception):
                    errors.append(result)

            # Log all errors
            for error in errors:
                self.logger.error(f"Error in parallel operation: {error}", exc_info=error)

    async def exec_branch(self, operation: Branch[StateT], context: Context[StateT]) -> None:
        """
        Execute a Branch operation.

        Evaluates a condition and executes the operation corresponding to
        the condition's result value. The condition can be specified as a
        function or as a path to a value in the state.

        Args:
            operation: The Branch operation to execute
            context: The execution context

        Raises:
            Exception: Any exception raised by the selected child operation
            OperationConfigError: If the condition value doesn't match any branch
        """
        # Evaluate the condition
        condition_value = await self._evaluate_branch_condition(operation, context)

        self.logger.debug(f"Branch condition evaluated to: {condition_value}")

        # Get the operation for this condition value
        branch_ops = operation.branch_ops
        if condition_value not in branch_ops:
            # No matching branch
            self.logger.debug(f"No branch found for condition value: {condition_value}")

            # Check if there's a default branch
            if None in branch_ops:
                condition_value = None
            else:
                raise OperationConfigError(
                    f"No branch found for condition value: {condition_value}",
                    operation=operation,
                    context=context,
                )

        # Execute the selected operation
        selected_op = branch_ops[condition_value]
        self.logger.debug(f"Executing branch for condition value: {condition_value}")

        # Create a derived context for the selected operation
        branch_context = context.derive(operation=selected_op)

        # Execute the selected operation
        await self.exec_operation(branch_context)

    async def exec_loop(self, operation: Loop[StateT], context: Context[StateT]) -> None:
        """
        Execute a Loop operation.

        Repeatedly executes an operation while a condition is true or until
        a maximum number of iterations is reached. The condition can be
        specified as a function or as a path to a value in the state.

        Args:
            operation: The Loop operation to execute
            context: The execution context

        Raises:
            Exception: Any exception raised by the loop operation
        """
        loop_op = operation.loop_op
        max_iterations = operation.max_iterations
        iteration = 0

        self.logger.debug(
            f"Starting loop operation"
            f"{f' (max_iterations={max_iterations})' if max_iterations is not None else ''}"
        )

        while True:
            # Check maximum iterations
            if max_iterations is not None and iteration >= max_iterations:
                self.logger.debug(f"Loop reached maximum iterations: {max_iterations}")
                break

            # Check condition if specified
            if operation.condition is not None or operation.condition_path is not None:
                condition_result = await self._evaluate_loop_condition(operation, context)
                if not condition_result:
                    self.logger.debug("Loop condition evaluated to False, exiting loop")
                    break

            # Execute the loop operation
            self.logger.debug(f"Executing loop iteration {iteration + 1}")

            # Create a derived context for the loop operation
            loop_context = context.derive(operation=loop_op)

            # Add iteration information to context
            loop_context["iteration"] = iteration

            # Execute the loop operation
            await self.exec_operation(loop_context)

            # Increment iteration counter
            iteration += 1

        # Execute on_finish if specified
        if operation.on_finish:
            self.logger.debug("Executing loop on_finish operation")

            # Create a derived context for the on_finish operation
            finish_context = context.derive(operation=operation.on_finish)

            # Add iteration information to context
            finish_context["iterations_completed"] = iteration

            # Execute the on_finish operation
            await self.exec_operation(finish_context)

    async def _evaluate_branch_condition(
        self, operation: Branch[StateT], context: Context[StateT]
    ) -> Any:
        """
        Evaluate the condition for a Branch operation.

        The condition can be specified as a function or as a path to a value
        in the state. This method evaluates the condition and returns its value.

        Args:
            operation: The Branch operation
            context: The execution context

        Returns:
            The condition value

        Raises:
            OperationConfigError: If the condition cannot be evaluated
        """
        # Check condition function
        if operation.condition is not None:
            condition_func = operation.condition

            # Execute the condition function
            try:
                if inspect.iscoroutinefunction(condition_func):
                    return await condition_func(context)
                else:
                    return condition_func(context)  # type: ignore
            except Exception as e:
                raise OperationExecutionError(
                    f"Error evaluating branch condition function: {e}",
                    operation=operation,
                    context=context,
                    cause=e,
                )

        # Check condition path
        elif operation.condition_path is not None:
            condition_path = operation.condition_path

            # Get value from state
            try:
                if isinstance(context.scope, AsyncStateProtocol):
                    value = await context.scope.get(*condition_path)
                elif isinstance(context.scope, SyncStateProtocol):
                    value = context.scope.get_primitive(*condition_path)
                else:
                    raise StateAccessError(
                        f"Unsupported dict type: {type(context.scope)}",
                        operation=operation,
                    )

                return value
            except Exception as e:
                raise OperationExecutionError(
                    f"Error accessing branch condition path {condition_path}: {e}",
                    operation=operation,
                    context=context,
                    cause=e,
                )

        # This should never happen due to validation in the Branch constructor
        raise OperationConfigError(
            "Branch operation has no condition or condition_path",
            operation=operation,
            context=context,
        )

    async def _evaluate_loop_condition(
        self, operation: Loop[StateT], context: Context[StateT]
    ) -> bool:
        """
        Evaluate the condition for a Loop operation.

        The condition can be specified as a function or as a path to a value
        in the state. This method evaluates the condition and returns its value.

        Args:
            operation: The Loop operation
            context: The execution context

        Returns:
            True if the loop should continue, False otherwise

        Raises:
            OperationConfigError: If the condition cannot be evaluated
        """
        # Check condition function
        if operation.condition is not None:
            condition_func = operation.condition

            # Execute the condition function
            try:
                if inspect.iscoroutinefunction(condition_func):
                    return await condition_func(context)
                else:
                    return condition_func(context)  # type: ignore
            except Exception as e:
                raise OperationExecutionError(
                    f"Error evaluating loop condition function: {e}",
                    operation=operation,
                    context=context,
                    cause=e,
                )

        # Check condition path
        elif operation.condition_path is not None:
            condition_path = operation.condition_path

            # Get value from state
            try:
                if isinstance(context.scope, AsyncStateProtocol):
                    value = await context.scope.get(*condition_path)
                elif isinstance(context.scope, SyncStateProtocol):
                    value = context.scope.get_primitive(*condition_path)
                else:
                    raise StateAccessError(
                        f"Unsupported dict type: {type(context.scope)}",
                        operation=operation,
                    )

                return bool(value)
            except Exception as e:
                raise OperationExecutionError(
                    f"Error accessing loop condition path {condition_path}: {e}",
                    operation=operation,
                    context=context,
                    cause=e,
                )

        # No condition means always continue (up to max_iterations)
        return True
