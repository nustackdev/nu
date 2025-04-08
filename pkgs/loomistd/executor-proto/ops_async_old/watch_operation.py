from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from ..exceptions import OperationError
from .base_operation import BaseOperation
from .logger import logger

if TYPE_CHECKING:
    from loomi.app.base import AsyncApp
    from loomi.app.handlers.state.protocols_tree import AsyncStateDictProtocol
    from loomi.app.handlers.state.types import StatePath
    from loomi.app.handlers.tasks import AsyncOperationProtocol


class WatchOperation(BaseOperation):
    """Executes an operation when a state change is detected for a specified key.

    This operation uses the state observation pattern to monitor a specific state key
    and triggers the target operation when a change is detected.

    Args:
        operation: Operation to execute when state changes
        watch_key: State key to monitor for changes (tuple of strings)
        depth: Depth of the state key to observe (default is 0)
            0 means the key itself, 1 means the first level of children, etc.
            -1 means any change in the state tree
        max_wait_time: Maximum time in seconds to wait for changes (None for indefinite)
        timeout_operation: Optional operation to execute if timeout occurs

    Example:
        ```python
        class ProcessOnChange(App):
            async def process_data(self):
                # Process logic here
                pass

            def define(self) -> Operation:
                return StateChangeOperation(
                    FunctionOperation(self.process_data),
                    watch_key=("user", "preferences"),
                )
        ```

    Internal State:
        - Tracks execution status and timing information
    """

    def __init__(
        self,
        operation: "AsyncOperationProtocol",
        *,
        watch_key: "StatePath",
        depth: int = 0,
        max_wait_time: float | None = None,
        timeout_operation: "AsyncOperationProtocol | None" = None,
    ) -> None:
        if not watch_key:
            raise ValueError("Watch key must be provided")
        if max_wait_time is not None and max_wait_time <= 0:
            raise ValueError("'max_wait_time' must be positive")

        self.operation = operation
        self.watch_key = watch_key
        self.depth = depth
        self.max_wait_time = max_wait_time
        self.timeout_operation = timeout_operation
        self._id = hex(id(self))[2:]

    async def _state_change_callback(self, key: "StatePath", event: asyncio.Event) -> None:
        """Callback function triggered when state changes"""
        logger.info(f"State change detected for key {key}")
        # Signal the main execution task that a change was detected
        event.set()

    async def execute(self, app: "AsyncApp", loc: "AsyncStateDictProtocol") -> None:
        """Execute the operation when state changes are detected."""
        logger.info(f"Starting state change operation for key {self.watch_key}")

        # Create an event for signaling state changes
        change_detected = asyncio.Event()

        # Define the callback function that captures the app context
        async def callback(key: "StatePath") -> None:
            await self._state_change_callback(key, change_detected)

        subscription = None
        timeout_task = None

        try:
            # Subscribe to changes for the watch key
            watch_key = loc.path + self.watch_key
            subscription = await app.s.subscribe(watch_key, callback, self.depth)
            logger.debug(
                f"Subscribed to changes for key {self.watch_key} depth {self.depth} with {subscription}"
            )
        except Exception as e:
            logger.error(f"Failed to subscribe to state changes: {str(e)}", exc_info=True)
            raise OperationError(f"State observation failed: {str(e)}") from e

        try:
            # Set up timeout if specified
            if self.max_wait_time is not None:

                async def handle_timeout():
                    await asyncio.sleep(self.max_wait_time or 0.0)
                    if not change_detected.is_set():
                        logger.warning(f"Timeout waiting for state change on {self.watch_key}")
                        if self.timeout_operation:
                            logger.info("Executing timeout operation")
                            await self._execute_child(self.timeout_operation, app, loc)
                        change_detected.set()  # Signal to exit wait

                timeout_task = asyncio.create_task(handle_timeout())

            # Wait for state change event
            logger.debug("Waiting for state change event")
            await change_detected.wait()

            # If change was detected (not timeout), execute the operation
            if change_detected.is_set() and (
                self.timeout_operation is None or timeout_task is None or not timeout_task.done()
            ):
                logger.info("Executing operation due to state change")
                await self._execute_child(self.operation, app, loc)

        except asyncio.CancelledError:
            logger.info("State change operation was cancelled")
            raise

        except Exception as e:
            logger.error(f"State change operation failed: {str(e)}", exc_info=True)
            raise OperationError(f"State change operation failed: {str(e)}") from e

        finally:
            # Clean up subscription and timeout task
            if subscription:
                try:
                    await app.s.unsubscribe(subscription)
                    logger.debug(f"Unsubscribed from {self.watch_key}")
                except Exception as e:
                    logger.warning(f"Failed to unsubscribe: {str(e)}")

            if timeout_task and not timeout_task.done():
                timeout_task.cancel()
                try:
                    await timeout_task
                except asyncio.CancelledError:
                    pass

            logger.info("State change operation completed")
