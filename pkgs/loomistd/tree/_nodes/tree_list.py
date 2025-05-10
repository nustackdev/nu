from __future__ import annotations

from typing import TYPE_CHECKING

from loomi.interfaces.state.tree import SyncTreeListProtocol

from .._exceptions import ObjectIndexError
from .._types import TreeValueContainer, TreeValueT
from .tree_node import TreeNode

__all__ = [
    "TreeList",
]


class TreeList(TreeNode[TreeValueT], SyncTreeListProtocol[TreeValueT]):
    """
    A list-like interface to tree storage.

    This class provides an interface similar to a Python list
    for interacting with list nodes in the tree storage.
    It implements methods for list operations that map
    to the underlying tree structure.
    """

    # --- Sync list operations --- #

    def get(self, index: int) -> TreeValueContainer[TreeValueT]:
        """
        Get an item from the list node at the specified index.

        Args:
            index: Index of the item to retrieve

        Returns:
            The item at the specified index

        Raises:
            ObjectIndexError: If the index is out of range
        """
        return self._storage.list_get(self._path, index, self._txn)

    def set(self, index: int, value: TreeValueT) -> None:
        """
        Set an item in the list node at the specified index.

        Args:
            index: Index of the item to set
            value: Value to set

        Raises:
            ObjectIndexError: If the index is out of range
        """
        self._storage.list_set(self._path, index, value, self._txn)

    def append(self, value: TreeValueT) -> int:
        """
        Append an item to the list node.

        Args:
            value: Value to append

        Returns:
            New length of the list
        """
        return self._storage.list_append(self._path, value, self._txn)

    def extend(self, values: list[TreeValueT]) -> int:
        """
        Extend the list node with multiple values.

        Args:
            values: List of values to append

        Returns:
            New length of the list
        """
        return self._storage.list_extend(self._path, values, self._txn)

    def insert(self, index: int, value: TreeValueT) -> None:
        """
        Insert an item at a specific position in the list node.

        Args:
            index: Position to insert the value
            value: Value to insert

        Raises:
            ObjectIndexError: If the index is out of range
        """
        self._storage.list_insert(self._path, index, value, self._txn)

    def delete(self, index: int) -> None:
        """
        Remove an item from the list node at the specified index.

        Args:
            index: Index of the item to remove

        Raises:
            ObjectIndexError: If the index is out of range
        """
        self._storage.list_remove(self._path, index, self._txn)

    def length(self) -> int:
        """
        Get the length of the list node.

        Returns:
            Number of items in the list
        """
        return self._storage.list_length(self._path, self._txn)

    # --- List conversion and utilities --- #

    def to_list(self) -> list[TreeValueT]:
        """
        Convert to a regular Python list.

        Returns:
            Python list containing all items from this list node
        """
        return self._storage.list_to_list(self._path, self._txn)

    def clear(self) -> None:
        """
        Remove all items from the list node.
        """
        # Get the current length and remove items one by one from the end
        length = self.length()
        for i in range(length - 1, -1, -1):
            try:
                self.delete(i)
            except ObjectIndexError:
                # Index became invalid, just skip it
                pass

    def pop(self, index: int = -1) -> TreeValueContainer[TreeValueT]:
        """
        Remove and return an item from the list node.

        Args:
            index: Index of the item to remove (default: last item)

        Returns:
            The item at the specified index

        Raises:
            ObjectIndexError: If the index is out of range
        """
        value = self.get(index)
        self.delete(index)
        return value

    def __len__(self) -> int:
        """
        Get the number of items in the list node.

        Returns:
            The number of items
        """
        return self.length()


if TYPE_CHECKING:
    _: type[SyncTreeListProtocol] = TreeList
