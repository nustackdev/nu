from __future__ import annotations

from typing import TYPE_CHECKING, cast

from loomi.interfaces.state.tree import EmptyProtocol, SyncTreeDictProtocol

from .._exceptions import ObjectKeyError
from .._types import TreePathComponent, TreeValueContainer, TreeValueT
from .tree_node import TreeNode

__all__ = [
    "TreeDict",
]


class TreeDict(TreeNode[TreeValueT], SyncTreeDictProtocol[TreeValueT]):
    """
    A dictionary-like interface to tree storage.

    This class provides an interface similar to a Python dictionary
    for interacting with dictionary nodes in the tree storage.
    It implements methods for dictionary operations that map
    to the underlying tree structure.
    """

    # --- Sync dictionary operations --- #

    def get(
        self,
        path: TreePathComponent,
        /,
        *paths: TreePathComponent,
        default: "TreeValueT | EmptyProtocol" = TreeNode.EMPTY,
    ) -> "TreeValueContainer[TreeValueT] | EmptyProtocol":
        """
        Get a value from the dictionary node.

        Args:
            path: First path segment
            *paths: Additional path segments
            default: Value to return if path doesn't exist

        Returns:
            The value associated with the path, or default if not found
        """
        complete_path = (path,) + paths
        return self._storage.dict_get(self._path, complete_path, default, self._txn)

    def set(self, path: TreePathComponent, /, *paths: TreePathComponent, value: TreeValueT) -> None:
        """
        Set a value in the dictionary node.

        Args:
            path: First path segment
            *paths_and_value: Additional path segments followed by the value to set

        Raises:
            ValueError: If no value is provided
        """
        complete_path = (path,) + tuple(paths)
        self._storage.dict_set(self._path, complete_path, value, self._txn)

    def delete(self, path: TreePathComponent, /, *paths: TreePathComponent) -> None:
        """
        Delete a path from the dictionary node.

        Args:
            path: First path segment
            *paths: Additional path segments

        Raises:
            ObjectKeyError: If the path doesn't exist
        """
        complete_path = (path,) + paths
        self._storage.dict_delete(self._path, complete_path, self._txn)

    def contains(self, path: TreePathComponent, /, *paths: TreePathComponent) -> bool:
        """
        Check if a path exists in the dictionary node.

        Args:
            path: First path segment
            *paths: Additional path segments

        Returns:
            True if the path exists, False otherwise
        """
        complete_path = (path,) + paths
        return self._storage.dict_contains(self._path, complete_path, self._txn)

    def keys(self) -> list[TreePathComponent]:
        """
        Get all top-level keys in the dictionary node.

        Returns:
            List of keys in the dictionary
        """
        return self._storage.dict_keys(self._path, self._txn)

    def values(self) -> list[TreeValueT]:
        """
        Get all top-level values in the dictionary node.

        Returns:
            List of values in the dictionary
        """
        return self._storage.dict_values(self._path, self._txn)

    def items(self) -> list[tuple[TreePathComponent, TreeValueT]]:
        """
        Get all top-level key-value pairs in the dictionary node.

        Returns:
            List of (key, value) tuples
        """
        return self._storage.dict_items(self._path, self._txn)

    # --- Dictionary conversion and utilities --- #

    def to_dict(self) -> dict[TreePathComponent, TreeValueT]:
        """
        Convert to a regular Python dictionary.

        Returns:
            Python dictionary containing all data from this dictionary node
        """
        return self._storage.dict_to_dict(self._path, self._txn)

    def update(self, other: dict[TreePathComponent, TreeValueT]) -> None:
        """
        Update the dictionary node with key-value pairs from another dictionary.

        Args:
            other: Dictionary containing key-value pairs to update
        """
        for key, value in other.items():
            self.set(key, value=value)

    def clear(self) -> None:
        """
        Remove all items from the dictionary node.
        """
        # Get all keys first, then delete them one by one
        keys = self.keys()
        for key in keys:
            try:
                self.delete(key)
            except ObjectKeyError:
                # Key disappeared, just skip it
                pass

    def pop(
        self,
        path: TreePathComponent,
        /,
        *paths: TreePathComponent,
        default: "TreeValueT | EmptyProtocol" = TreeNode.EMPTY,
    ) -> "TreeValueContainer[TreeValueT] | EmptyProtocol":
        """
        Remove and return a value from the dictionary node.

        Args:
            path: First path segment
            *paths: Additional path segments
            default: Value to return if key doesn't exist

        Returns:
            The value associated with the key, or default if not found

        Raises:
            ObjectKeyError: If the key doesn't exist and no default is provided
        """
        complete_path = (path,) + paths
        try:
            value = self.get(*complete_path)
            self.delete(*complete_path)
            return value
        except ObjectKeyError:
            if default is not None:
                return default
            raise

    def setdefault(
        self,
        path: TreePathComponent,
        /,
        *paths: TreePathComponent,
        default: TreeValueT = None,
    ) -> TreeValueContainer[TreeValueT]:
        """
        Return the value for key if it exists, otherwise set it to default.

        Args:
            key: Key to check and potentially set
            default: Value to set and return if key doesn't exist

        Returns:
            The value associated with the key, or default if not found
        """
        complete_path = (path,) + paths
        if self.contains(*complete_path):
            return cast(TreeValueContainer[TreeValueT], self.get(*complete_path))
        self.set(*complete_path, value=default)
        return default

    def __len__(self) -> int:
        """
        Get the number of items in the dictionary node.

        Returns:
            The number of items
        """
        keys = self.keys()
        return len(keys)


if TYPE_CHECKING:
    _: type[SyncTreeDictProtocol] = TreeDict
