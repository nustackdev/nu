from __future__ import annotations

from typing import Any, cast

from loomi.interfaces.state.kv import AsyncTransactionProtocol
from loomistd.kv import StorageKeyError

from .._exceptions import ObjectIndexError, ObjectTypeError
from .._types import TreePath, TreeValueContainer, TreeValueT
from .core import StorageCore

__all__ = [
    "ListOperations",
]


class ListOperations(StorageCore[TreeValueT]):
    """
    Implementation of list operations for tree storage.

    This class provides methods for manipulating list-like structures
    in the underlying key-value storage. It extends the StorageCore class
    with list-specific operations while maintaining the same transactional
    guarantees and error handling protocols.

    List nodes in the tree represent Python list objects, with each
    list index becoming a child node in the tree. A special length field
    is maintained to efficiently track the list's size.
    """

    # --- List initialization and type management --- #

    async def _insert_list(self, path: TreePath, txn: AsyncTransactionProtocol[TreeValueT]) -> None:
        """
        Initialize an empty list node at the specified path.

        This method creates all the required structure for an empty list
        at the given path location. It does not check if the path already exists,
        so it should only be called for paths that don't exist or need to be
        completely re-initialized.

        Args:
            path: Path where to create the list node
            txn: Transaction to use
        """
        # Set type directly on the container path
        await self._storage_set(path, cast(TreeValueT, self._TYPE_LIST), txn)

        # Initialize length to 0
        length_path = self._make_path(path, self._LENGTH_FIELD)
        await self._storage_set(length_path, cast(TreeValueT, 0), txn)

    async def _ensure_list(self, path: TreePath, txn: AsyncTransactionProtocol[TreeValueT]) -> None:
        """
        Ensure that a path contains a list node or initialize it if it doesn't exist.

        Args:
            path: Path to check and potentially initialize
            txn: Transaction to use

        Raises:
            ObjectTypeError: If the path exists but is not a list node
        """
        try:
            # Check if the path exists and what it contains
            node_type = await self._get_node_type(path, txn)

            # If it's not a list type marker
            if node_type != self._TYPE_LIST:
                raise ObjectTypeError(
                    f"Path {path} exists but is not a list node (current type: {node_type})"
                )
        except StorageKeyError:
            # Path doesn't exist, initialize as empty list
            await self._insert_list(path, txn)

    async def _set_list(
        self,
        path: TreePath,
        value: list[TreeValueT],
        txn: AsyncTransactionProtocol[TreeValueT],
    ) -> None:
        """
        Store a list as a tree structure with index-value pairs.

        This method recursively stores a Python list into the tree storage
        system, preserving its structure.

        Args:
            path: Base path for the list node
            value: List to store
            txn: Transaction to use
        """
        # If replacing an existing value, delete old data first
        await self._delete_node(path, txn)

        # Initialize the list structure
        await self._insert_list(path, txn)

        # Update length to match the provided list
        length_path = self._make_path(path, self._LENGTH_FIELD)
        await self._storage_set(length_path, cast(TreeValueT, len(value)), txn)

        # Store each item
        for i, v in enumerate(value):
            item_path = self._make_path(path, str(i))

            # Handle nested nodes
            if isinstance(v, dict):
                await self._set_dict(item_path, v, txn)
            elif isinstance(v, list):
                await self._set_list(item_path, v, txn)
            else:
                # Regular value
                await self._storage_set(item_path, v, txn)

    # --- List length management --- #

    async def list_length(
        self,
        base_path: TreePath,
        txn: AsyncTransactionProtocol[TreeValueT] | None = None,
    ) -> int:
        """
        Get the length of a list node.

        Args:
            base_path: Base path of the list node
            txn: Optional transaction to use

        Returns:
            Number of items in the list

        Raises:
            ObjectTypeError: If base_path is not a list node
        """
        if txn is None:
            async with await self._storage.transaction() as new_txn:
                result = await self._list_length(base_path, new_txn)
            return result
        else:
            return await self._list_length(base_path, txn)

    async def _list_length(
        self,
        base_path: TreePath,
        txn: AsyncTransactionProtocol[TreeValueT],
    ) -> int:
        """
        Internal implementation for getting the length of a list node.

        Args:
            base_path: Base path of the list node
            txn: Transaction to use

        Returns:
            Number of items in the list

        Raises:
            ObjectTypeError: If base_path is not a list node
        """
        # Verify this is a list node
        await self._verify_list(base_path, txn)

        # Get the length
        length_path = self._make_path(base_path, self._LENGTH_FIELD)
        try:
            return await self._storage_get(length_path, txn)
        except StorageKeyError:
            # Length not set, assume empty list
            # This should not happen with properly initialized lists
            length = 0
            await self._storage_set(length_path, cast(TreeValueT, length), txn)
            return length

    # --- List item access operations --- #

    async def list_get(
        self,
        base_path: TreePath,
        index: int,
        txn: AsyncTransactionProtocol[TreeValueT] | None = None,
    ) -> TreeValueContainer[TreeValueT]:
        """
        Get an item from a list node at the specified index.

        Args:
            base_path: Base path of the list node
            index: Index of the item to retrieve
            txn: Optional transaction to use

        Returns:
            Value at the specified index

        Raises:
            ObjectTypeError: If base_path is not a list node
            ObjectIndexError: If index is out of range
        """
        if txn is None:
            async with await self._storage.transaction() as new_txn:
                result = await self._list_get(base_path, index, new_txn)
            return result
        else:
            return await self._list_get(base_path, index, txn)

    async def _list_get(
        self,
        base_path: TreePath,
        index: int,
        txn: AsyncTransactionProtocol[TreeValueT],
    ) -> TreeValueContainer[TreeValueT]:
        """
        Internal implementation for getting an item from a list node.

        Args:
            base_path: Base path of the list node
            index: Index of the item to retrieve
            txn: Transaction to use

        Returns:
            Value at the specified index

        Raises:
            ObjectTypeError: If base_path is not a list node
            ObjectIndexError: If index is out of range
        """
        # Verify this is a list node
        await self._verify_list(base_path, txn)

        # Get list length
        length = await self._list_length(base_path, txn)

        # Normalize negative indices
        if index < 0:
            index = length + index

        # Check if index is valid
        if index < 0 or index >= length:
            raise ObjectIndexError(f"List index {index} out of range (0-{length - 1})")

        # Get the item
        item_path = self._make_path(base_path, str(index))

        return await self._get_value_recursive(item_path, txn)

    async def list_set(
        self,
        base_path: TreePath,
        index: int,
        value: TreeValueT,
        txn: AsyncTransactionProtocol[TreeValueT] | None = None,
    ) -> None:
        """
        Set an item in a list node at the specified index.

        Args:
            base_path: Base path of the list node
            index: Index of the item to set
            value: Value to set
            txn: Optional transaction to use

        Raises:
            ObjectTypeError: If base_path is not a list node
            ObjectIndexError: If index is out of range
        """
        if txn is None:
            async with await self._storage.transaction() as new_txn:
                await self._list_set(base_path, index, value, new_txn)
        else:
            await self._list_set(base_path, index, value, txn)

    async def _list_set(
        self,
        base_path: TreePath,
        index: int,
        value: TreeValueT,
        txn: AsyncTransactionProtocol[TreeValueT],
    ) -> None:
        """
        Internal implementation for setting an item in a list node.

        Args:
            base_path: Base path of the list node
            index: Index of the item to set
            value: Value to set
            txn: Transaction to use

        Raises:
            ObjectTypeError: If base_path is not a list node
            ObjectIndexError: If index is out of range
        """
        # Verify this is a list node
        await self._verify_list(base_path, txn)

        # Get list length
        length = await self._list_length(base_path, txn)

        # Normalize negative indices
        if index < 0:
            index = length + index

        # Check if index is valid
        if index < 0 or index >= length:
            raise ObjectIndexError(f"List index {index} out of range (0-{length - 1})")

        # Set the item
        item_path = self._make_path(base_path, str(index))

        # Delete existing item if it's a dict or list node
        try:
            if await self._is_dict(item_path, txn) or await self._is_list(item_path, txn):
                # Recursively delete the existing node
                await self._delete_node(item_path, txn)
            else:
                # Delete the simple value if it exists
                try:
                    await self._storage_delete(item_path, txn)
                except StorageKeyError:
                    pass  # Item might not exist
        except StorageKeyError:
            pass  # Path doesn't exist yet

        # Store the new value
        if isinstance(value, dict):
            await self._set_dict(item_path, value, txn)
        elif isinstance(value, list):
            await self._set_list(item_path, value, txn)
        else:
            # Regular value
            await self._storage_set(item_path, value, txn)

    # --- List modification operations --- #

    async def list_append(
        self,
        base_path: TreePath,
        value: TreeValueT,
        txn: AsyncTransactionProtocol[TreeValueT] | None = None,
    ) -> int:
        """
        Append an item to a list node.

        Args:
            base_path: Base path of the list node
            value: Value to append
            txn: Optional transaction to use

        Returns:
            New length of the list

        Raises:
            ObjectTypeError: If base_path is not a list node
        """
        if txn is None:
            async with await self._storage.transaction() as new_txn:
                result = await self._list_append(base_path, value, new_txn)
            return result
        else:
            return await self._list_append(base_path, value, txn)

    async def _list_append(
        self,
        base_path: TreePath,
        value: TreeValueT,
        txn: AsyncTransactionProtocol[TreeValueT],
    ) -> int:
        """
        Internal implementation for appending an item to a list node.

        Args:
            base_path: Base path of the list node
            value: Value to append
            txn: Transaction to use

        Returns:
            New length of the list

        Raises:
            ObjectTypeError: If base_path is not a list node
        """
        # Verify this is a list node or create it
        try:
            node_type = await self._get_node_type(base_path, txn)
            if node_type is not None and node_type != self._TYPE_LIST:
                raise ObjectTypeError(
                    f"Path {base_path} is not a list node (current type: {node_type})"
                )
        except StorageKeyError:
            # Initialize as empty list if it doesn't exist
            await self._insert_list(base_path, txn)

        # Get current length
        length_path = self._make_path(base_path, self._LENGTH_FIELD)
        try:
            length = await self._storage_get(length_path, txn)
        except StorageKeyError:
            # Should not happen if properly initialized, but let's be safe
            length = 0
            await self._storage_set(length_path, cast(TreeValueT, length), txn)

        # Append the item
        item_path = self._make_path(base_path, str(length))
        if isinstance(value, dict):
            await self._set_dict(item_path, value, txn)
        elif isinstance(value, list):
            await self._set_list(item_path, value, txn)
        else:
            # Regular value
            await self._storage_set(item_path, value, txn)

        # Update length
        new_length = length + 1
        await self._storage_set(length_path, cast(TreeValueT, new_length), txn)

        return new_length

    async def list_extend(
        self,
        base_path: TreePath,
        values: list[TreeValueT],
        txn: AsyncTransactionProtocol[TreeValueT] | None = None,
    ) -> int:
        """
        Extend a list node with multiple values.

        Args:
            base_path: Base path of the list node
            values: Values to append
            txn: Optional transaction to use

        Returns:
            New length of the list

        Raises:
            ObjectTypeError: If base_path is not a list node
        """
        if txn is None:
            async with await self._storage.transaction() as new_txn:
                result = await self._list_extend(base_path, values, new_txn)
            return result
        else:
            return await self._list_extend(base_path, values, txn)

    async def _list_extend(
        self,
        base_path: TreePath,
        values: list[TreeValueT],
        txn: AsyncTransactionProtocol[TreeValueT],
    ) -> int:
        """
        Internal implementation for extending a list node with multiple values.

        Args:
            base_path: Base path of the list node
            values: Values to append
            txn: Transaction to use

        Returns:
            New length of the list

        Raises:
            ObjectTypeError: If base_path is not a list node
        """
        # Ensure it's a list node or initialize it
        try:
            node_type = await self._get_node_type(base_path, txn)
            if node_type is not None and node_type != self._TYPE_LIST:
                raise ObjectTypeError(
                    f"Path {base_path} is not a list node (current type: {node_type})"
                )
        except StorageKeyError:
            # Initialize as empty list if it doesn't exist
            await self._insert_list(base_path, txn)

        # Get the current length
        try:
            current_length = await self._list_length(base_path, txn)
        except StorageKeyError:
            # Should not happen with proper initialization, but let's be safe
            current_length = 0
            length_path = self._make_path(base_path, self._LENGTH_FIELD)
            await self._storage_set(length_path, cast(TreeValueT, current_length), txn)

        # Append each value
        for i, value in enumerate(values):
            item_path = self._make_path(base_path, str(current_length + i))

            if isinstance(value, dict):
                await self._set_dict(item_path, value, txn)
            elif isinstance(value, list):
                await self._set_list(item_path, value, txn)
            else:
                # Regular value
                await self._storage_set(item_path, value, txn)

        # Update length
        new_length = current_length + len(values)
        length_path = self._make_path(base_path, self._LENGTH_FIELD)
        await self._storage_set(length_path, cast(TreeValueT, new_length), txn)

        # Return new length
        return new_length

    async def list_insert(
        self,
        base_path: TreePath,
        index: int,
        value: TreeValueT,
        txn: AsyncTransactionProtocol[TreeValueT] | None = None,
    ) -> None:
        """
        Insert an item at a specific position in a list node.

        Args:
            base_path: Base path of the list node
            index: Position to insert the value
            value: Value to insert
            txn: Optional transaction to use

        Raises:
            ObjectTypeError: If base_path is not a list node
            ObjectIndexError: If index is out of range
        """
        if txn is None:
            async with await self._storage.transaction() as new_txn:
                await self._list_insert(base_path, index, value, new_txn)
        else:
            await self._list_insert(base_path, index, value, txn)

    async def _list_insert(
        self,
        base_path: TreePath,
        index: int,
        value: TreeValueT,
        txn: AsyncTransactionProtocol[TreeValueT],
    ) -> None:
        """
        Internal implementation for inserting an item in a list node.

        Args:
            base_path: Base path of the list node
            index: Position to insert the value
            value: Value to insert
            txn: Transaction to use

        Raises:
            ObjectTypeError: If base_path is not a list node
            ObjectIndexError: If index is out of range
        """
        # Get current list data
        current_list = await self._list_to_list(base_path, txn)

        # Normalize negative indices
        if index < 0:
            index = len(current_list) + index + 1  # +1 because insert happens before the index

        # Clamp index to valid range (for insert, one past the end is valid)
        index = max(0, min(index, len(current_list)))

        # Perform the insert operation
        current_list.insert(index, value)

        # Store the updated list - this could be optimized but using the direct approach for safety
        await self._set_list(base_path, current_list, txn)

    async def list_remove(
        self,
        base_path: TreePath,
        index: int,
        txn: AsyncTransactionProtocol[TreeValueT] | None = None,
    ) -> None:
        """
        Remove an item from a list node at the specified index.

        Args:
            base_path: Base path of the list node
            index: Index of the item to remove
            txn: Optional transaction to use

        Raises:
            ObjectTypeError: If base_path is not a list node
            ObjectIndexError: If index is out of range
        """
        if txn is None:
            async with await self._storage.transaction() as new_txn:
                await self._list_remove(base_path, index, new_txn)
        else:
            await self._list_remove(base_path, index, txn)

    async def _list_remove(
        self, base_path: TreePath, index: int, txn: AsyncTransactionProtocol[TreeValueT]
    ) -> None:
        """
        Internal implementation for removing an item from a list node.

        Efficiently removes an item by shifting all subsequent items up by one.
        This avoids the need to rebuild the entire list.

        Args:
            base_path: Base path of the list node
            index: Index of the item to remove
            txn: Transaction to use

        Raises:
            ObjectTypeError: If base_path is not a list node
            ObjectIndexError: If index is out of range
        """
        # Verify this is a list node
        await self._verify_list(base_path, txn)

        # Get current length
        length = await self._list_length(base_path, txn)

        # Normalize negative indices
        if index < 0:
            index = length + index

        # Check index
        if index < 0 or index >= length:
            raise ObjectIndexError(f"List index {index} out of range (0-{length - 1})")

        # Remove the item by shifting all subsequent items
        # This is more efficient than rebuilding the entire list
        item_to_remove = self._make_path(base_path, str(index))

        # First, delete the item we're removing
        await self._delete_node(item_to_remove, txn)

        # Shift all subsequent items up by one index
        for i in range(index + 1, length):
            src_path = self._make_path(base_path, str(i))
            dst_path = self._make_path(base_path, str(i - 1))

            # Check if it's a dict or list node
            try:
                if await self._is_dict(src_path, txn):
                    # It's a dictionary node, copy it recursively
                    src_dict = await self._dict_to_dict(src_path, txn)
                    # Delete the destination first in case it exists
                    await self._delete_node(dst_path, txn)
                    # Copy the dictionary
                    await self._set_dict(dst_path, src_dict, txn)
                elif await self._is_list(src_path, txn):
                    # It's a list node, copy it recursively
                    src_list = await self._list_to_list(src_path, txn)
                    # Delete the destination first in case it exists
                    await self._delete_node(dst_path, txn)
                    # Copy the list
                    await self._set_list(dst_path, src_list, txn)
                else:
                    # Regular value
                    value = await self._storage_get(src_path, txn)
                    await self._storage_set(dst_path, value, txn)
            except StorageKeyError:
                # Source path disappeared (rare race condition)
                # Just skip this item
                continue

            # Delete the source after copying
            await self._delete_node(src_path, txn)

        # Update the length
        length_path = self._make_path(base_path, self._LENGTH_FIELD)
        await self._storage_set(length_path, cast(TreeValueT, length - 1), txn)

    # --- List conversion operations --- #

    async def list_to_list(
        self,
        base_path: TreePath,
        txn: AsyncTransactionProtocol[TreeValueT] | None = None,
    ) -> list[TreeValueT]:
        """
        Convert a stored list node to a regular Python list.

        Args:
            base_path: Base path of the list node
            txn: Optional transaction to use

        Returns:
            List containing all items from the stored list node

        Raises:
            ObjectTypeError: If base_path is not a list node
        """
        if txn is None:
            async with await self._storage.transaction() as new_txn:
                result = await self._list_to_list(base_path, new_txn)
            return result
        else:
            return await self._list_to_list(base_path, txn)

    async def _list_to_list(
        self,
        base_path: TreePath,
        txn: AsyncTransactionProtocol[TreeValueT],
    ) -> list[TreeValueT]:
        """
        Internal implementation for converting a stored list node to a Python list.

        Args:
            base_path: Base path of the list node
            txn: Transaction to use

        Returns:
            List containing all items from the stored list node

        Raises:
            ObjectTypeError: If base_path is not a list node
        """
        # Verify this is a list node
        await self._verify_list(base_path, txn)

        # Get list length
        length = await self._list_length(base_path, txn)

        # Build result list
        result: list[Any] = []
        for i in range(length):
            try:
                item = await self._list_get(base_path, i, txn)
                result.append(item)
            except (StorageKeyError, ObjectIndexError):
                # Handle potential race conditions
                # If an item disappeared during iteration, append None as placeholder
                result.append(None)

        return result
