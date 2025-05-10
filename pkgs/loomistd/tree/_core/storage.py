from __future__ import annotations

from typing import Any, Callable, cast

from loomi.interfaces.state.kv import SyncStorageProtocol, SyncTransactionProtocol
from loomistd.kv import StorageKeyError

from .._exceptions import ObjectTypeError
from .._nodes.tree_dict import TreeDict
from .._nodes.tree_list import TreeList
from .._types import TreePath, TreeValueT
from .dict_operations import DictOperations
from .list_operations import ListOperations

__all__ = [
    "TreeStorage",
]


class TreeStorage(DictOperations[TreeValueT], ListOperations[TreeValueT]):
    """
    Hierarchical tree storage system built on top of a flat key-value store.

    This class provides a complete tree-based storage interface that maps complex
    nested Python objects (dictionaries and lists) to a flat key-value storage system,
    preserving their structure and relationships while enabling efficient access
    to specific nodes within the tree.

    TreeStorage combines the functionality from both DictOperations and ListOperations
    to provide a complete API for working with hierarchical data structures. Dictionary
    objects become nodes with named branches, while list objects become ordered
    sequences of elements.

    The tree structure allows efficient traversal and manipulation of specific paths
    within the tree without having to retrieve the entire structure.
    """

    def __init__(self, storage: SyncStorageProtocol[TreeValueT]):
        """
        Initialize the tree storage wrapper.

        Args:
            storage: The underlying key-value storage implementation
        """
        super().__init__(storage)

    # --- Public tree node object methods --- #

    def dict(
        self,
        path: TreePath,
        txn: SyncTransactionProtocol[TreeValueT] | None = None,
    ) -> TreeDict[TreeValueT]:
        """
        Get a proxy object for dictionary-like access to a tree node.

        This method creates a TreeDict object that provides a dictionary-like
        interface to interact with the data at the specified path. If the path doesn't
        exist yet, it initializes an empty dictionary node. If the path exists but is not
        a dictionary node, it raises an error.

        Args:
            path: Base path for the dictionary node location
            txn: Optional transaction context to use

        Returns:
            TreeDict instance for accessing the dictionary node

        Raises:
            ObjectTypeError: If the path exists but is not a dictionary node
        """
        if txn is None:
            with self._storage.transaction() as new_txn:
                # Initialize or verify the dictionary node
                self._ensure_dict(path, new_txn)
            return TreeDict(self, path)
        else:
            # Use the provided transaction
            self._ensure_dict(path, txn)
            return TreeDict(self, path, txn)

    def list(
        self,
        path: TreePath,
        txn: SyncTransactionProtocol[TreeValueT] | None = None,
    ) -> TreeList[TreeValueT]:
        """
        Get a proxy object for list-like access to a tree node.

        This method creates a TreeList object that provides a list-like
        interface to interact with the data at the specified path. If the path doesn't
        exist yet, it initializes an empty list node. If the path exists but is not
        a list node, it raises an error.

        Args:
            path: Base path for the list node location
            txn: Optional transaction context to use

        Returns:
            TreeList instance for accessing the list node

        Raises:
            ObjectTypeError: If the path exists but is not a list node
        """
        if txn is None:
            with self._storage.transaction() as new_txn:
                # Initialize or verify the list node
                self._ensure_list(path, new_txn)
            return TreeList(self, path)
        else:
            # Use the provided transaction
            self._ensure_list(path, txn)
            return TreeList(self, path, txn)

    def delete_node(
        self,
        path: TreePath,
        txn: SyncTransactionProtocol[TreeValueT] | None = None,
    ) -> None:
        """
        Delete a node and all its contained values.

        This method deletes the node at the specified path,
        including all nested dictionary and list nodes.

        Args:
            path: Path of the node to delete
            txn: Optional transaction to use
        """
        if txn is None:
            with self._storage.transaction() as new_txn:
                self._delete_node(path, new_txn)
        else:
            self._delete_node(path, txn)

    # --- Utility method for recursive conversion --- #

    def to_python_object(
        self,
        path: TreePath,
        txn: SyncTransactionProtocol[TreeValueT] | None = None,
    ) -> Any:
        """
        Convert a stored tree node to a standard Python object.

        This method detects the type of the node at the specified path and converts
        it to the appropriate Python object (dict, list, or primitive value).

        Args:
            path: Path of the node to convert
            txn: Optional transaction to use

        Returns:
            The Python representation of the stored node

        Raises:
            StorageKeyError: If the path doesn't exist
        """
        if txn is None:
            with self._storage.transaction() as new_txn:
                return self._to_python_object(path, new_txn)
        else:
            return self._to_python_object(path, txn)

    def _to_python_object(
        self,
        path: TreePath,
        txn: SyncTransactionProtocol[TreeValueT],
    ) -> Any:
        """
        Internal implementation for converting a stored tree node.

        Args:
            path: Path of the node to convert
            txn: Transaction to use

        Returns:
            The Python representation of the stored node

        Raises:
            StorageKeyError: If the path doesn't exist
        """
        node_type = self._get_node_type(path, txn)

        if node_type == self._TYPE_DICT:
            # It's a dictionary node
            return self._dict_to_dict(path, txn)
        elif node_type == self._TYPE_LIST:
            # It's a list node
            return self._list_to_list(path, txn)
        else:
            # It's a primitive value node
            return self._storage_get(path, txn)

    # --- Utility method for storing Python objects --- #

    def store_python_object(
        self,
        path: TreePath,
        value: TreeValueT,
        txn: SyncTransactionProtocol[TreeValueT] | None = None,
    ) -> None:
        """
        Store a Python object at the specified path in the tree.

        This method detects the type of the provided value and stores it
        appropriately as a dictionary node, list node, or primitive value.

        Args:
            path: Path where to store the object
            value: Python object to store (dict, list, or primitive value)
            txn: Optional transaction to use

        Raises:
            TypeError: If the value is of an unsupported type
        """
        if txn is None:
            with self._storage.transaction() as new_txn:
                self._store_python_object(path, value, new_txn)
        else:
            self._store_python_object(path, value, txn)

    def _store_python_object(
        self,
        path: TreePath,
        value: TreeValueT,
        txn: SyncTransactionProtocol[TreeValueT],
    ) -> None:
        """
        Internal implementation for storing a Python object in the tree.

        Args:
            path: Path where to store the object
            value: Python object to store
            txn: Transaction to use

        Raises:
            TypeError: If the value is of an unsupported type
        """
        # First, delete any existing data at this path
        try:
            self._delete_node(path, txn)
        except StorageKeyError:
            pass  # Path doesn't exist, nothing to delete

        # Store the value according to its type
        if isinstance(value, dict):
            self._set_dict(path, value, txn)
        elif isinstance(value, list):
            self._set_list(path, value, txn)
        elif value is None or isinstance(value, (str, int, float, bool, bytes)):
            # These are the primitive types that can be stored directly
            self._storage_set(path, cast(TreeValueT, value), txn)
        else:
            # Unsupported type
            raise TypeError(f"Cannot store object of type {type(value).__name__}")

    # --- Utility methods for type checking --- #

    def is_dict(
        self,
        path: TreePath,
        txn: SyncTransactionProtocol[TreeValueT] | None = None,
    ) -> bool:
        """
        Check if a path contains a dictionary node.

        Args:
            path: Path to check
            txn: Optional transaction to use

        Returns:
            True if the path contains a dictionary node, False otherwise
        """
        if txn is None:
            with self._storage.transaction() as new_txn:
                result = self._is_dict(path, new_txn)
            return result
        else:
            return self._is_dict(path, txn)

    def is_list(
        self,
        path: TreePath,
        txn: SyncTransactionProtocol[TreeValueT] | None = None,
    ) -> bool:
        """
        Check if a path contains a list node.

        Args:
            path: Path to check
            txn: Optional transaction to use

        Returns:
            True if the path contains a list node, False otherwise
        """
        if txn is None:
            with self._storage.transaction() as new_txn:
                result = self._is_list(path, new_txn)
            return result
        else:
            return self._is_list(path, txn)

    def exists(
        self,
        path: TreePath,
        txn: SyncTransactionProtocol[TreeValueT] | None = None,
    ) -> bool:
        """
        Check if a path exists in the tree.

        Args:
            path: Path to check
            txn: Optional transaction to use

        Returns:
            True if the path exists, False otherwise
        """
        if txn is None:
            with self._storage.transaction() as new_txn:
                result = self._storage_exists(path, new_txn)
            return result
        else:
            return self._storage_exists(path, txn)

    # --- Utility methods for tree operations --- #

    def copy_node(
        self,
        source_path: TreePath,
        target_path: TreePath,
        txn: SyncTransactionProtocol[TreeValueT] | None = None,
    ) -> None:
        """
        Copy a node from one path to another.

        Args:
            source_path: Path of the source node
            target_path: Path where to copy the node
            txn: Optional transaction to use

        Raises:
            StorageKeyError: If the source path doesn't exist
        """
        if txn is None:
            with self._storage.transaction() as new_txn:
                self._copy_node(source_path, target_path, new_txn)
        else:
            self._copy_node(source_path, target_path, txn)

    def _copy_node(
        self,
        source_path: TreePath,
        target_path: TreePath,
        txn: SyncTransactionProtocol[TreeValueT],
    ) -> None:
        """
        Internal implementation for copying a node.

        Args:
            source_path: Path of the source node
            target_path: Path where to copy the node
            txn: Transaction to use

        Raises:
            StorageKeyError: If the source path doesn't exist
        """
        # Get the node type
        try:
            node_type = self._get_node_type(source_path, txn)

            # Delete any existing data at the target
            self._delete_node(target_path, txn)

            if node_type == self._TYPE_DICT:
                # It's a dictionary node
                source_dict = self._dict_to_dict(source_path, txn)
                self._set_dict(target_path, source_dict, txn)
            elif node_type == self._TYPE_LIST:
                # It's a list node
                source_list = self._list_to_list(source_path, txn)
                self._set_list(target_path, source_list, txn)
            else:
                # It's a primitive value
                value = self._storage_get(source_path, txn)
                self._storage_set(target_path, value, txn)
        except StorageKeyError:
            # Source path doesn't exist
            raise

    def move_node(
        self,
        source_path: TreePath,
        target_path: TreePath,
        txn: SyncTransactionProtocol[TreeValueT] | None = None,
    ) -> None:
        """
        Move a node from one path to another.

        This operation is atomic - either the move completes successfully,
        or no changes are made to the tree.

        Args:
            source_path: Path of the source node
            target_path: Path where to move the node
            txn: Optional transaction to use

        Raises:
            StorageKeyError: If the source path doesn't exist
        """
        if txn is None:
            with self._storage.transaction() as new_txn:
                self._move_node(source_path, target_path, new_txn)
        else:
            self._move_node(source_path, target_path, txn)

    def _move_node(
        self,
        source_path: TreePath,
        target_path: TreePath,
        txn: SyncTransactionProtocol[TreeValueT],
    ) -> None:
        """
        Internal implementation for moving a node.

        Args:
            source_path: Path of the source node
            target_path: Path where to move the node
            txn: Transaction to use

        Raises:
            StorageKeyError: If the source path doesn't exist
        """
        # Copy the node
        self._copy_node(source_path, target_path, txn)

        # Delete the source
        self._delete_node(source_path, txn)

    def transform_node(
        self,
        path: TreePath,
        transform_func: Callable[[TreeValueT], TreeValueT],
        txn: SyncTransactionProtocol[TreeValueT] | None = None,
    ) -> None:
        """
        Apply a transformation function to a tree node.

        The transformation function takes a Python object and returns
        a new transformed Python object.

        Args:
            path: Path of the node to transform
            transform_func: Function that takes a Python object and returns a transformed version
            txn: Optional transaction to use

        Raises:
            StorageKeyError: If the path doesn't exist
            TypeError: If the transformation result is not of a compatible type
        """
        if txn is None:
            with self._storage.transaction() as new_txn:
                self._transform_node(path, transform_func, new_txn)
        else:
            self._transform_node(path, transform_func, txn)

    def _transform_node(
        self,
        path: TreePath,
        transform_func: Callable[[TreeValueT], TreeValueT],
        txn: SyncTransactionProtocol[TreeValueT],
    ) -> None:
        """
        Internal implementation for transforming a tree node.

        Args:
            path: Path of the node to transform
            transform_func: Function that takes a Python object and returns a transformed version
            txn: Transaction to use

        Raises:
            StorageKeyError: If the path doesn't exist
            TypeError: If the transformation result is not of a compatible type
        """
        # Get the current node as a Python object
        obj = self._to_python_object(path, txn)

        # Apply the transformation
        transformed_obj = transform_func(obj)

        # Store the transformed object
        self._store_python_object(path, transformed_obj, txn)

    def filter_node(
        self,
        path: TreePath,
        filter_func: Callable[[TreeValueT], bool] | Callable[[str, TreeValueT], bool],
        txn: SyncTransactionProtocol[TreeValueT] | None = None,
    ) -> None:
        """
        Filter elements of a list or dictionary node using a filter function.

        For list nodes, the filter_func takes (value) and returns a boolean.
        For dictionary nodes, the filter_func takes (key, value) and returns a boolean.

        Args:
            path: Path of the node to filter
            filter_func: Function that takes elements and returns whether to keep them
            txn: Optional transaction to use

        Raises:
            ObjectTypeError: If the node is neither a list nor a dictionary
            StorageKeyError: If the path doesn't exist
        """
        if txn is None:
            with self._storage.transaction() as new_txn:
                self._filter_node(path, filter_func, new_txn)
        else:
            self._filter_node(path, filter_func, txn)

    def _filter_node(
        self,
        path: TreePath,
        filter_func: Callable[[TreeValueT], bool] | Callable[[str, TreeValueT], bool],
        txn: SyncTransactionProtocol[TreeValueT],
    ) -> None:
        """
        Internal implementation for filtering tree nodes.

        Args:
            path: Path of the node to filter
            filter_func: Function that takes elements and returns whether to keep them
            txn: Transaction to use

        Raises:
            ObjectTypeError: If the node is neither a list nor a dictionary
            StorageKeyError: If the path doesn't exist
        """
        # Check the node type
        node_type = self._get_node_type(path, txn)

        if node_type == self._TYPE_LIST:
            # Filter the list node
            items = self._list_to_list(path, txn)
            filter_func_list = cast(Callable[[TreeValueT], bool], filter_func)
            filtered_items = [item for item in items if filter_func_list(item)]

            # Replace with filtered list
            self._set_list(path, filtered_items, txn)

        elif node_type == self._TYPE_DICT:
            # Filter the dictionary node
            items = self._dict_items(path, txn)
            filter_func_dict = cast(Callable[[str, TreeValueT], bool], filter_func)
            keys_to_delete = [k for k, v in items if not filter_func_dict(k, v)]

            # Delete filtered keys
            for k in keys_to_delete:
                self._dict_delete(
                    path,
                    (k,),  # Single component path for the key
                    txn,
                )

        else:
            raise ObjectTypeError(
                f"Node at path {path} must be a list or dictionary node for filtering"
            )
