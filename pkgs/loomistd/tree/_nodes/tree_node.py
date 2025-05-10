from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING, Any, Callable, Generic, cast, overload

from loomi.interfaces.state.kv import SyncTransactionProtocol
from loomi.interfaces.state.tree import (
    EmptyProtocol,
    SyncTreeDictProtocol,
    SyncTreeListProtocol,
    SyncTreeNodeProtocol,
)

from .._core import StorageCore
from .._types import TreePath, TreePathComponent, TreeValueContainer, TreeValueT

if TYPE_CHECKING:
    from .._core import TreeStorage

__all__ = [
    "TreeNode",
]


class TreeNode(Generic[TreeValueT], ABC):
    """
    Abstract base class for tree node objects.

    This class provides common functionality for both TreeDict and TreeList classes,
    allowing them to share code for nested node access, transformations, filtering,
    and other common tree operations.

    TreeNode serves as a consistent interface for working with nodes in the tree,
    regardless of their type (dictionary or list).
    """

    EMPTY: EmptyProtocol = StorageCore.EMPTY

    @property
    def is_sync(self) -> bool:
        """
        Check if the node is synchronous.

        Returns:
            True if the node is synchronous, False otherwise
        """
        return True

    def __init__(
        self,
        storage: TreeStorage[TreeValueT],
        path: TreePath,
        txn: SyncTransactionProtocol[TreeValueT] | None = None,
    ):
        """
        Initialize a tree node interface.

        Args:
            storage: The TreeStorage instance
            path: The base path for this tree node
            txn: Optional transaction to use
        """
        self._storage = storage
        self._path = path
        self._txn = txn

    @property
    def path(self) -> TreePath:
        """
        Get the base path for this tree node.

        Returns:
            The base path
        """
        return self._path

    def dict(
        self,
        path: TreePathComponent,
        /,
        *paths: TreePathComponent,
        txn: SyncTransactionProtocol[TreeValueT] | None = None,
    ) -> SyncTreeDictProtocol[TreeValueT]:
        """
        Get a nested dictionary node interface.

        Args:
            path: First path segment
            *paths: Additional path segments
            txn: Optional transaction to use

        Returns:
            A new TreeDict instance for the nested dictionary node
        """
        rel_path = self._make_relative_path(path, *paths)
        combined_path = self._combine_paths(self._path, rel_path)
        return self._storage.dict(combined_path, txn or self._txn)

    def list(
        self,
        path: TreePathComponent,
        /,
        *paths: TreePathComponent,
        txn: SyncTransactionProtocol[TreeValueT] | None = None,
    ) -> SyncTreeListProtocol[TreeValueT]:
        """
        Get a nested list node interface.

        Args:
            path: First path segment
            *paths: Additional path segments
            txn: Optional transaction to use

        Returns:
            A new TreeList instance for the nested list node
        """
        rel_path = self._make_relative_path(path, *paths)
        combined_path = self._combine_paths(self._path, rel_path)
        return self._storage.list(combined_path, txn or self._txn)

    @overload
    def remove(
        self,
        txn: SyncTransactionProtocol[TreeValueT] | None = None,
    ) -> None: ...

    @overload
    def remove(
        self,
        path: TreePathComponent,
        /,
        *paths: TreePathComponent,
        txn: SyncTransactionProtocol[TreeValueT] | None = None,
    ) -> None: ...

    def remove(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """
        Delete a node from the tree.

        When called with no path arguments, deletes the current node.
        When called with path segments, deletes the specified nested node.

        Args:
            path: Optional first path segment
            *paths: Additional path segments
            txn: Optional transaction to use
        """
        target_path, txn = self._process_path_args(args, kwargs)
        self._storage.delete_node(target_path, txn)

    @overload
    def exists(
        self,
        txn: SyncTransactionProtocol[TreeValueT] | None = None,
    ) -> bool: ...

    @overload
    def exists(
        self,
        path: TreePathComponent,
        /,
        *paths: TreePathComponent,
        txn: SyncTransactionProtocol[TreeValueT] | None = None,
    ) -> bool: ...

    def exists(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> bool:
        """
        Check if a node exists in the tree.

        When called with no path arguments, checks if the current node exists.
        When called with path segments, checks if the specified nested node exists.

        Args:
            path: Optional first path segment
            *paths: Additional path segments
            txn: Optional transaction to use

        Returns:
            True if the node exists, False otherwise
        """
        target_path, txn = self._process_path_args(args, kwargs)
        return self._storage.exists(target_path, txn)

    @overload
    def is_dict(
        self,
        txn: SyncTransactionProtocol[TreeValueT] | None = None,
    ) -> bool: ...

    @overload
    def is_dict(
        self,
        path: TreePathComponent,
        /,
        *paths: TreePathComponent,
        txn: SyncTransactionProtocol[TreeValueT] | None = None,
    ) -> bool: ...

    def is_dict(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> bool:
        """
        Check if a node is a dictionary node.

        When called with no path arguments, checks if the current node is a dictionary.
        When called with path segments, checks if the specified nested node is a dictionary.

        Args:
            path: Optional first path segment
            *paths: Additional path segments
            txn: Optional transaction to use

        Returns:
            True if the node is a dictionary, False otherwise
        """
        target_path, txn = self._process_path_args(args, kwargs)
        return self._storage.is_dict(target_path, txn)

    @overload
    def is_list(
        self,
        txn: SyncTransactionProtocol[TreeValueT] | None = None,
    ) -> bool: ...

    @overload
    def is_list(
        self,
        path: TreePathComponent,
        /,
        *paths: TreePathComponent,
        txn: SyncTransactionProtocol[TreeValueT] | None = None,
    ) -> bool: ...

    def is_list(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> bool:
        """
        Check if a node is a list node.

        When called with no path arguments, checks if the current node is a list.
        When called with path segments, checks if the specified nested node is a list.

        Args:
            path: Optional first path segment
            *paths: Additional path segments
            txn: Optional transaction to use

        Returns:
            True if the node is a list, False otherwise
        """
        target_path, txn = self._process_path_args(args, kwargs)
        return self._storage.is_list(target_path, txn)

    @overload
    def to_python_object(
        self,
        txn: SyncTransactionProtocol[TreeValueT] | None = None,
    ) -> TreeValueContainer[TreeValueT]: ...

    @overload
    def to_python_object(
        self,
        path: TreePathComponent,
        /,
        *paths: TreePathComponent,
        txn: SyncTransactionProtocol[TreeValueT] | None = None,
    ) -> TreeValueContainer[TreeValueT]: ...

    def to_python_object(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> TreeValueContainer[TreeValueT]:
        """
        Convert a node to a standard Python object.

        When called with no path arguments, converts the current node.
        When called with path segments, converts the specified nested node.

        Args:
            path: Optional first path segment
            *paths: Additional path segments
            txn: Optional transaction to use

        Returns:
            The Python representation of the node

        Raises:
            StorageKeyError: If the node doesn't exist
        """
        target_path, txn = self._process_path_args(args, kwargs)
        return self._storage.to_python_object(target_path, txn)

    def copy_to(
        self,
        target: TreePathComponent,
        /,
        *targets: TreePathComponent,
        txn: SyncTransactionProtocol[TreeValueT] | None = None,
    ) -> None:
        """
        Create a copy of this node at another location in the tree.

        Args:
            target: First segment of the target path
            *targets: Additional segments of the target path
            txn: Optional transaction to use
        """
        target_path = self._make_relative_path(target, *targets)
        self._storage.copy_node(self._path, target_path, txn or self._txn)

    def move_to(
        self,
        target: TreePathComponent,
        /,
        *targets: TreePathComponent,
        txn: SyncTransactionProtocol[TreeValueT] | None = None,
    ) -> None:
        """
        Move this node to another location in the tree.

        This operation is atomic - either the move completes successfully,
        or no changes are made to the tree.

        Args:
            target: First segment of the target path
            *targets: Additional segments of the target path
            txn: Optional transaction to use

        Note:
            After this operation, the current TreeNode instance should not be used
            as its path is no longer valid.
        """
        target_path = self._make_relative_path(target, *targets)
        self._storage.move_node(self._path, target_path, txn or self._txn)

    @overload
    def transform(
        self,
        transform_func: Callable[[TreeValueContainer[TreeValueT]], TreeValueT],
        txn: SyncTransactionProtocol[TreeValueT] | None = None,
    ) -> None: ...

    @overload
    def transform(
        self,
        transform_func: Callable[[TreeValueContainer[TreeValueT]], TreeValueT],
        path: TreePathComponent,
        /,
        *paths: TreePathComponent,
        txn: SyncTransactionProtocol[TreeValueT] | None = None,
    ) -> None: ...

    def transform(
        self,
        transform_func: Callable[[TreeValueContainer[TreeValueT]], TreeValueT],
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """
        Apply a transformation function to a node.

        The transformation function takes the current value as a Python object
        and returns a new transformed Python object.

        When called with just the transform function, transforms the current node.
        When called with path segments, transforms the specified nested node.

        Args:
            transform_func: Function that takes a Python object and returns a transformed version
            path: Optional first path segment
            *paths: Additional path segments
            txn: Optional transaction to use

        Raises:
            StorageKeyError: If the node doesn't exist
            TypeError: If the transformation result is not of a compatible type
        """
        target_path, txn = self._process_path_args(args, kwargs)
        self._storage.transform_node(target_path, transform_func, txn)

    @overload
    def filter(
        self,
        filter_func: (
            Callable[[TreeValueContainer[TreeValueT]], bool]
            | Callable[[str, TreeValueContainer[TreeValueT]], bool]
        ),
        txn: SyncTransactionProtocol[TreeValueT] | None = None,
    ) -> None: ...

    @overload
    def filter(
        self,
        filter_func: (
            Callable[[TreeValueContainer[TreeValueT]], bool]
            | Callable[[str, TreeValueContainer[TreeValueT]], bool]
        ),
        path: TreePathComponent,
        /,
        *paths: TreePathComponent,
        txn: SyncTransactionProtocol[TreeValueT] | None = None,
    ) -> None: ...

    def filter(
        self,
        filter_func: (
            Callable[[TreeValueContainer[TreeValueT]], bool]
            | Callable[[str, TreeValueContainer[TreeValueT]], bool]
        ),
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """
        Filter elements of a list or dictionary node.

        For list nodes, filter_func takes (value) and returns a boolean.
        For dictionary nodes, filter_func takes (key, value) and returns a boolean.

        Elements for which filter_func returns False will be removed.

        When called with just the filter function, filters the current node.
        When called with path segments, filters the specified nested node.

        Args:
            filter_func: Function that takes elements and returns whether to keep them
            path: Optional first path segment
            *paths: Additional path segments
            txn: Optional transaction to use

        Raises:
            ObjectTypeError: If the node is neither a list nor a dictionary
            StorageKeyError: If the node doesn't exist
        """
        target_path, txn = self._process_path_args(args, kwargs)
        self._storage.filter_node(target_path, filter_func, txn)

    @overload
    def map(
        self,
        map_func: Callable[[TreeValueContainer[TreeValueT]], TreeValueT],
        txn: SyncTransactionProtocol[TreeValueT] | None = None,
    ) -> None: ...

    @overload
    def map(
        self,
        map_func: Callable[[TreeValueContainer[TreeValueT]], TreeValueT],
        path: TreePathComponent,
        /,
        *paths: TreePathComponent,
        txn: SyncTransactionProtocol[TreeValueT] | None = None,
    ) -> None: ...

    def map(
        self,
        map_func: Callable[[TreeValueContainer[TreeValueT]], TreeValueT],
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """
        Apply a mapping function to each element in a list or dictionary node.

        For list nodes, each element is replaced with the result of map_func(element).
        For dictionary nodes, each value is replaced with the result of map_func(value).

        This is a convenience method that transforms the node by applying the map function
        to each element while preserving the structure.

        When called with just the map function, maps the current node elements.
        When called with path segments, maps the specified nested node elements.

        Args:
            map_func: Function to apply to each element
            path: Optional first path segment
            *paths: Additional path segments
            txn: Optional transaction to use

        Raises:
            ObjectTypeError: If the node is neither a list nor a dictionary
            StorageKeyError: If the node doesn't exist
            TypeError: If the mapping result contains unsupported types
        """
        target_path, txn = self._process_path_args(args, kwargs)

        # Get the current value
        value = self._storage.to_python_object(target_path, txn)

        # Apply mapping based on type
        if isinstance(value, list):
            # Map each list element
            mapped_value = [map_func(item) for item in value]
            self._storage.store_python_object(target_path, cast(TreeValueT, mapped_value), txn)
        elif isinstance(value, dict):
            # Map each dictionary value
            mapped_value = {key: map_func(val) for key, val in value.items()}
            self._storage.store_python_object(target_path, cast(TreeValueT, mapped_value), txn)
        else:
            # For primitive values, apply transform directly
            self._storage.transform_node(target_path, lambda x: map_func(x), txn)

    @overload
    def store(
        self,
        value: TreeValueT,
        txn: SyncTransactionProtocol[TreeValueT] | None = None,
    ) -> None: ...

    @overload
    def store(
        self,
        value: TreeValueT,
        path: TreePathComponent,
        /,
        *paths: TreePathComponent,
        txn: SyncTransactionProtocol[TreeValueT] | None = None,
    ) -> None: ...

    def store(
        self,
        value: TreeValueT,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """
        Store a Python object at a specified node.

        This is a convenience method for directly storing Python objects
        (dictionaries, lists, or primitive values) in the tree.

        When called with just the value, replaces the current node.
        When called with path segments, stores at the specified nested node.

        Args:
            value: Python object to store
            path: Optional first path segment
            *paths: Additional path segments
            txn: Optional transaction to use

        Raises:
            TypeError: If the value is of an unsupported type
        """
        target_path, txn = self._process_path_args(args, kwargs)
        self._storage.store_python_object(target_path, value, txn)

    def _process_path_args(self, args, kwargs):
        """
        Process variable arguments to extract path and transaction.

        Args:
            args: Positional arguments passed to the method
            kwargs: Keyword arguments passed to the method

        Returns:
            tuple: (target_path, txn)
                - target_path: Combined path to operate on
                - txn: Transaction to use
        """
        txn = kwargs.get("txn")

        # Handle case where the first argument might be a transaction
        if args and isinstance(args[0], SyncTransactionProtocol):
            txn = args[0]
            args = args[1:]

        # If we have path segments, construct the path
        if args:
            rel_path = self._make_relative_path(args[0], *args[1:])
            target_path = self._combine_paths(self._path, rel_path)
        else:
            # No path segments means we're operating on the current node
            target_path = self._path

        return target_path, txn or self._txn

    def _make_relative_path(self, path: TreePathComponent, *paths: TreePathComponent) -> TreePath:
        """
        Create a relative path from path segments.

        Args:
            path: First path segment
            *paths: Additional path segments

        Returns:
            A tuple path formed from the segments
        """
        return (path,) + paths

    def _combine_paths(self, base_path: TreePath, additional_path: TreePath) -> TreePath:
        """
        Combine two paths into a single path.

        Args:
            base_path: The base path
            additional_path: The additional path to append

        Returns:
            The combined path

        Raises:
            TypeError: If paths are not tuples
        """
        if not isinstance(base_path, tuple) or not isinstance(additional_path, tuple):
            raise TypeError("Paths must be tuples")
        return base_path + additional_path


if TYPE_CHECKING:
    _: type[SyncTreeNodeProtocol] = TreeNode
