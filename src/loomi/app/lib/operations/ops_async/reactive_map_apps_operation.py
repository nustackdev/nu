from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Dict, List, Optional, Set

from ..exceptions import OperationError
from .base_operation import BaseOperation
from .logger import logger

if TYPE_CHECKING:
    from loomi.app.base import AsyncApp
    from loomi.app.handlers.state.protocols_tree import AsyncStateDictProtocol
    from loomi.app.handlers.state.types import StatePath
    from loomi.app.handlers.tasks import AsyncOperationProtocol


class ReactiveMapAppsOperation(BaseOperation):
    """Reactively maps apps to items in a dictionary as they are added.

    This operation monitors a dictionary in the state and automatically applies
    the specified apps to each item as it appears. It processes all existing items
    on startup and then watches for new items to process them as they arrive.
    Key deletions are tracked and logged but running tasks are not canceled.

    Args:
        apps: List of apps to execute for each item
        watch_key: State key pointing to the dictionary to monitor
        max_concurrency: Maximum number of concurrent app executions
        completion_operation: Optional operation to execute when an item finishes processing

    Example:
        ```python
        class MonitorTransactions(App):
            def define(self) -> Operation:
                return ReactiveMapAppsOperation(
                    apps=[TransactionSenderApp(), TransactionLoggerApp()],
                    watch_key=("transactions", "pending"),
                    max_concurrency=10,
                    completion_operation=NotifyCompletionOperation()
                )
        ```
    """

    def __init__(
        self,
        apps: List["AsyncApp"],
        *,
        watch_key: "StatePath",
        max_concurrency: Optional[int] = None,
        completion_operation: Optional["AsyncOperationProtocol"] = None,
    ) -> None:
        if not apps:
            raise ValueError("At least one app must be provided")
        if not watch_key:
            raise ValueError("Watch key must be provided")
        if max_concurrency is not None and max_concurrency <= 0:
            raise ValueError("'max_concurrency' must be positive")

        self.apps = apps
        self.watch_key = watch_key
        self.max_concurrency = max_concurrency
        self.completion_operation = completion_operation
        self._id = hex(id(self))[2:]

        # Track processed keys and active tasks
        self._processed_keys: Set[str] = set()
        self._active_tasks: Dict[str, asyncio.Task] = {}
        self._deleted_keys: Set[str] = set()

        # Lock for synchronizing access to shared state
        self._lock = asyncio.Lock()

        # Event for signaling when to stop processing
        self._stop_event = asyncio.Event()

        # Semaphore for controlling concurrency
        self._semaphore = None if max_concurrency is None else asyncio.Semaphore(max_concurrency)

    async def _process_item(
        self, app: "AsyncApp", loc: "AsyncStateDictProtocol", item_key: str
    ) -> None:
        """Process a single item with all the provided apps."""
        logger.debug(f"Processing item {item_key}")

        try:
            # Create the path to the specific item
            item_path = self.watch_key + (item_key,)

            # Check if the item still exists (might have been deleted concurrently)
            if not await loc.exists(*item_path):
                logger.warning(f"Item {item_key} no longer exists, skipping processing")
                return

            # Get the storage dictionary for this specific item
            item_loc = await loc.dict(*item_path)

            # Execute each app with the item-specific location
            for app_index, child_app in enumerate(self.apps):
                try:
                    logger.info(
                        f"Executing app {app_index + 1}/{len(self.apps)} for item {item_key}: {child_app.readable_name}"
                    )

                    # Create context for this app execution
                    child_app_context = {
                        "reactive_key": item_key,
                    }

                    await child_app.execute(
                        await child_app.run(child_app_context, item_loc), item_loc
                    )

                    logger.info(
                        f"App '{child_app.readable_name}' completed successfully for item {item_key}"
                    )

                except Exception as e:
                    error_msg = (
                        f"App '{child_app.readable_name}' failed for item {item_key}: {str(e)}"
                    )
                    logger.error(error_msg, exc_info=True)
                    raise OperationError(error_msg) from e

            # Execute completion operation if provided
            if self.completion_operation:
                try:
                    # Create context for completion operation
                    completion_context = {
                        "completed_key": item_key,
                    }

                    # Execute completion operation
                    self.completion_operation.update_context(self.context)
                    self.completion_operation.update_context(
                        completion_context
                    )  # Add completion context

                    await self.completion_operation.execute(app, loc)

                    logger.info(f"Completion operation executed for item {item_key}")

                except Exception as e:
                    logger.error(
                        f"Error in completion operation for {item_key}: {str(e)}", exc_info=True
                    )

        except asyncio.CancelledError:
            logger.info(f"Processing of item {item_key} was cancelled")
            raise

        except Exception as e:
            error_msg = f"Failed to process item {item_key}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise OperationError(error_msg) from e

        finally:
            # Remove from active tasks
            async with self._lock:
                if item_key in self._active_tasks:
                    del self._active_tasks[item_key]

    async def _handle_key_event(
        self, app: "AsyncApp", loc: "AsyncStateDictProtocol", key: str, is_new: bool = True
    ) -> None:
        """Handle a key event (addition or deletion)."""
        async with self._lock:
            # For new keys - start processing if not already processed
            if is_new:
                if key in self._processed_keys:
                    logger.debug(f"Key {key} already processed, skipping")
                    return

                # Mark as processed
                self._processed_keys.add(key)

                # Create and store task
                task = asyncio.create_task(self._process_item_with_semaphore(app, loc, key))
                self._active_tasks[key] = task

            # For deleted keys - track deletion
            else:
                self._deleted_keys.add(key)
                logger.info(f"Tracked deletion of key {key}")

                # If task is still running, log a warning but don't cancel
                if key in self._active_tasks:
                    logger.warning(f"Item {key} was deleted while still being processed")
                    # Note: we don't cancel the task as it might be finishing up

    async def _process_item_with_semaphore(
        self, app: "AsyncApp", loc: "AsyncStateDictProtocol", item_key: str
    ) -> None:
        """Process an item with semaphore-based concurrency control."""
        if self._semaphore:
            async with self._semaphore:
                await self._process_item(app, loc, item_key)
        else:
            await self._process_item(app, loc, item_key)

    async def _subscribe_to_changes(
        self, app: "AsyncApp", loc: "AsyncStateDictProtocol", dict_obj: "AsyncStateDictProtocol"
    ) -> None:
        """Set up subscription to watch for dictionary changes."""

        # Define callback for key changes
        async def on_change(change_key: "StatePath") -> None:
            try:
                # Extract the key that changed from the full path
                if len(change_key) > len(self.watch_key):
                    item_key = change_key[len(self.watch_key)]

                    # Check if this is a new key or a deleted key
                    item_exists = await loc.exists(*(self.watch_key + (item_key,)))

                    await self._handle_key_event(app, loc, item_key, is_new=item_exists)
            except Exception as e:
                logger.error(f"Error handling change event: {str(e)}", exc_info=True)

        # Subscribe to changes
        # Depth of 1 means direct children only
        subscription = await app.s.subscribe(self.watch_key, on_change, depth=1)
        logger.info(f"Subscribed to changes for key {self.watch_key}")

        # Wait until stop event is set
        await self._stop_event.wait()

        # Unsubscribe when done
        await app.s.unsubscribe(subscription)
        logger.info(f"Unsubscribed from changes for key {self.watch_key}")

    async def execute(self, app: "AsyncApp", loc: "AsyncStateDictProtocol") -> None:
        """Execute the reactive mapping operation."""
        logger.info(f"Starting ReactiveMapAppsOperation for key {self.watch_key}")

        try:
            # Check if the watch key exists and is a dictionary
            if not await loc.exists(*self.watch_key):
                raise OperationError(f"Key {self.watch_key} does not exist")

            if not await loc.is_dict(*self.watch_key):
                raise OperationError(f"Key {self.watch_key} is not a dictionary")

            # Get the dictionary we're watching
            dict_obj = await loc.dict(*self.watch_key)

            # Process existing keys first
            existing_keys = await dict_obj.keys()
            logger.info(f"Found {len(existing_keys)} existing items to process")

            # Initialize the concurrency control semaphore
            if self.max_concurrency is not None:
                self._semaphore = asyncio.Semaphore(self.max_concurrency)

            # Start tasks for processing existing items
            for key in existing_keys:
                async with self._lock:
                    if key not in self._processed_keys:
                        self._processed_keys.add(key)
                        task = asyncio.create_task(self._process_item_with_semaphore(app, loc, key))
                        self._active_tasks[key] = task

            # Watch for changes in the dictionary
            watch_task = asyncio.create_task(self._subscribe_to_changes(app, loc, dict_obj))

            try:
                # Keep running until explicitly cancelled
                while True:
                    await asyncio.sleep(1.0)

            except asyncio.CancelledError:
                logger.info("ReactiveMapAppsOperation was cancelled")
                # Signal watching to stop
                self._stop_event.set()

                # Wait for watch task to complete
                await watch_task

                # Cancel all active processing tasks
                async with self._lock:
                    for key, task in self._active_tasks.items():
                        if not task.done():
                            task.cancel()

                    # Wait for all tasks to complete or be cancelled
                    if self._active_tasks:
                        pending_tasks = list(self._active_tasks.values())
                        await asyncio.gather(*pending_tasks, return_exceptions=True)

                raise

        except Exception as e:
            if not isinstance(e, asyncio.CancelledError):
                logger.error(f"ReactiveMapAppsOperation failed: {str(e)}", exc_info=True)
                raise OperationError(f"ReactiveMapAppsOperation failed: {str(e)}") from e
            raise
