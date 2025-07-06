"""
Map operation.

This module provides the Map operation, which executes an operation
for each item in a collection from the state.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Tuple, Union

from loomi.evaluator.interface.operations import MapOperationProtocol
from loomi.evaluator.interface.types import ErrorBehavior
from loomi.state.interface.type_vars import StateT

from ..base import Operation
from ..metadata import OperationMetadata

if TYPE_CHECKING:
    from ...context import Context


class Map(Operation[StateT]):
    """
    Executes an operation for each item in a collection.

    This operation retrieves a dictionary from the state using the specified
    path, then executes the provided operation once for each item. Operations can be
    executed sequentially or concurrently based on max_concurrency.

    The context for each executed operation is enriched with 'map_key' (the key or index
    of the current item) and 'map_index' (the position in the iteration).

    Args:
        op: The operation to execute for each item
        items_path: Path to the collection in state
        max_concurrency: Maximum number of concurrent operations
            - 1 means sequential execution
            - >1 means limited concurrent execution
            - 0 or -1 means unlimited concurrency
        error_behavior: How to handle errors that occur during execution
        on_fail: Operation to execute when an error occurs

    Examples:
        >>> # Process items sequentially
        >>> map_op = Map(
        ...     Function(process_item),
        ...     items_path=("data", "items"),
        ... )
        >>>
        >>> # Process items concurrently (up to 5 at a time)
        >>> map_op = Map(
        ...     Function(process_item),
        ...     items_path=("data", "items"),
        ...     max_concurrency=5,
        ... )
    """

    def __init__(
        self,
        op: Operation[StateT],
        /,
        *,
        items_path: Union[Tuple[str, ...], str],
        max_concurrency: int = 1,
        error_behavior: ErrorBehavior = "fail",
        on_fail: Optional[Operation[StateT]] = None,
    ):
        """
        Initialize the Map operation.

        Args:
            op: The operation to execute for each item
            items_path: Path to the collection in state
            max_concurrency: Maximum number of concurrent operations
                - 1 means sequential execution
                - >1 means limited concurrent execution
                - 0 or -1 means unlimited concurrency
            error_behavior: How to handle errors that occur during execution
            on_fail: Operation to execute when an error occurs

        Raises:
            ValueError: If items_path is empty or max_concurrency is invalid
        """
        super().__init__(error_behavior=error_behavior, on_fail=on_fail)

        if not items_path:
            raise ValueError("items_path must be provided")

        if max_concurrency < -1:
            raise ValueError(f"Invalid max_concurrency: {max_concurrency}. Must be >= -1")

        self._op = op

        # Normalize items_path to tuple
        if isinstance(items_path, str):
            self._items_path = (items_path,)
        else:
            self._items_path = items_path

        self._max_concurrency = max_concurrency

        # Set child operation
        self.children = (op,)

    @property
    def map_op(self) -> Operation[StateT]:
        """
        Get the operation to execute for each item.

        Returns:
            The operation to execute
        """
        return self._op

    @property
    def items_path(self) -> Tuple[str, ...]:
        """
        Get the path to the collection in state.

        Returns:
            The path to the collection
        """
        return self._items_path

    @property
    def max_concurrency(self) -> int:
        """
        Get the maximum number of concurrent operations.

        Returns:
            The maximum number of concurrent operations
        """
        return self._max_concurrency

    @property
    def metadata(self) -> OperationMetadata:
        """
        Get the operation's metadata.

        Returns:
            The operation metadata
        """
        metadata = super().metadata

        custom_properties = {
            "items_path": self._items_path,
            "max_concurrency": self._max_concurrency,
        }

        return metadata.with_properties(**custom_properties)


if TYPE_CHECKING:
    _: type[MapOperationProtocol[Operation, "Context"]] = Map
