from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any, Awaitable, Callable

from ..exceptions import OperationError
from .base_operation import BaseOperation
from .logger import logger

if TYPE_CHECKING:
    from loomi.app.base import AsyncApp
    from loomi.app.handlers.state.protocols_tree import AsyncStateDictProtocol
    from loomi.app.handlers.state.types import StatePath
    from loomi.app.handlers.tasks import AsyncOperationProtocol


class LoopOperation(BaseOperation):
    """Repeatedly executes an operation while a specified condition evaluates to True.

    This operation can evaluate conditions in two ways:
    1. By checking a state key condition (if condition_key is provided)
    2. By executing a custom condition function (if condition_func is provided)

    The operation will continue executing until the condition becomes False or
    max_iterations is reached (if specified).

    Args:
        operation: Operation to execute while condition is True
        condition_key: State key to check for the condition (tuple of strings)
        condition_func: Function that returns a boolean result
        max_iterations: Maximum number of iterations to prevent infinite loops
        delay: Delay between iterations in seconds
        else_operation: Optional operation to execute after the loop completes

    Example:
        ```python
        class ProcessUntilDone(App):
            async def process_batch(self):
                # Process logic here
                # Update processing status when done
                remaining = await self.get(("queue", "remaining"))
                if remaining == 0:
                    await self.set(("processing", "complete"), True)

            async def check_more_work(self):
                # Custom condition logic that returns an awaitable result
                return await self.get(("queue", "remaining")) > 0

            async def finalize(self):
                # Run after all processing is complete
                await self.set(("processing", "status"), "finalized")

            # Using state key condition
            def define_with_key(self) -> Operation:
                return LoopOperation(
                    FunctionOperation(self.process_batch),
                    condition_key=("processing", "continue"),
                    max_iterations=100,
                    delay=1.0,
                    else_operation=FunctionOperation(self.finalize),
                )

            # Using function condition
            def define_with_func(self) -> Operation:
                return LoopOperation(
                    FunctionOperation(self.process_batch),
                    condition_func=self.check_more_work,
                    max_iterations=100,
                    delay=1.0,
                    else_operation=FunctionOperation(self.finalize),
                )
        ```

    Internal State:
        - Tracks iteration count and execution status
    """

    def __init__(
        self,
        operation: "AsyncOperationProtocol",
        *,
        condition_key: "StatePath | None" = None,
        condition_func: Callable[["AsyncStateDictProtocol"], Awaitable[bool | Any]] | None = None,
        max_iterations: int | None = None,
        delay: float = 0,
        else_operation: "AsyncOperationProtocol | None" = None,
    ) -> None:
        if condition_key is None and condition_func is None:
            raise ValueError("Either condition_key or condition_func must be provided")
        if condition_key is not None and condition_func is not None:
            raise ValueError("Cannot specify both condition_key and condition_func")
        if max_iterations is not None and max_iterations <= 0:
            raise ValueError("'max_iterations' must be positive")
        if delay < 0:
            raise ValueError("'delay' must be non-negative")

        self.operation = operation
        self.condition_key = condition_key
        self.condition_func = condition_func
        self.max_iterations = max_iterations
        self.delay = delay
        self.else_operation = else_operation
        self._id = hex(id(self))[2:]

    async def _evaluate_condition(self, app: "AsyncApp", loc: "AsyncStateDictProtocol") -> bool:
        """Evaluate the condition using either key or function."""
        if self.condition_key is not None:
            # Check the condition in the state
            condition_value = await loc.get(*self.condition_key)
            return bool(condition_value)
        elif self.condition_func is not None:
            # Execute the condition function
            result = await self.condition_func(loc)
            return bool(result)

        # This should never happen due to validation in __init__
        return False

    async def execute(self, app: "AsyncApp", loc: "AsyncStateDictProtocol") -> None:
        """Execute the operation repeatedly while the condition is True."""
        condition_source = "key" if self.condition_key is not None else "function"
        condition_identifier = (
            self.condition_key
            if self.condition_key is not None
            else (
                getattr(self.condition_func, "__name__")
                if hasattr(self.condition_func, "__name__")
                else "anonymous"
            )
        )

        logger.info(
            f"Starting while operation with condition {condition_source}: {condition_identifier}"
        )

        try:
            iteration = 0

            # Check condition before first execution
            while await self._evaluate_condition(app, loc):
                # Check if we've reached max iterations
                if self.max_iterations is not None and iteration >= self.max_iterations:
                    logger.warning(f"Reached maximum iterations limit of {self.max_iterations}")
                    break

                logger.debug(f"Condition is True, executing iteration {iteration + 1}")

                # Execute the operation
                await self._execute_child(self.operation, app, loc)

                iteration += 1

                # Add delay if specified
                if self.delay > 0 and await self._evaluate_condition(app, loc):
                    logger.debug(f"Waiting {self.delay}s before next iteration")
                    await asyncio.sleep(self.delay)

            logger.info(f"Condition is now False after {iteration} iterations")

            # Execute else_operation if provided
            if self.else_operation:
                logger.info("Executing else operation")
                await self._execute_child(self.else_operation, app, loc)

            logger.info("While operation completed successfully")

        except asyncio.CancelledError:
            logger.info("While operation was cancelled")
            raise

        except Exception as e:
            logger.error(f"While operation failed: {str(e)}", exc_info=True)
            raise OperationError(f"While operation failed: {str(e)}") from e
