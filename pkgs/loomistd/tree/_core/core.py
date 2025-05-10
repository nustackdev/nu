from __future__ import annotations

from typing import Generator, Generic, cast

from loomi.interfaces.state.kv import SyncStorageProtocol, SyncTransactionProtocol
from loomi.interfaces.state.tree import EmptyProtocol
from loomistd.kv import StorageKeyError

from .._exceptions import ObjectTypeError
from .._types import TreePath, TreePathComponent, TreeValueContainer, TreeValueT

__all__ = [
    "StorageCore",
    "Empty",
]


class Empty(EmptyProtocol):
    """Sentinel object representing an empty value, distinct from None."""

    def __repr__(self) -> str:
        return "<Empty>"


class StorageCore(Generic[TreeValueT]):
    """
    Base class for tree storage operations providing core utilities.

    This class contains the foundational methods for interacting with the
    underlying storage layer, handling path construction, type detection,
    and common operations on nodes and subtrees.

    The core philosophy is to ensure complete isolation between the tree storage
    operations and the underlying flat key-value storage implementation, while
    maintaining robust error handling and type safety.
    """

    # Markers for node metadata and types

    _MARKER: str = "\ue000"
    # The Private Use Area (PUA) is a range of Unicode code points (U+E000 to U+F8FF)
    # that are intentionally not assigned to any standard characters.
    # Using PUA characters virtually eliminates the risk of collision since:
    # - They don't appear on standard keyboards
    # - They're not used in any human writing systems
    # - They have no standard visual representation

    # Special markers are used to identify the type of node:
    _TYPE_DICT: str = _MARKER + "DICT"  # Dictionary node marker
    _TYPE_LIST: str = _MARKER + "LIST"  # List node marker
    _LENGTH_FIELD: str = _MARKER + "LEN"  # Length field for lists

    # Special sentinels
    EMPTY: EmptyProtocol = Empty()  # Sentinel for empty values

    def __init__(self, storage: SyncStorageProtocol[TreeValueT]):
        """
        Initialize the storage core.

        Args:
            storage: The underlying key-value storage implementation
        """
        self._storage = storage

    # --- Core utility methods --- #

    def _make_path(self, base_path: TreePath, *components: TreePathComponent) -> TreePath:
        """
        Create a tree path by appending components to the base path.

        Args:
            base_path: The base path to extend
            *components: Path components to append to the path

        Returns:
            A new tree path

        Raises:
            TypeError: If base_path is not a tuple
        """
        if not isinstance(base_path, tuple):
            raise TypeError("Base path must be a tuple")
        return base_path + tuple(components)  # type: ignore

    def _storage_get(
        self,
        path: TreePath,
        txn: SyncTransactionProtocol[TreeValueT] | None = None,
    ) -> TreeValueT:
        """
        Get a value from the underlying key-value storage, using transaction if provided.

        Args:
            path: The tree path to get the value for
            txn: Optional transaction to use

        Returns:
            The value associated with the path

        Raises:
            StorageKeyError: If the path doesn't exist in the underlying storage
        """
        if txn is not None:
            return txn.get(path)
        return self._storage.get(path)

    def _storage_set(
        self,
        path: TreePath,
        value: TreeValueT,
        txn: SyncTransactionProtocol[TreeValueT] | None = None,
    ) -> None:
        """
        Set a value in the underlying key-value storage, using transaction if provided.

        Args:
            path: The tree path to set the value for
            value: The value to set
            txn: Optional transaction to use
        """
        if txn is not None:
            txn.set(path, value)
        else:
            self._storage.set(path, value)

    def _storage_delete(
        self,
        path: TreePath,
        txn: SyncTransactionProtocol[TreeValueT] | None = None,
    ) -> None:
        """
        Delete a value from the underlying key-value storage, using transaction if provided.

        Args:
            path: The tree path to delete
            txn: Optional transaction to use

        Raises:
            StorageKeyError: If the path doesn't exist
        """
        if txn is not None:
            txn.delete(path)
        else:
            self._storage.delete(path)

    def _storage_exists(
        self,
        path: TreePath,
        txn: SyncTransactionProtocol[TreeValueT] | None = None,
    ) -> bool:
        """
        Check if a path exists in the underlying key-value storage, using transaction if provided.

        Args:
            path: The tree path to check
            txn: Optional transaction to use

        Returns:
            True if the path exists, False otherwise
        """
        if txn is not None:
            return txn.exists(path)
        return self._storage.exists(path)

    def _storage_list_paths(
        self,
        prefix: TreePath,
        depth: int = 1,
        txn: SyncTransactionProtocol[TreeValueT] | None = None,
    ) -> Generator[TreePath, None]:
        """
        List paths with the given prefix from storage, using transaction if provided.

        This allows navigation of the tree structure by listing all paths
        at a given depth from the specified prefix path.

        Args:
            prefix: The prefix path to search for
            depth: How many levels deep to search (-1 for unlimited)
            txn: Optional transaction to use

        Yields:
            Tree paths matching the prefix
        """
        if txn is not None:
            for path in txn.list_keys(prefix, depth):
                yield path
        else:
            for path in self._storage.list_keys(prefix, depth):
                yield path

    # --- Node type detection --- #

    def _get_node_type(
        self,
        path: TreePath,
        txn: SyncTransactionProtocol[TreeValueT] | None = None,
    ) -> str | None:
        """
        Get the type of a node at a specific path in the tree.

        Args:
            path: The tree path to check
            txn: Optional transaction to use

        Returns:
            _TYPE_DICT, _TYPE_LIST, or None (for primitive values)

        Raises:
            StorageKeyError: If the path doesn't exist
        """
        # This will raise StorageKeyError if path doesn't exist
        value = self._storage_get(path, txn)

        if value == self._TYPE_DICT or value == self._TYPE_LIST:
            return cast(str, value)
        return None  # Not a dict or list node but a primitive value

    def _is_dict(
        self,
        path: TreePath,
        txn: SyncTransactionProtocol[TreeValueT] | None = None,
    ) -> bool:
        """
        Check if a path contains a dictionary node.

        Args:
            path: The tree path to check
            txn: Optional transaction to use

        Returns:
            True if the path contains a dictionary node, False otherwise

        Note:
            Returns False if the path doesn't exist (doesn't raise StorageKeyError)
        """
        try:
            node_type = self._get_node_type(path, txn)
            return node_type == self._TYPE_DICT
        except StorageKeyError:
            return False

    def _is_list(
        self,
        path: TreePath,
        txn: SyncTransactionProtocol[TreeValueT] | None = None,
    ) -> bool:
        """
        Check if a path contains a list node.

        Args:
            path: The tree path to check
            txn: Optional transaction to use

        Returns:
            True if the path contains a list node, False otherwise

        Note:
            Returns False if the path doesn't exist (doesn't raise StorageKeyError)
        """
        try:
            node_type = self._get_node_type(path, txn)
            return node_type == self._TYPE_LIST
        except StorageKeyError:
            return False

    def _is_primitive(
        self,
        path: TreePath,
        txn: SyncTransactionProtocol[TreeValueT] | None = None,
    ) -> bool:
        """
        Check if a path contains a primitive value (not a dict or list node).

        Args:
            path: The tree path to check
            txn: Optional transaction to use

        Returns:
            True if the path contains a primitive value, False otherwise

        Note:
            Returns False if the path doesn't exist (doesn't raise StorageKeyError)
        """
        try:
            node_type = self._get_node_type(path, txn)
            return node_type is None  # None indicates a primitive value
        except StorageKeyError:
            return False

    def _verify_dict(
        self,
        path: TreePath,
        txn: SyncTransactionProtocol[TreeValueT] | None = None,
    ) -> None:
        """
        Verify that a path contains a dictionary node or raise an error.

        Args:
            path: The tree path to check
            txn: Optional transaction to use

        Raises:
            ObjectTypeError: If the path exists but is not a dictionary node
            StorageKeyError: If the path doesn't exist
        """
        node_type = self._get_node_type(path, txn)
        if node_type != self._TYPE_DICT:
            raise ObjectTypeError(f"Path {path} is not a dictionary node")

    def _verify_list(
        self,
        path: TreePath,
        txn: SyncTransactionProtocol[TreeValueT] | None = None,
    ) -> None:
        """
        Verify that a path contains a list node or raise an error.

        Args:
            path: The tree path to check
            txn: Optional transaction to use

        Raises:
            ObjectTypeError: If the path exists but is not a list node
            StorageKeyError: If the path doesn't exist
        """
        node_type = self._get_node_type(path, txn)
        if node_type != self._TYPE_LIST:
            raise ObjectTypeError(f"Path {path} is not a list node")

    # --- Subtree deletion --- #

    def _delete_node(  # noqa: C901
        self, path: TreePath, txn: SyncTransactionProtocol[TreeValueT]
    ) -> None:
        """
        Delete a node and all its nested values from the tree.

        It traverses the node and removes all child nodes, handling both dictionary
        and list nodes, including all their nested structures.

        Args:
            path: Tree path of the node to delete
            txn: Transaction to use

        Note:
            If the path doesn't exist or is not a dict/list node, this method
            will attempt to delete it anyway without raising an error.
        """
        # Check if it's a dict or list node
        try:
            node_type = self._get_node_type(path, txn)

            # If it's not a dict or list node, try to delete it directly
            if node_type is None:
                try:
                    self._storage_delete(path, txn)
                except StorageKeyError:
                    # Path doesn't exist, nothing to do
                    pass
                return

            # Special handling for lists - delete length field
            if node_type == self._TYPE_LIST:
                length_path = self._make_path(path, self._LENGTH_FIELD)
                try:
                    self._storage_delete(length_path, txn)
                except StorageKeyError:
                    # Length field might not exist (corrupted data)
                    pass

            # Collect all non-compound paths to delete
            paths_to_delete = []

            # Get all paths in the subtree (for nested values)
            for storage_path in self._storage_list_paths(path, depth=-1, txn=txn):
                # Skip the path itself (will be processed separately)
                if storage_path == path:
                    continue

                # Check if it's a nested subtree
                try:
                    nested_node_type = self._get_node_type(storage_path, txn)
                    if nested_node_type is not None:
                        # It's a nested dict or list node, delete recursively
                        self._delete_node(storage_path, txn)
                    else:
                        # Not a dict or list node, add to list to delete
                        paths_to_delete.append(storage_path)
                except StorageKeyError:
                    # Path disappeared during iteration (concurrent modification)
                    continue

            # Delete all collected paths
            for p in paths_to_delete:
                try:
                    self._storage_delete(p, txn)
                except StorageKeyError:
                    # May have been deleted as part of nested cleanup or by another process
                    pass

            # Finally, delete the node type marker itself
            try:
                self._storage_delete(path, txn)
            except StorageKeyError:
                # Already deleted
                pass

        except StorageKeyError:
            # Path doesn't exist, nothing to do
            pass

    # --- Recursive value retrieval --- #

    def _get_value_recursive(
        self,
        path: TreePath,
        txn: SyncTransactionProtocol[TreeValueT],
    ) -> TreeValueContainer[TreeValueT]:
        """
        Get a value, recursively resolving dict and list nodes in the tree.

        This helper method checks if a path points to a dict or list node
        and if so, returns the full value by traversing the subtree.
        Used by both dictionary and list operations to retrieve values that
        might be nested nodes.

        Args:
            path: Tree path to get value for
            txn: Transaction to use

        Returns:
            The value, with any dict or list nodes fully resolved

        Raises:
            StorageKeyError: If the path doesn't exist
        """
        # Check if it's a dict or list node
        node_type = self._get_node_type(path, txn)

        if node_type == self._TYPE_DICT:
            # It's a dictionary node, get all its contents recursively
            return self._dict_to_dict(path, txn)
        elif node_type == self._TYPE_LIST:
            # It's a list node, get all its contents recursively
            return self._list_to_list(path, txn)
        else:
            # Not a dict or list node, return direct value
            return self._storage_get(path, txn)

    # --- Placeholder methods for node conversion --- #
    # These will be implemented in the derived classes

    def _dict_to_dict(
        self,
        path: TreePath,
        txn: SyncTransactionProtocol[TreeValueT],
    ) -> dict[str, TreeValueT]:
        """
        Convert a stored dictionary node to a regular Python dictionary.

        This method traverses the subtree starting at the given path and
        reconstructs a Python dictionary from the flattened key-value storage.

        Args:
            path: Base path of the dictionary node
            txn: Transaction to use

        Returns:
            Dict containing all data from the stored dictionary node

        Raises:
            NotImplementedError: This base method must be overridden
        """
        raise NotImplementedError("Must be implemented by derived class")

    def _list_to_list(
        self,
        path: TreePath,
        txn: SyncTransactionProtocol[TreeValueT],
    ) -> list[TreeValueT]:
        """
        Convert a stored list node to a regular Python list.

        This method traverses the subtree starting at the given path and
        reconstructs a Python list from the flattened index-value storage.

        Args:
            path: Base path of the list node
            txn: Transaction to use

        Returns:
            List containing all items from the stored list node

        Raises:
            NotImplementedError: This base method must be overridden
        """
        raise NotImplementedError("Must be implemented by derived class")

    # --- Placeholder methods for node creation --- #
    # These will be implemented in the derived classes

    def _set_dict(
        self,
        path: TreePath,
        value: dict[str, TreeValueT],
        txn: SyncTransactionProtocol[TreeValueT],
    ) -> None:
        """
        Store a dictionary as a subtree in the tree storage.

        This method takes a Python dictionary and stores it in the tree
        by flattening it into individual key-value pairs in the underlying
        key-value storage.

        Args:
            path: Base path for the dictionary node
            value: Dictionary to store
            txn: Transaction to use

        Raises:
            NotImplementedError: This base method must be overridden
        """
        raise NotImplementedError("Must be implemented by derived class")

    def _set_list(
        self,
        path: TreePath,
        value: list[TreeValueT],
        txn: SyncTransactionProtocol[TreeValueT],
    ) -> None:
        """
        Store a list as a subtree in the tree storage.

        This method takes a Python list and stores it in the tree
        by flattening it into individual index-value pairs in the
        underlying key-value storage.

        Args:
            path: Base path for the list node
            value: List to store
            txn: Transaction to use

        Raises:
            NotImplementedError: This base method must be overridden
        """
        raise NotImplementedError("Must be implemented by derived class")
