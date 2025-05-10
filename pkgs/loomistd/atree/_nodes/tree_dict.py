from __future__ import annotations

from typing import TYPE_CHECKING

from loomi.interfaces.state.tree import AsyncTreeDictProtocol, EmptyProtocol

from .._exceptions import ObjectKeyError
from .._types import TreePathComponent, TreeValueContainer, TreeValueT
from .tree_node import TreeNode

__all__ = [
    "TreeDict",
]


class TreeDict(TreeNode[TreeValueT], AsyncTreeDictProtocol[TreeValueT]):
    """
    A dictionary-like interface to tree storage.

    This class provides an interface similar to a Python dictionary
    for interacting with dictionary nodes in the tree storage.
    It implements async methods for dictionary operations that map
    to the underlying tree structure.
    """

    # --- Async dictionary operations --- #

    async def get(
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
        return await self._storage.dict_get(self._path, complete_path, default, self._txn)

    async def set(
        self, path: TreePathComponent, /, *paths: TreePathComponent, value: TreeValueT
    ) -> None:
        """
        Set a value in the dictionary node.

        Args:
            path: First path segment
            *paths_and_value: Additional path segments followed by the value to set

        Raises:
            ValueError: If no value is provided
        """
        complete_path = (path,) + tuple(paths)
        await self._storage.dict_set(self._path, complete_path, value, self._txn)

    async def delete(self, path: TreePathComponent, /, *paths: TreePathComponent) -> None:
        """
        Delete a path from the dictionary node.

        Args:
            path: First path segment
            *paths: Additional path segments

        Raises:
            ObjectKeyError: If the path doesn't exist
        """
        complete_path = (path,) + paths
        await self._storage.dict_delete(self._path, complete_path, self._txn)

    async def contains(self, path: TreePathComponent, /, *paths: TreePathComponent) -> bool:
        """
        Check if a path exists in the dictionary node.

        Args:
            path: First path segment
            *paths: Additional path segments

        Returns:
            True if the path exists, False otherwise
        """
        complete_path = (path,) + paths
        return await self._storage.dict_contains(self._path, complete_path, self._txn)

    async def keys(self) -> list[TreePathComponent]:
        """
        Get all top-level keys in the dictionary node.

        Returns:
            List of keys in the dictionary
        """
        return await self._storage.dict_keys(self._path, self._txn)

    async def values(self) -> list[TreeValueT]:
        """
        Get all top-level values in the dictionary node.

        Returns:
            List of values in the dictionary
        """
        return await self._storage.dict_values(self._path, self._txn)

    async def items(self) -> list[tuple[TreePathComponent, TreeValueT]]:
        """
        Get all top-level key-value pairs in the dictionary node.

        Returns:
            List of (key, value) tuples
        """
        return await self._storage.dict_items(self._path, self._txn)

    # --- Dictionary conversion and utilities --- #

    async def to_dict(self) -> dict[TreePathComponent, TreeValueT]:
        """
        Convert to a regular Python dictionary.

        Returns:
            Python dictionary containing all data from this dictionary node
        """
        return await self._storage.dict_to_dict(self._path, self._txn)

    async def update(self, other: dict[TreePathComponent, TreeValueT]) -> None:
        """
        Update the dictionary node with key-value pairs from another dictionary.

        Args:
            other: Dictionary containing key-value pairs to update
        """
        for key, value in other.items():
            await self.set(key, value=value)

    async def clear(self) -> None:
        """
        Remove all items from the dictionary node.
        """
        # Get all keys first, then delete them one by one
        keys = await self.keys()
        for key in keys:
            try:
                await self.delete(key)
            except ObjectKeyError:
                # Key disappeared, just skip it
                pass

    async def pop(
        self, key: TreePathComponent, default: "TreeValueT | EmptyProtocol" = TreeNode.EMPTY
    ) -> "TreeValueContainer[TreeValueT] | EmptyProtocol":
        """
        Remove and return a value from the dictionary node.

        Args:
            key: Key to remove
            default: Value to return if key doesn't exist

        Returns:
            The value associated with the key, or default if not found

        Raises:
            ObjectKeyError: If the key doesn't exist and no default is provided
        """
        try:
            value = await self.get(key)  # type: ignore
            await self.delete(key)
            return value
        except ObjectKeyError:
            if default is not None:
                return default
            raise

    async def setdefault(self, key: TreePathComponent, default: TreeValueT = None) -> TreeValueT:
        """
        Return the value for key if it exists, otherwise set it to default.

        Args:
            key: Key to check and potentially set
            default: Value to set and return if key doesn't exist

        Returns:
            The value associated with the key, or default if not found
        """
        if await self.contains(key):
            return await self.get(key)  # type: ignore
        await self.set(key, value=default)
        return default

    async def __len__(self) -> int:
        """
        Get the number of items in the dictionary node.

        Returns:
            The number of items
        """
        keys = await self.keys()
        return len(keys)


if TYPE_CHECKING:
    _: type[AsyncTreeDictProtocol] = TreeDict
