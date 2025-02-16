from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from ..exceptions import OperationError
from .base_operation import BaseOperation
from .logger import logger

if TYPE_CHECKING:
    from loomi.app.base import AsyncApp
    from loomi.app.handlers.tasks import AsyncOperationProtocol


class SequenceOperation(BaseOperation):
    """Executes operations in sequence, one after another.

    Args:
        *operations: Operations to execute in sequence
        delay: Delay between operations in seconds. Defaults to 0.
        continue_on_error: Whether to continue execution if an operation fails.
            Defaults to False.

    Example:
        ```python
        class ProcessData(App):
            async def extract(self):
                await self.store.set("data", {"extracted": True})

            async def transform(self):
                await self.store.set("data.transformed", True)

            def define(self) -> Operation:
                return SequenceOperation(
                    FunctionOperation(self.extract),
                    FunctionOperation(self.transform),
                    delay=1.0
                )
        ```

    Internal State:
        - Stores execution status under __sequence__.<id>.current_step
        - Tracks errors under __sequence__.<id>.errors
    """

    def __init__(
        self,
        *operations: "AsyncOperationProtocol",
        delay: float = 0,
        continue_on_error: bool = False,
    ) -> None:
        self.operations = operations
        self.delay = delay
        self.continue_on_error = continue_on_error
        # Unique identifier for this sequence instance
        self._id = hex(id(self))[2:]

    async def _initialize_state(self, app: "AsyncApp") -> None:
        """Initialize sequence state in store"""
        pass

    async def _update_step(self, app: "AsyncApp", step: int) -> None:
        """Update current execution step in store"""
        pass

    async def _record_error(self, app: "AsyncApp", step: int, error: Exception) -> None:
        """Record operation error in store"""
        pass

    async def execute(self, app: "AsyncApp") -> None:
        """Execute operations in sequence with optional delay between them."""
        logger.info(f"Starting sequence execution of {len(self.operations)} operations")

        try:
            await self._initialize_state(app)

            for i, operation in enumerate(self.operations):
                try:
                    await self._update_step(app, i)
                    logger.debug(f"Executing sequence step {i + 1}/{len(self.operations)}")

                    await operation.execute(app)

                    if i < len(self.operations) - 1 and self.delay > 0:
                        logger.debug(f"Waiting {self.delay}s before next operation")
                        await asyncio.sleep(self.delay)

                except Exception as e:
                    error_msg = f"Operation {i + 1} failed: {str(e)}"
                    logger.error(error_msg, exc_info=True)
                    await self._record_error(app, i, e)

                    if not self.continue_on_error:
                        raise OperationError(error_msg) from e

            logger.info("Sequence execution completed successfully")

        except Exception as e:
            logger.error("Sequence execution failed", exc_info=True)
            raise OperationError("Sequence execution failed") from e
