from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from ..exceptions import OperationError
from .base_operation import BaseOperation
from .logger import logger

if TYPE_CHECKING:
    from loomi.app.base import AsyncApp
    from loomi.app.handlers.state.protocols_tree import AsyncStateDictProtocol
    from loomi.app.handlers.tasks import AsyncOperationProtocol


class DelayOperation(BaseOperation):
    """Executes an operation after a specified delay.

    This operation introduces a time delay before executing the target operation,
    which can be useful for rate limiting, cooling periods, or scheduled execution.

    Args:
        operation: Operation to execute after the delay
        delay: Time in seconds to wait before executing the operation

    Example:
        ```python
        class ProcessWithDelay(App):
            async def process_data(self):
                # Process logic here
                pass

            def define(self) -> Operation:
                return DelayOperation(
                    FunctionOperation(self.process_data),
                    delay=5.0,  # Wait 5 seconds before processing
                )
        ```

    Internal State:
        - Tracks execution status and timing information
    """

    def __init__(
        self,
        operation: "AsyncOperationProtocol | None" = None,
        *,
        delay: float,
    ) -> None:
        if delay < 0:
            raise ValueError("'delay' must be non-negative")

        self.operation = operation
        self.delay = delay
        self._id = hex(id(self))[2:]

    async def execute(self, app: "AsyncApp", loc: "AsyncStateDictProtocol") -> None:
        """Execute the operation after the specified delay."""
        logger.info(f"Starting delay operation with {self.delay}s delay")

        try:
            # Wait for the specified delay
            if self.delay > 0:
                logger.debug(f"Waiting for {self.delay}s")
                await asyncio.sleep(self.delay)

            # Execute the operation after the delay
            logger.info("Delay completed, executing operation")

            if self.operation is None:
                logger.debug("No operation to execute after delay")
                return

            await self._execute_child(self.operation, app, loc)

            logger.info("Delay operation completed successfully")

        except asyncio.CancelledError:
            logger.info("Delay operation was cancelled")
            raise

        except Exception as e:
            logger.error(f"Delay operation failed: {str(e)}", exc_info=True)
            raise OperationError(f"Delay operation failed: {str(e)}") from e
