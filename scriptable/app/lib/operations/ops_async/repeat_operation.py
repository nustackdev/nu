from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Optional, Tuple, Union

from ..exceptions import OperationError
from .base_operation import BaseOperation
from .logger import logger

if TYPE_CHECKING:
    from scriptable.app.base import AsyncApp
    from scriptable.app.handlers.tasks import AsyncOperationProtocol


class RepeatOperation(BaseOperation):
    """Repeats an operation either a fixed number of times or while a condition is true.

    Args:
        operation: Operation to repeat
        times: Fixed number of times to repeat the operation
        while_key: State key to check for continuation condition
        max_iterations: Maximum number of iterations when using while_key
        delay: Delay between iterations in seconds
        ignore_errors: Whether to continue execution if an iteration fails

    Example:
        ```python
        class ProcessBatch(App):
            async def process_item(self):
                # Process logic here
                pass

            def define(self) -> Operation:
                return RepeatOperation(
                    FunctionOperation(self.process_item),
                    times=5,
                    delay=1.0
                )

            # Or with condition
            def define_conditional(self) -> Operation:
                return RepeatOperation(
                    FunctionOperation(self.process_item),
                    while_key="has_more_items",
                    max_iterations=100
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
        times: Optional[int] = None,
        while_key: Optional[Union[str, Tuple[str, ...]]] = None,
        max_iterations: Optional[int] = None,
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

    def _state_key(self, key: str | tuple[str, ...] | None = None) -> tuple[str, ...]:
        """Base key for repeat operation state in store"""
        if isinstance(key, str):
            key = (key,)
        return (f"__app__repeat__{self._id}",) + key if key else (f"__app__repeat__{self._id}",)

    async def _initialize_state(self, app: "AsyncApp") -> None:
        """Initialize repeat operation state in store"""
        await app.set(
            self._state_key(),
            value={
                "status": "initialized",
                "current_iteration": 0,
                "max_iterations": self.times or self.max_iterations,
                "while_key": self.while_key,
                "errors": [],
                "start_time": None,
                "end_time": None,
            },
        )

    async def _update_iteration(self, app: "AsyncApp", iteration: int) -> None:
        """Update current iteration count in store"""
        await app.set(self._state_key("current_iteration"), value=iteration)
        await app.set(self._state_key("status"), value="running")

    async def _record_error(self, app: "AsyncApp", iteration: int, error: Exception) -> None:
        """Record iteration error in store"""
        error_data = {
            "iteration": iteration,
            "error": str(error),
            "error_type": error.__class__.__name__,
        }
        await app.set(self._state_key("errors"), value=lambda errors: [*errors, error_data])

    async def _should_continue(self, app: "AsyncApp", iteration: int) -> bool:
        """Determine if operation should continue based on conditions"""
        if self.times is not None:
            return iteration < self.times
        elif self.while_key is not None:
            if self.max_iterations is not None and iteration >= self.max_iterations:
                logger.warning("Reached maximum iterations limit")
                return False
            try:
                return await app.get(self.while_key)
            except Exception as e:
                logger.error(f"Error checking while_key condition: {str(e)}")
                return False
        return False

    async def execute(self, app: "AsyncApp") -> None:
        """Execute the operation repeatedly based on specified conditions."""
        logger.info("Starting repeat operation")

        try:
            await self._initialize_state(app)
            await app.set(self._state_key("start_time"), value="now")

            iteration = 0
            while await self._should_continue(app, iteration):
                try:
                    await self._update_iteration(app, iteration)
                    logger.debug(f"Executing iteration {iteration + 1}")

                    await self.operation.execute(app)

                    if self.delay > 0:
                        logger.debug(f"Waiting {self.delay}s before next iteration")
                        await asyncio.sleep(self.delay)

                except Exception as e:
                    error_msg = f"Iteration {iteration + 1} failed: {str(e)}"
                    logger.error(error_msg, exc_info=True)
                    await self._record_error(app, iteration, e)

                    if not self.ignore_errors:
                        raise OperationError(error_msg) from e

                iteration += 1

            await app.set(self._state_key("status"), value="completed")
            await app.set(self._state_key("end_time"), value="now")
            logger.info(f"Repeat operation completed after {iteration} iterations")

        except asyncio.CancelledError:
            await app.set(self._state_key("status"), value="cancelled")
            logger.info("Repeat operation was cancelled")
            raise

        except Exception as e:
            await app.set(self._state_key("status"), value="failed")
            await app.set(self._state_key("end_time"), value="now")
            if not isinstance(e, OperationError):
                logger.error("Repeat operation failed", exc_info=True)
                raise OperationError(f"Repeat operation failed: {str(e)}") from e
            raise
