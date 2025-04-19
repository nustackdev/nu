"""
ReactiveMap operation.

This module provides the ReactiveMap function, which creates a composite operation
that continuously maps an operation to new items in a collection as they are added.
"""

from __future__ import annotations

import logging
from typing import Optional, Tuple, Union

from loomi.interfaces.executor.types import ErrorBehavior
from loomi.interfaces.state.type_vars import StateDictT

from ..context import Context
from ..operations.atom.function import Function
from ..operations.base import Operation
from ..operations.collections.map import Map
from ..operations.flow.sequence import Sequence
from ..operations.reactive.subscribe import Subscribe


def ReactiveMap(
    op: Operation[StateDictT],
    /,
    *,
    items_path: Union[Tuple[str, ...], str],
    max_concurrency: int = 1,
    error_behavior: ErrorBehavior = "fail",
    on_fail: Optional[Operation[StateDictT]] = None,
) -> Operation[StateDictT]:
    """
    Create a composite operation that continuously maps an operation to new items
    in a collection as they are added.

    This operation first processes all existing items in the collection,
    then establishes a subscription to watch for changes. When new items
    are added, it automatically applies the operation to them. Updates and
    removals of existing items are logged but not reprocessed.

    Args:
        op: The operation to apply to each item
        items_path: Path to the collection in state
        max_concurrency: Maximum number of concurrent operations
            - 1 means sequential execution
            - >1 means limited concurrent execution
            - 0 or -1 means unlimited concurrency
        error_behavior: How to handle errors that occur during execution
        on_fail: Operation to execute when an error occurs

    Returns:
        A composite operation that implements the reactive mapping behavior

    Examples:
        >>> # Process new to-do items as they are added
        >>> reactive_map = ReactiveMap(
        ...     Function(process_todo),
        ...     items_path=("todos",),
        ...     max_concurrency=5
        ... )
    """
    if not items_path:
        raise ValueError("items_path must be provided")

    if max_concurrency < -1:
        raise ValueError(f"Invalid max_concurrency: {max_concurrency}. Must be >= -1")

    # Normalize items_path to tuple
    if isinstance(items_path, str):
        items_path = (items_path,)

    # Set up logger
    logger = logging.getLogger(__name__)  # FIXME: Use a proper logger

    # Set up a registry to track processed keys
    processed_keys = set()

    # Define a wrapper function that updates our registry
    async def process_item(context: Context[StateDictT]):
        """Process a single item and track it in our registry."""
        # Get the key from the context (added by Map operation)
        key = context["map_key"]

        # Add this key to our processed set
        processed_keys.add(key)

        # The engine will execute the operation with this context

    # Define a change handler function
    async def handle_change(context: Context[StateDictT]):
        """Handle collection changes and process new items."""
        # Extract change information
        change_path = context["change_path"]

        # The last element of the path is the key that changed
        if len(change_path) != len(items_path) + 1:
            raise ValueError(
                f"Invalid change path length: {len(change_path)}. Expected {len(items_path) + 1}"
            )

        # Get the key that changed
        key = change_path[-1]

        if key not in processed_keys:
            # New item added - process it
            logger.debug(f"New item added at key {key}, processing")

            # Track this key as processed
            processed_keys.add(key)

            # The engine will execute the operation with this context
        elif key in processed_keys:
            # Existing item updated - just log
            logger.debug(f"Item at key {key} was updated, not reprocessing")

    # First map over all existing items
    initial_map = Map(
        Sequence(
            Function(process_item),
            op,
        ),
        items_path=items_path,
        max_concurrency=max_concurrency,
        error_behavior=error_behavior,
        on_fail=on_fail,
    )

    # Then subscribe to changes
    subscription = Subscribe(
        Sequence(
            Function(handle_change),
            op,
        ),
        watch_path=items_path,
        depth=1,  # Only watch direct children
        error_behavior=error_behavior,
        on_fail=on_fail,
    )

    # Return a sequence that does both
    return Sequence(
        initial_map,
        subscription,
        error_behavior=error_behavior,
        on_fail=on_fail,
    )
