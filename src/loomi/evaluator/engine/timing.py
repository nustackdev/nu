# """
# Timing operation execution engine.

# This module provides execution capabilities for timing operations such as
# Delay, Timeout, and Retry, which control the timing aspects of execution.
# """

# from __future__ import annotations

# import asyncio
# import inspect

# from loomi.state.interface.tree import AsyncStateProtocol, SyncStateProtocol
# from loomi.state.interface.type_vars import StateT

# from ..context import Context
# from ..operations import Delay, Retry, Timeout
# from .base import EngineBase
# from .exceptions import OperationExecutionError, OperationTimeoutError, StateAccessError


# class TimingEngine(EngineBase[StateT]):
#     """
#     Engine mixin for executing timing operations.

#     Provides implementation for executing operations like Delay, Timeout,
#     and Retry that control the timing aspects of operation execution.
#     """

#     async def exec_delay(self, operation: Delay[StateT], context: Context[StateT]) -> None:
#         """
#         Execute a Delay operation.

#         Pauses execution for the specified duration, which can be derived
#         from a fixed value, a function, or a state path.

#         Args:
#             operation: The Delay operation to execute
#             context: The execution context

#         Raises:
#             OperationExecutionError: If the delay value cannot be determined
#         """
#         # Determine the delay duration
#         delay_seconds = await self._get_delay_duration(operation, context)

#         self.logger.debug(f"Executing delay operation for {delay_seconds:.2f} seconds")

#         # Execute the delay
#         if delay_seconds > 0:
#             await asyncio.sleep(delay_seconds)

#         self.logger.debug("Delay operation completed")

#     async def exec_timeout(self, operation: Timeout[StateT], context: Context[StateT]) -> None:
#         """
#         Execute a Timeout operation.

#         Executes a child operation with a timeout constraint, cancelling it
#         if execution exceeds the specified timeout duration. Optionally executes
#         an on_timeout operation if the timeout is reached.

#         Args:
#             operation: The Timeout operation to execute
#             context: The execution context

#         Raises:
#             OperationTimeoutError: If the operation times out
#             Exception: Any exception raised by the child operation
#         """
#         timeout_seconds = operation.timeout
#         child_op = operation.timeout_op
#         on_timeout = operation.on_timeout

#         self.logger.debug(f"Executing operation with {timeout_seconds}s timeout")

#         # Create a derived context for the child operation
#         child_context = context.derive(operation=child_op)

#         try:
#             # Execute the child operation with a timeout
#             task = asyncio.create_task(self.exec_operation(child_context))
#             await asyncio.wait_for(task, timeout=timeout_seconds)

#             self.logger.debug(f"Timeout operation completed successfully within {timeout_seconds}s")

#         except asyncio.TimeoutError:
#             # Operation timed out
#             self.logger.warning(f"Operation timed out after {timeout_seconds}s")

#             # Cancel the task
#             if not task.done():
#                 task.cancel()
#                 try:
#                     # Wait for the task to be cancelled
#                     await task  # type: ignore
#                 except asyncio.CancelledError:
#                     pass

#             # Execute on_timeout operation if specified
#             if on_timeout:
#                 self.logger.debug("Executing on_timeout operation")
#                 timeout_context = context.derive(operation=on_timeout)
#                 await self.exec_operation(timeout_context)

#             # Raise an error if error_behavior is "fail"
#             if operation._error_behavior == "fail":
#                 raise OperationTimeoutError(
#                     f"Operation timed out after {timeout_seconds}s",
#                     operation=operation,
#                     context=context,
#                 )

#     async def exec_retry(self, operation: Retry[StateT], context: Context[StateT]) -> None:
#         """
#         Execute a Retry operation.

#         Attempts to execute a child operation multiple times with exponential
#         backoff between attempts. Can be configured to retry only on specific
#         exception types.

#         Args:
#             operation: The Retry operation to execute
#             context: The execution context

#         Raises:
#             Exception: The last exception raised after all retries fail
#         """
#         max_attempts = operation.max_attempts
#         backoff_factor = operation.backoff_factor
#         initial_delay = operation.initial_delay
#         max_delay = operation.max_delay
#         retry_on = operation.retry_on
#         child_op = operation.retry_op

#         self.logger.debug(
#             f"Executing retry operation (max_attempts={max_attempts}, "
#             f"backoff_factor={backoff_factor}, initial_delay={initial_delay}s)"
#         )

