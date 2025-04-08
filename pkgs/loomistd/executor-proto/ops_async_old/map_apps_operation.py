from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any, List

from ..exceptions import OperationError
from .base_operation import BaseOperation
from .logger import logger

if TYPE_CHECKING:
    from loomi.app.base import AsyncApp
    from loomi.app.handlers.state.protocols_tree import AsyncStateDictProtocol
    from loomi.app.handlers.state.types import StatePath


class MapAppsOperation(BaseOperation):
    """Executes a series of app operations, one for each item in a collection from the state.

    This operation retrieves a list or dictionary from the state using the specified key,
    then executes each app in the provided apps list once for each item in the collection.
    The app's execution location (loc) is adjusted to point to the specific item's location
    in the state.

    Apps can be executed sequentially or concurrently based on max_concurrency.

    Args:
        apps: List of AsyncApp instances to execute for each item
        items_key: State key pointing to the list or dictionary of items to process
        max_concurrency: Maximum number of concurrent app executions (None for sequential processing)

    Example:
        ```python
        class ProcessUserData(App):
            def define(self) -> Operation:
                return MapAppsOperation(
                    apps=[UserProfileApp(), UserPreferencesApp(), UserHistoryApp()],
                    items_key=("users",),
                    max_concurrency=3,  # Process up to 3 users concurrently
                )
        ```

    Internal State:
        - Each app is executed with its loc adjusted to point to the specific item
        - Tracks execution status, progress, and timing information
    """

    def __init__(
        self,
        apps: List["AsyncApp"],
        *,
        items_key: "str | StatePath",
        max_concurrency: int | None = None,
    ) -> None:
        if not apps:
            raise ValueError("At least one app must be provided")
        if not items_key:
            raise ValueError("Items key must be provided")
        if max_concurrency is not None and max_concurrency <= 0:
            raise ValueError("'max_concurrency' must be positive")

        self.apps = apps
        self.items_key = items_key if isinstance(items_key, tuple) else (items_key,)
        self.max_concurrency = max_concurrency
        self._id = hex(id(self))[2:]

    async def _process_item_with_apps(
        self, app: "AsyncApp", loc: "AsyncStateDictProtocol", item_key: str, index: int
    ) -> None:
        """Process a single item with all the provided apps."""
        logger.debug(f"Processing item {index} with {len(self.apps)} apps")

        try:
            # Create the path to the specific item in the state
            item_path = self.items_key + (item_key,)

            # Get the storage dictionary for this specific item
            item_loc = await loc.dict(*item_path)

            # Execute each app with the item-specific location
            for app_index, child_app in enumerate(self.apps):
                try:
                    logger.info(
                        f"Executing app {app_index + 1}/{len(self.apps)} for item {index}: {child_app.readable_name}"
                    )

                    # Execute the app with the item-specific location
                    try:
                        child_app_context = {
                            "map_key": item_key,
                            "map_index": index,
                        }

                        # Run and execute the app
                        await child_app.execute(
                            await child_app.run(child_app_context, item_loc), item_loc
                        )

                        logger.info(
                            f"App '{child_app.readable_name}' completed successfully for item {index}"
                        )

                    except Exception as e:
                        error_msg = (
                            f"App '{child_app.readable_name}' failed for item {index}: {str(e)}"
                        )
                        logger.error(error_msg, exc_info=True)
                        raise OperationError(error_msg) from e

                except Exception as e:
                    logger.error(
                        f"Error in app {app_index + 1} for item {index}: {str(e)}", exc_info=True
                    )
                    raise

            logger.debug(f"Completed processing item {index} with all apps")

        except Exception as e:
            logger.error(f"Error processing item {index}: {str(e)}", exc_info=True)
            raise

    async def execute(self, app: "AsyncApp", loc: "AsyncStateDictProtocol") -> None:
        """Execute the apps for each item in the collection."""
        logger.info(f"Starting MapAppsOperation with items key {self.items_key}")

        try:
            # Check if the items key exists and determine its type
            if await loc.exists(*self.items_key):
                # Determine if it's a dictionary or a list and get appropriate identifiers
                if await loc.is_dict(*self.items_key):
                    # Get dictionary keys without retrieving values
                    dict_obj = await loc.dict(*self.items_key)
                    identifiers = await dict_obj.keys()
                    logger.debug(f"Retrieved {len(identifiers)} dictionary keys to process")
                elif await loc.is_list(*self.items_key):
                    # Get list indices without retrieving all values
                    list_obj = await loc.list(*self.items_key)
                    length = await list_obj.length()
                    identifiers = list([str(i) for i in range(length)])
                    logger.debug(f"Retrieved {length} list indices to process")
                else:
                    raise OperationError(
                        f"Item at {self.items_key} is neither a dict nor a list in compound storage"
                    )
            else:
                raise OperationError(f"Item at {self.items_key} does not exist")

            items = identifiers
            item_count = len(items)
            logger.info(f"Retrieved {item_count} items to process with {len(self.apps)} apps each")

            if item_count == 0:
                logger.info("No items to process, MapAppsOperation completed")
                return

            # Process items sequentially or concurrently based on max_concurrency
            if self.max_concurrency == 1:
                # Process sequentially
                logger.debug("Processing items sequentially")
                for index, item in enumerate(items):
                    try:
                        await self._process_item_with_apps(app, loc, item, index)
                    except Exception as e:
                        raise OperationError(f"Failed to process item {index}: {str(e)}") from e
            else:
                # Process concurrently with max_concurrency limit
                semaphore = None
                if self.max_concurrency is not None:
                    logger.debug(
                        f"Processing items concurrently with max concurrency {self.max_concurrency}"
                    )
                    # Create a semaphore to limit concurrency
                    semaphore = asyncio.Semaphore(self.max_concurrency)

                async def process_with_semaphore(item: Any, index: int) -> None:
                    if semaphore is not None:
                        async with semaphore:
                            await self._process_item_with_apps(app, loc, item, index)
                    else:
                        await self._process_item_with_apps(app, loc, item, index)

                # Create tasks for all items
                tasks = [
                    asyncio.create_task(process_with_semaphore(item, index))
                    for index, item in enumerate(items)
                ]

                # Wait for all tasks to complete
                await asyncio.gather(*tasks)

            logger.info(f"MapAppsOperation completed for all {item_count} items")

        except asyncio.CancelledError:
            logger.info("MapAppsOperation was cancelled")
            raise

        except Exception as e:
            if not isinstance(e, OperationError):
                logger.error(f"MapAppsOperation failed: {str(e)}", exc_info=True)
                raise OperationError(f"MapAppsOperation failed: {str(e)}") from e
            raise
