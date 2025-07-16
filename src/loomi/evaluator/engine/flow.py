"""
Flow expression execution engine.

This module provides execution capabilities for flow expressions such as
Sequence, Parallel, Branch, and Loop, which control the flow of execution
through multiple expressions.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..context import Context
from ..expressions import Sequence
from .base import EngineBase

if TYPE_CHECKING:
    pass


class FlowEngine(EngineBase):
    """
    Engine mixin for executing flow control expressions.

    Provides implementation for executing expressions like Sequence, Parallel,
    Branch, and Loop that control the flow of execution through multiple
    child expressions.
    """

    def exec_sequence(self, expression: Sequence, context: Context) -> None:
        """
        Execute a Sequence expression.

        Executes each child expression in sequence, waiting for each to complete
        before starting the next. Propagates context appropriately to each child.

        Args:
            expression: The Sequence expression to execute
            context: The execution context

        Raises:
            Exception: Any exception raised by child expressions (if error_behavior is "fail")
        """
        self.logger.debug(f"Executing sequence of {len(expression.children)} expressions")

        # Execute each child expression in sequence
        for i, child_op in enumerate(expression.children):
            self.logger.debug(f"Executing sequence item {i + 1}/{len(expression.children)}")

            # Create a derived context for the child expression
            # This maintains the scope but sets the expression reference correctly
            child_context = context.derive(expression=child_op)

            # Execute the child expression
            self.exec_expression(child_context)

    # async def exec_parallel(self, expression: Parallel, context: Context) -> None:
    #     """
    #     Execute a Parallel expression.

    #     Executes child expressions concurrently, with respect to the max_concurrency
    #     parameter. When max_concurrency is 1, it behaves like a Sequence. When
    #     negative or zero, it runs all expressions with no limit.

    #     Args:
    #         expression: The Parallel expression to execute
    #         context: The execution context

    #     Raises:
    #         Exception: Any exception raised by child expressions (if error_behavior is "fail")
    #     """
    #     max_concurrency = expression.max_concurrency
    #     child_ops = expression.children

    #     self.logger.debug(
    #         f"Executing parallel expression with {len(child_ops)} expressions "
    #         f"(max_concurrency={max_concurrency})"
    #     )

    #     # If max_concurrency is 1, execute sequentially
    #     if max_concurrency == 1:
    #         self.logger.debug("Parallel expression with max_concurrency=1, executing sequentially")

    #         # Execute each expression sequentially without creating a new Sequence
    #         for i, child_op in enumerate(child_ops):
    #             self.logger.debug(
    #                 f"Executing parallel (sequential mode) item {i + 1}/{len(child_ops)}"
    #             )

    #             # Create a derived context for the child expression
    #             child_context = context.derive(expression=child_op)

    #             # Execute the child expression
    #             await self.exec_expression(child_context)

    #         return

    #     # Create tasks for all child expressions
    #     tasks = []
    #     errors = []

    #     # Create semaphore for concurrency control if needed
    #     semaphore = asyncio.Semaphore(max_concurrency) if max_concurrency > 0 else None

    #     async def execute_with_semaphore(op: Expression, ctx: Context) -> None:
    #         """Execute an expression with semaphore control if enabled."""
    #         if semaphore:
    #             async with semaphore:
    #                 await self.exec_expression(ctx)
    #         else:
    #             await self.exec_expression(ctx)

    #     # Create tasks for all expressions
    #     for i, child_op in enumerate(child_ops):
    #         self.logger.debug(f"Creating task for parallel item {i + 1}/{len(child_ops)}")

    #         # Create a derived context for the child expression
    #         child_context = context.derive(expression=child_op)

    #         # Create a task for this expression
    #         task = asyncio.create_task(execute_with_semaphore(child_op, child_context))
    #         tasks.append(task)

    #     # Wait for all tasks to complete, gathering errors
    #     if expression._error_behavior == "fail":
    #         # In fail mode, any error will stop all tasks
    #         try:
    #             await asyncio.gather(*tasks)
    #         except Exception as e:
    #             # Cancel all remaining tasks
    #             for task in tasks:
    #                 if not task.done():
    #                     task.cancel()

    #             # Re-raise the error
    #             raise e
    #     else:
    #         # In continue mode, collect all errors but don't stop execution
    #         results = await asyncio.gather(*tasks, return_exceptions=True)

    #         # Check for exceptions
    #         for result in results:
    #             if isinstance(result, Exception):
    #                 errors.append(result)

    #         # Log all errors
    #         for error in errors:
    #             self.logger.error(f"Error in parallel expression: {error}", exc_info=error)

    # async def exec_branch(self, expression: Branch, context: Context) -> None:
    #     """
    #     Execute a Branch expression.

    #     Evaluates a condition and executes the expression corresponding to
    #     the condition's result value. The condition can be specified as a
    #     function or as a path to a value in the state.

    #     Args:
    #         expression: The Branch expression to execute
    #         context: The execution context

    #     Raises:
    #         Exception: Any exception raised by the selected child expression
    #         ExpressionConfigError: If the condition value doesn't match any branch
    #     """
    #     # Evaluate the condition
    #     condition_value = await self._evaluate_branch_condition(expression, context)

    #     self.logger.debug(f"Branch condition evaluated to: {condition_value}")

    #     # Get the expression for this condition value
    #     branch_ops = expression.branch_ops
    #     if condition_value not in branch_ops:
    #         # No matching branch
    #         self.logger.debug(f"No branch found for condition value: {condition_value}")

    #         # Check if there's a default branch
    #         if None in branch_ops:
    #             condition_value = None
    #         else:
    #             raise ExpressionConfigError(
    #                 f"No branch found for condition value: {condition_value}",
    #                 expression=expression,
    #                 context=context,
    #             )

    #     # Execute the selected expression
    #     selected_op = branch_ops[condition_value]
    #     self.logger.debug(f"Executing branch for condition value: {condition_value}")

    #     # Create a derived context for the selected expression
    #     branch_context = context.derive(expression=selected_op)

    #     # Execute the selected expression
    #     await self.exec_expression(branch_context)

    # async def exec_loop(self, expression: Loop, context: Context) -> None:
    #     """
    #     Execute a Loop expression.

    #     Repeatedly executes an expression while a condition is true or until
    #     a maximum number of iterations is reached. The condition can be
    #     specified as a function or as a path to a value in the state.

    #     Args:
    #         expression: The Loop expression to execute
    #         context: The execution context

    #     Raises:
    #         Exception: Any exception raised by the loop expression
    #     """
    #     loop_op = expression.loop_op
    #     max_iterations = expression.max_iterations
    #     iteration = 0

    #     self.logger.debug(
    #         f"Starting loop expression"
    #         f"{f' (max_iterations={max_iterations})' if max_iterations is not None else ''}"
    #     )

    #     while True:
    #         # Check maximum iterations
    #         if max_iterations is not None and iteration >= max_iterations:
    #             self.logger.debug(f"Loop reached maximum iterations: {max_iterations}")
    #             break

    #         # Check condition if specified
    #         if expression.condition is not None or expression.condition_path is not None:
    #             condition_result = await self._evaluate_loop_condition(expression, context)
    #             if not condition_result:
    #                 self.logger.debug("Loop condition evaluated to False, exiting loop")
    #                 break

    #         # Execute the loop expression
    #         self.logger.debug(f"Executing loop iteration {iteration + 1}")

    #         # Create a derived context for the loop expression
    #         loop_context = context.derive(expression=loop_op)

    #         # Add iteration information to context
    #         loop_context["iteration"] = iteration

    #         # Execute the loop expression
    #         await self.exec_expression(loop_context)

    #         # Increment iteration counter
    #         iteration += 1

    #     # Execute on_finish if specified
    #     if expression.on_finish:
    #         self.logger.debug("Executing loop on_finish expression")

    #         # Create a derived context for the on_finish expression
    #         finish_context = context.derive(expression=expression.on_finish)

    #         # Add iteration information to context
    #         finish_context["iterations_completed"] = iteration

    #         # Execute the on_finish expression
    #         await self.exec_expression(finish_context)

    # async def _evaluate_branch_condition(
    #     self, expression: Branch, context: Context
    # ) -> Any:
    #     """
    #     Evaluate the condition for a Branch expression.

    #     The condition can be specified as a function or as a path to a value
    #     in the state. This method evaluates the condition and returns its value.

    #     Args:
    #         expression: The Branch expression
    #         context: The execution context

    #     Returns:
    #         The condition value

    #     Raises:
    #         ExpressionConfigError: If the condition cannot be evaluated
    #     """
    #     # Check condition function
    #     if expression.condition is not None:
    #         condition_func = expression.condition

    #         # Execute the condition function
    #         try:
    #             if inspect.iscoroutinefunction(condition_func):
    #                 return await condition_func(context)
    #             else:
    #                 return condition_func(context)  # type: ignore
    #         except Exception as e:
    #             raise ExpressionExecutionError(
    #                 f"Error evaluating branch condition function: {e}",
    #                 expression=expression,
    #                 context=context,
    #                 cause=e,
    #             )

    #     # Check condition path
    #     elif expression.condition_path is not None:
    #         condition_path = expression.condition_path

    #         # Get value from state
    #         try:
    #             if isinstance(context.scope, AsyncStateProtocol):
    #                 value = await context.scope.get(*condition_path)
    #             elif isinstance(context.scope, SyncStateProtocol):
    #                 value = context.scope.get_primitive(*condition_path)
    #             else:
    #                 raise StateAccessError(
    #                     f"Unsupported dict type: {type(context.scope)}",
    #                     expression=expression,
    #                 )

    #             return value
    #         except Exception as e:
    #             raise ExpressionExecutionError(
    #                 f"Error accessing branch condition path {condition_path}: {e}",
    #                 expression=expression,
    #                 context=context,
    #                 cause=e,
    #             )

    #     # This should never happen due to validation in the Branch constructor
    #     raise ExpressionConfigError(
    #         "Branch expression has no condition or condition_path",
    #         expression=expression,
    #         context=context,
    #     )

    # async def _evaluate_loop_condition(
    #     self, expression: Loop, context: Context
    # ) -> bool:
    #     """
    #     Evaluate the condition for a Loop expression.

    #     The condition can be specified as a function or as a path to a value
    #     in the state. This method evaluates the condition and returns its value.

    #     Args:
    #         expression: The Loop expression
    #         context: The execution context

    #     Returns:
    #         True if the loop should continue, False otherwise

    #     Raises:
    #         ExpressionConfigError: If the condition cannot be evaluated
    #     """
    #     # Check condition function
    #     if expression.condition is not None:
    #         condition_func = expression.condition

    #         # Execute the condition function
    #         try:
    #             if inspect.iscoroutinefunction(condition_func):
    #                 return await condition_func(context)
    #             else:
    #                 return condition_func(context)  # type: ignore
    #         except Exception as e:
    #             raise ExpressionExecutionError(
    #                 f"Error evaluating loop condition function: {e}",
    #                 expression=expression,
    #                 context=context,
    #                 cause=e,
    #             )

    #     # Check condition path
    #     elif expression.condition_path is not None:
    #         condition_path = expression.condition_path

    #         # Get value from state
    #         try:
    #             if isinstance(context.scope, AsyncStateProtocol):
    #                 value = await context.scope.get(*condition_path)
    #             elif isinstance(context.scope, SyncStateProtocol):
    #                 value = context.scope.get_primitive(*condition_path)
    #             else:
    #                 raise StateAccessError(
    #                     f"Unsupported dict type: {type(context.scope)}",
    #                     expression=expression,
    #                 )

    #             return bool(value)
    #         except Exception as e:
    #             raise ExpressionExecutionError(
    #                 f"Error accessing loop condition path {condition_path}: {e}",
    #                 expression=expression,
    #                 context=context,
    #                 cause=e,
    #             )

    #     # No condition means always continue (up to max_iterations)
    #     return True
