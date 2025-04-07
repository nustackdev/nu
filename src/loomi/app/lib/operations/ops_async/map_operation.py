from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

from ..exceptions import OperationError
from .base_operation import BaseOperation
from .logger import logger

if TYPE_CHECKING:
    from loomi.app.base import AsyncApp
    from loomi.app.handlers.state.protocols_tree import AsyncStateDictProtocol
    from loomi.app.handlers.state.types import StatePath
    from loomi.app.handlers.tasks import AsyncOperationProtocol


class MapOperation(BaseOperation):
    """Executes an operation for each item in a collection from the state.

    This operation retrieves a list from the state using the specified key,
    then executes the target operation once for each item in the list.
    Operations can be executed sequentially or concurrently.

    Args:
        operation: Operation to execute for each item in the collection
        items_key: State key pointing to the list of items to process
        max_concurrency: Maximum number of concurrent operations (None for sequential processing)

    Example:
        ```python
        class ProcessItems(App):
            async def process_item(self):
                # Get current item from context
                item = await self.get("current_item")
                # Process logic here
                pass

            def define(self) -> Operation:
                return MapOperation(
                    FunctionOperation(self.process_item),
                    items_key=("data", "items"),
                    max_concurrency=5,  # Process up to 5 items concurrently
                )
        ```

    Internal State:
        - Sets "current_item" in the state for each operation execution
        - Tracks execution status, progress, and timing information
    """

    def __init__(
        self,
        operation: "AsyncOperationProtocol",
        *,
        items_key: "str | StatePath",
        max_concurrency: int | None = None,
    ) -> None:
        if not items_key:
            raise ValueError("Items key must be provided")
        if max_concurrency is not None and max_concurrency <= 0:
            raise ValueError("'max_concurrency' must be positive")

        self.operation = operation
        self.items_key = items_key if isinstance(items_key, tuple) else (items_key,)
        self.max_concurrency = max_concurrency
        self._id = hex(id(self))[2:]

    async def _process_item(
        self, app: "AsyncApp", loc: "AsyncStateDictProtocol", item: str, index: int
    ) -> None:
        """Process a single item."""
        logger.debug(f"Processing item {index}")

        # Create a context for this item execution
        # item_context_key = ("current_item",)

        try:
            # Execute the operation for this item
            self.operation.update_context(self.context)
            self.operation.update_context(
                {
                    "map_key": item,
                    "map_index": index,
                }
            )
            await self.operation.execute(app, loc)

            logger.debug(f"Completed processing item {index}")

        except Exception as e:
            logger.error(f"Error processing item {index}: {str(e)}", exc_info=True)
            raise

        finally:
            # Clean up the item context
            try:
                # await app.delete(item_context_key)
                pass
            except Exception as e:
                logger.warning(f"Failed to clean up item context: {str(e)}")

    async def execute(self, app: "AsyncApp", loc: "AsyncStateDictProtocol") -> None:
        """Execute the operation for each item in the collection."""
        logger.debug(f"Starting map operation with items key {self.items_key}")

        try:
            if await loc.exists(*self.items_key):
                # Check type and get appropriate identifiers
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
            logger.info(f"Retrieved {item_count} items to process")

            if item_count == 0:
                logger.info("No items to process, map operation completed")
                return

            # Process items sequentially or concurrently based on max_concurrency
            if isinstance(self.max_concurrency, int) and self.max_concurrency == 1:
                # Process sequentially
                logger.debug("Processing items sequentially")
                for index, item in enumerate(items):
                    try:
                        await self._process_item(app, loc, item, index)
                    except Exception as e:
                        raise OperationError(f"Failed to process item {index}: {str(e)}") from e
            else:
                # Process concurrently with max_concurrency limit
                semaphore: asyncio.Semaphore | None = None
                if self.max_concurrency is not None:
                    logger.debug(
                        f"Processing items concurrently with max concurrency {self.max_concurrency}"
                    )

                    # Create a semaphore to limit concurrency
                    semaphore = asyncio.Semaphore(self.max_concurrency)

                async def process_with_semaphore(item: Any, index: int) -> None:
                    if semaphore is not None:
                        async with semaphore:
                            await self._process_item(app, loc, item, index)
                    else:
                        await self._process_item(app, loc, item, index)

                # Create tasks for all items
                tasks = [
                    asyncio.create_task(process_with_semaphore(item, index))
                    for index, item in enumerate(items)
                ]

                # Wait for all tasks to complete
                await asyncio.gather(*tasks)

            logger.info(f"Map operation completed for all {item_count} items")

        except asyncio.CancelledError:
            logger.info("Map operation was cancelled")
            raise

        except Exception as e:
            if not isinstance(e, OperationError):
                logger.error(f"Map operation failed: {str(e)}", exc_info=True)
                raise OperationError(f"Map operation failed: {str(e)}") from e
            raise
