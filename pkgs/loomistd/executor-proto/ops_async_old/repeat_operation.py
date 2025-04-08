from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, cast

from ..exceptions import OperationError
from .base_operation import BaseOperation
from .logger import logger

if TYPE_CHECKING:
    from loomi.app.base import AsyncApp
    from loomi.app.handlers.state.protocols_tree import AsyncStateDictProtocol
    from loomi.app.handlers.state.types import StatePath
    from loomi.app.handlers.tasks import AsyncOperationProtocol


class RepeatOperation(BaseOperation):
    """Repeats an operation either a fixed number of times, while a condition is true, or infinitely.

    Args:
        operation: Operation to repeat
        times: Fixed number of times to repeat the operation (None for infinite)
        while_key: State key to check for continuation condition
        max_iterations: Maximum number of iterations when using while_key or for safety with infinite loops
        delay: Delay between iterations in seconds
        ignore_errors: Whether to continue execution if an iteration fails

    Example:
        ```python
        class ProcessBatch(App):
            async def process_item(self):
                # Process logic here
                pass

            def define(self) -> Operation:
                # Repeat 5 times
                return RepeatOperation(
                    FunctionOperation(self.process_item),
                    times=5,
                    delay=1.0
                )

            # With condition
            def define_conditional(self) -> Operation:
                return RepeatOperation(
                    FunctionOperation(self.process_item),
                    while_key="has_more_items",
                    max_iterations=100
                )

            # Infinite loop with safety max
            def define_infinite(self) -> Operation:
                return RepeatOperation(
                    FunctionOperation(self.process_item),
                    delay=1.0,
                    max_iterations=1000  # Safety limit
                )
        ```

    Internal State:
        - Tracks iteration count under __repeat__.<id>.current_iteration
        - Records errors under __repeat__.<id>.errors
        - Stores execution status and timing information
    """

    def __init__(
        self,
        operation: "AsyncOperationProtocol",
        *,
        times: int | None = None,
        while_key: "str | StatePath | None" = None,
        max_iterations: int | None = None,
        delay: float = 0,
        ignore_errors: bool = False,
    ) -> None:
        if times is not None and while_key is not None:
            raise ValueError("Cannot specify both 'times' and 'while_key'")
        if times is not None and times <= 0:
            raise ValueError("'times' must be positive")
        if while_key is not None and max_iterations is None:
            raise ValueError("'max_iterations' required when using 'while_key'")
        if max_iterations is not None and max_iterations <= 0:
            raise ValueError("'max_iterations' must be positive")

        self.operation = operation
        self.times = times
        self.while_key = (
            while_key if isinstance(while_key, tuple) else (while_key,) if while_key else None
        )
        self.max_iterations = max_iterations
        self.delay = delay
        self.ignore_errors = ignore_errors
        self._id = hex(id(self))[2:]

        # If neither times nor while_key is specified, the operation runs infinitely
        self.infinite = times is None and while_key is None

    async def _should_continue(
        self, app: "AsyncApp", loc: "AsyncStateDictProtocol", iteration: int
    ) -> bool:
        """Determine if operation should continue based on conditions"""
        # Safety check for max iterations if set (applies to all modes)
        if self.max_iterations is not None and iteration >= self.max_iterations:
            logger.warning(f"Reached maximum iterations limit of {self.max_iterations}")
            return False

        # If infinite mode is enabled and no max_iterations has been hit
        if self.infinite:
            return True

        # Check fixed number of iterations
        if self.times is not None:
            return iteration < self.times

        # Check condition from state
        elif self.while_key is not None:
            try:
                return cast(bool, await loc.get(*self.while_key))
            except Exception as e:
                logger.error(f"Error checking while_key condition: {str(e)}")
                return False

        # Default - shouldn't reach here with proper initialization
        return False

    async def execute(self, app: "AsyncApp", loc: "AsyncStateDictProtocol") -> None:
        """Execute the operation repeatedly based on specified conditions."""
        if self.infinite and self.max_iterations is None:
            logger.warning(
                "Starting infinite repeat operation with no maximum iterations limit. "
                "This could potentially run forever."
            )
        else:
            logger.info("Starting repeat operation")

        try:

            iteration = 0
            while await self._should_continue(app, loc, iteration):
                try:

                    if self.infinite:
                        logger.debug(f"Executing iteration {iteration + 1} (infinite mode)")
                    else:
                        logger.debug(f"Executing iteration {iteration + 1}")

                    await self._execute_child(self.operation, app, loc)

                    if self.delay > 0:
                        logger.debug(f"Waiting {self.delay}s before next iteration")
                        await asyncio.sleep(self.delay)

                except Exception as e:
                    error_msg = f"Iteration {iteration + 1} failed: {str(e)}"
                    logger.error(error_msg, exc_info=True)

                    if not self.ignore_errors:
                        raise OperationError(error_msg) from e

                iteration += 1

            logger.info(f"Repeat operation completed after {iteration} iterations")

        except asyncio.CancelledError:
            logger.info("Repeat operation was cancelled")
            raise

        except Exception as e:
            if not isinstance(e, OperationError):
                logger.error("Repeat operation failed", exc_info=True)
                raise OperationError(f"Repeat operation failed: {str(e)}") from e
            raise
