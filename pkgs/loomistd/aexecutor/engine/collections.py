"""
Collection operation execution engine.

This module provides execution capabilities for collection operations such as
Map, which apply operations to elements in collections.
"""

from __future__ import annotations

import asyncio
from typing import List, Tuple

from loomi.interfaces.state.state import AsyncStateProtocol, SyncStateProtocol
from loomi.interfaces.state.type_vars import StateDictT, StateT

from ..context import Context
from ..operations import Map
from .base import EngineBase
from .exceptions import OperationExecutionError, StateAccessError


class CollectionEngine(EngineBase[StateT, StateDictT]):
    """
    Engine mixin for executing collection operations.

    Provides implementation for executing operations like Map that
    iterate over collections and apply operations to each item.
    """

    async def exec_map(self, operation: Map[StateDictT], context: Context[StateDictT]) -> None:
        """
        Execute a Map operation.

        Retrieves a dictionary from state and executes an operation for each item.
        Supports configurable concurrency for item processing.

        Args:
            operation: The Map operation to execute
            context: The execution context

        Raises:
            StateAccessError: If the items path doesn't exist or is not a dictionary
            OperationExecutionError: If there's an error during execution
        """
        items_path = operation.items_path
        operation.map_op
        max_concurrency = operation.max_concurrency

        self.logger.debug(
            f"Executing map operation with items_path={items_path}, "
            f"max_concurrency={max_concurrency}"
        )

        # Get the dictionary object
        if isinstance(self.state, AsyncStateProtocol):
            path_exists = await self.state.exists(*items_path)
        elif isinstance(self.state, SyncStateProtocol):
            path_exists = self.state.exists(*items_path)
        else:
            raise StateAccessError(
                f"Unsupported state type: {type(self.state)}",
                operation=operation,
            )

        if not path_exists:
            raise StateAccessError(
                f"Items path {items_path} does not exist",
                operation=operation,
                context=context,
                state_path=items_path,
            )

        # Get the dictionary object
        if isinstance(self.state, AsyncStateProtocol):
            is_dict = await self.state.is_dict(*items_path)
        elif isinstance(self.state, SyncStateProtocol):
            is_dict = self.state.is_dict(*items_path)
        else:
            raise StateAccessError(
                f"Unsupported state type: {type(self.state)}",
                operation=operation,
            )

        if not is_dict:
            raise StateAccessError(
                f"Items path {items_path} is not a dictionary",
                operation=operation,
                context=context,
                state_path=items_path,
            )

        # Get the dictionary object
        if isinstance(self.state, AsyncStateProtocol):
            dict_obj = await self.state.dict(*items_path)
            keys = await dict_obj.keys()
        elif isinstance(self.state, SyncStateProtocol):
            dict_obj = self.state.dict(*items_path)
            keys = dict_obj.keys()
        else:
            raise StateAccessError(
                f"Unsupported state type: {type(self.state)}",
                operation=operation,
            )

        item_count = len(keys)
        self.logger.info(f"Retrieved {item_count} items to process")

        if item_count == 0:
            self.logger.info("No items to process, map operation completed")
            return

        # Process items based on concurrency setting
        if max_concurrency == 1:
            # Process sequentially
            await self._exec_map_sequential(operation, context, items_path, keys)
        else:
            # Process concurrently
            await self._exec_map_concurrent(operation, context, items_path, keys, max_concurrency)

        self.logger.info(f"Map operation completed for all {item_count} items")

    async def _exec_map_sequential(
        self,
        operation: Map[StateDictT],
        context: Context[StateDictT],
        items_path: Tuple[str, ...],
        keys: List[str],
    ) -> None:
        """
        Execute a Map operation sequentially.

        Processes each item one at a time in order.

        Args:
            operation: The Map operation
            context: The execution context
            items_path: Path to the dictionary
            keys: List of keys in the dictionary

        Raises:
            Exception: Any exception from the item processing
        """
        self.logger.debug("Processing items sequentially")
        map_op = operation.map_op

        for index, key in enumerate(keys):
            self.logger.debug(f"Processing item {index + 1}/{len(keys)}: {key}")

            try:
                # Create context for this item
                item_context = context.derive(operation=map_op)

                # Add map metadata to context
                item_context["map_key"] = key
                item_context["map_path"] = items_path + (key,)

                # Execute the operation for this item
                await self.exec_operation(item_context)

                self.logger.debug(f"Completed processing item {index + 1}: {key}")

            except Exception as e:
                error_msg = f"Error processing item {index + 1} ({key}): {str(e)}"
                self.logger.error(error_msg, exc_info=e)

                if operation._error_behavior == "fail":
                    raise OperationExecutionError(
                        error_msg, operation=operation, context=context, cause=e
                    )

    async def _exec_map_concurrent(
        self,
        operation: Map[StateDictT],
        context: Context[StateDictT],
        items_path: Tuple[str, ...],
        keys: List[str],
        max_concurrency: int,
    ) -> None:
        """
        Execute a Map operation concurrently.

        Processes multiple items at once with concurrency control.

        Args:
            operation: The Map operation
            context: The execution context
            items_path: Path to the dictionary
            keys: List of keys in the dictionary
            max_concurrency: Maximum number of concurrent operations

        Raises:
            Exception: Any exception from the item processing
        """
        # Adjust max_concurrency for unlimited (-1 or 0)
        actual_max_concurrency = None
        if max_concurrency > 0:
            actual_max_concurrency = max_concurrency
            self.logger.debug(
                f"Processing items concurrently with max_concurrency={max_concurrency}"
            )
        else:
            self.logger.debug("Processing items with unlimited concurrency")

        # Create a semaphore for concurrency control if needed
        semaphore = None
        if actual_max_concurrency:
            semaphore = asyncio.Semaphore(actual_max_concurrency)

        operation.map_op
        errors = []

        async def process_item(key: str, index: int) -> None:
            """Process a single item with semaphore control if enabled."""
            if semaphore:
                async with semaphore:
                    await self._process_map_item(operation, context, items_path, key, index)
            else:
                await self._process_map_item(operation, context, items_path, key, index)

        # Create tasks for all items
        tasks: list[asyncio.Task] = []
        for index, key in enumerate(keys):
            task = asyncio.create_task(process_item(key, index), name=f"map-{index}")
            tasks.append(task)

        # Wait for all tasks based on error handling behavior
        if operation._error_behavior == "fail":
            # In fail mode, first error stops everything
            try:
                await asyncio.gather(*tasks)
            except Exception as e:
                # Cancel all remaining tasks
                for task in tasks:
                    if not task.done():
                        task.cancel()

                # Re-raise the error
                raise e
        else:
            # In continue mode, collect errors but don't stop
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Check for exceptions
            for result in results:
                if isinstance(result, Exception):
                    errors.append(result)
                    self.logger.error(f"Error in map operation: {result}", exc_info=result)

    async def _process_map_item(
        self,
        operation: Map[StateDictT],
        context: Context[StateDictT],
        items_path: Tuple[str, ...],
        key: str,
        index: int,
    ) -> None:
        """
        Process a single item from a Map operation.

        Args:
            operation: The Map operation
            context: The execution context
            items_path: Path to the dictionary
            key: Key of the item
            index: Position in the iteration

        Raises:
            Exception: Any exception from the item processing
        """
        self.logger.debug(f"Processing map item {index}: {key}")

        map_op = operation.map_op

        try:
            # Create context for this item
            item_context = context.derive(operation=map_op)

            # Add map metadata to context
            item_context["map_key"] = key
            item_context["map_path"] = items_path + (key,)

            # Execute the operation for this item
            await self.exec_operation(item_context)

            self.logger.debug(f"Completed processing map item {index}: {key}")

        except Exception as e:
            error_msg = f"Error processing map item {index} ({key}): {str(e)}"
            self.logger.error(error_msg, exc_info=e)

            # Re-raise for error handling at higher level
            raise OperationExecutionError(error_msg, operation=operation, context=context, cause=e)