#         # Track attempts and last exception
#         attempt = 0
#         last_exception = None

#         while attempt < max_attempts:
#             # Create a derived context for this attempt
#             attempt_context = context.derive(operation=child_op)
#             attempt_context["retry_attempt"] = attempt

#             try:
#                 # Execute the child operation
#                 self.logger.debug(f"Retry attempt {attempt + 1}/{max_attempts}")
#                 await self.exec_operation(attempt_context)

#                 # If successful, we're done
#                 self.logger.debug(f"Retry operation succeeded on attempt {attempt + 1}")
#                 return

#             except Exception as e:
#                 # Check if we should retry this exception type
#                 should_retry = retry_on is None or any(
#                     isinstance(e, exc_type) for exc_type in retry_on
#                 )

#                 if not should_retry:
#                     self.logger.debug(
#                         f"Exception {type(e).__name__} is not in retry_on list, " f"not retrying"
#                     )
#                     raise e

#                 # Store the exception
#                 last_exception = e

#                 # Log the failure
#                 self.logger.debug(
#                     f"Retry attempt {attempt + 1} failed with {type(e).__name__}: {e}"
#                 )

#                 # Check if we have more attempts
#                 attempt += 1
#                 if attempt >= max_attempts:
#                     self.logger.debug(f"Maximum retry attempts ({max_attempts}) reached")
#                     break

#                 # Calculate backoff delay
#                 delay = min(initial_delay * (backoff_factor ** (attempt - 1)), max_delay)

#                 # Wait before the next attempt
#                 self.logger.debug(f"Waiting {delay:.2f}s before retry attempt {attempt + 1}")
#                 await asyncio.sleep(delay)

#         # If we get here, all retries failed
#         if last_exception is not None:
#             self.logger.debug("All retry attempts failed, raising last exception")
#             raise last_exception

#     async def _get_delay_duration(
#         self, operation: Delay[StateT], context: Context[StateT]
#     ) -> float:
#         """
#         Determine the delay duration from the operation configuration.

#         The delay can be specified as a fixed value, derived from a function,
#         or from a state path.

#         Args:
#             operation: The Delay operation
#             context: The execution context

#         Returns:
#             The delay duration in seconds

#         Raises:
#             OperationExecutionError: If the delay value cannot be determined
#         """
#         # Check fixed delay or function
#         if operation.delay is not None:
#             delay = operation.delay

#             # If it's a function, call it
#             if callable(delay):
#                 try:
#                     if inspect.iscoroutinefunction(delay):
#                         delay_value = await delay(context)
#                     else:
#                         delay_value = delay(context)

#                     if not isinstance(delay_value, (int, float)):
#                         raise ValueError(
#                             f"Delay function must return a number, got {type(delay_value)}"
#                         )

#                     # Ensure the delay is a number
#                     delay_value = float(delay_value)
#                     if delay_value < 0:
#                         raise ValueError(f"Delay must be non-negative, got {delay_value}")

#                     return delay_value
#                 except Exception as e:
#                     raise OperationExecutionError(
#                         f"Error evaluating delay function: {e}",
#                         operation=operation,
#                         context=context,
#                         cause=e,
#                     )

#             # Otherwise, it's a fixed value
#             return float(delay)

#         # Check delay path
#         elif operation.delay_path is not None:
#             delay_path = operation.delay_path

#             # Get value from state
#             try:
#                 if isinstance(context.scope, AsyncStateProtocol):
#                     value = await context.scope.get(*delay_path, default=None)
#                 elif isinstance(context.scope, SyncStateProtocol):
#                     value = context.scope.get_primitive(*delay_path, default=None)
#                 else:
#                     raise StateAccessError(
#                         f"Unsupported dict type: {type(context.scope)}",
#                         operation=operation,
#                     )

#                 if not isinstance(value, (int, float)):
#                     raise ValueError(f"Delay path must resolve to a number, got {type(value)}")

#                 # Ensure the value is a number
#                 value = float(value)
#                 if value < 0:
#                     raise ValueError(f"Delay must be non-negative, got {value}")

#                 return value
#             except Exception as e:
#                 raise OperationExecutionError(
#                     f"Error accessing delay path {delay_path}: {e}",
#                     operation=operation,
#                     context=context,
#                     cause=e,
#                 )

#         # This should never happen due to validation in the Delay constructor
#         raise OperationExecutionError(
#             "Delay operation has no delay or delay_path", operation=operation, context=context
#         )
