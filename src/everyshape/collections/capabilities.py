"""Container capability protocols.

These protocols define optional capabilities for container-like objects.
Not all containers support all operations - check protocol support before use.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, TypeGuard, runtime_checkable

from everyshape.view import View


if TYPE_CHECKING:
    from everyshape.storage import CallbackFn, StorageProtocol, Subscription
    from everyshape.types import Empty


__all__ = [
    "Appendable",
    "Assignable",
    "ChildWatchable",
    "Clearable",
    "Containable",
    "Convertible",
    "Deletable",
    "Initializable",
    "Nestable",
    "Sizeable",
    "Subscriptable",
    "Watchable",
    "is_appendable",
    "is_assignable",
    "is_child_watchable",
    "is_clearable",
    "is_containable",
    "is_convertible",
    "is_deletable",
    "is_initializable",
    "is_nestable",
    "is_sizeable",
    "is_subscriptable",
    "is_watchable",
]


# =============================================================================
# CORE CAPABILITY PROTOCOLS
# =============================================================================


@runtime_checkable
class Convertible[V](View, Protocol):
    """Protocol for containers that can convert their contents to Python values.

    Convertible containers can materialize their entire stored state into
    native Python data structures (dict, list, set, etc.).

    Type Parameters:
        T: The type of value this container extracts to

    Example:
        >>> if isinstance(container, Convertible):
        ...     data = container.extract()
        ...     # data is now a native Python dict/list/etc
    """

    def extract(self) -> V | Empty:
        """Extract container contents as native Python value.

        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Native Python value representing container contents
        """
        ...


@runtime_checkable
class Initializable[V](View, Protocol):
    """Protocol for containers that can be initialized from Python values.

    Initializable containers can populate their contents from native Python
    data structures, handling the conversion and storage automatically.

    Type Parameters:
        T: The type of value this container accepts for initialization

    Example:
        >>> if isinstance(container, Initializable):
        ...     container.store({"key": "value"}, replace=True)
    """

    def store(self, value: V) -> None:
        """Store Python value into container.

        Args:
            value: Native Python value to store
            *args: Positional arguments
            replace: If True, clear existing content before storing
            **kwargs: Keyword arguments

        Raises:
            TypeError: If value type not supported
            ValueError: If value format invalid
        """
        ...


@runtime_checkable
class Nestable[A](View, Protocol):
    """Protocol for containers that support navigation to child containers.

    Nestable containers can navigate their hierarchy, returning appropriate
    container instances for child nodes.

    Example:
        >>> if isinstance(container, Nestable):
        ...     child = container.open_child("users", DictView)
        ...     # child is another container at the given location
    """

    def open_child[ViewT: View](self, address: A, view: type[ViewT]) -> ViewT:
        """Navigate to child container.

        Args:
            address: Child container address
            view: View to open child container with
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Container instance for child

        Raises:
            KeyError: If child doesn't exist
            TypeError: If child is not a container
        """
        ...


@runtime_checkable
class Subscriptable[A, V](View, Protocol):
    """Protocol for containers that support item access via subscript notation.

    Subscriptable containers implement __getitem__ to retrieve values by
    address, key, or index using bracket notation.

    Example:
        >>> if isinstance(container, Subscriptable):
        ...     value = container["key"]
        ...     # or: value = container[0]
    """

    def __getitem__(self, address: A) -> V | Empty:
        """Get item by address.

        Args:
            address: Item address (key, index, or other identifier)

        Returns:
            Value at the given address

        Raises:
            KeyError: If address doesn't exist
            IndexError: If index out of range
        """
        ...


@runtime_checkable
class Assignable[A, V](View, Protocol):
    """Protocol for containers that support item assignment via subscript notation.

    Assignable containers implement __setitem__ to store values by
    address, key, or index using bracket notation.

    Example:
        >>> if isinstance(container, Assignable):
        ...     container["key"] = value
        ...     # or: container[0] = value
    """

    def __setitem__(self, address: A, value: V) -> None:
        """Set item at address.

        Args:
            address: Item address (key, index, or other identifier)
            value: Value to store

        Raises:
            TypeError: If value type not supported
            IndexError: If index out of range
        """
        ...


@runtime_checkable
class Containable[V](View, Protocol):
    """Protocol for containers that support membership testing.

    Containable containers implement __contains__ to check if an address
    exists using the 'in' operator.

    Type Parameters:
        A: The type of address to check for membership

    Example:
        >>> if isinstance(container, Containable):
        ...     if "key" in container:
        ...         print("Key exists")
    """

    def __contains__(self, obj: V) -> bool:
        """Check if address exists in container.

        Args:
            obj: Object to check for existence (existence dimension is based on the view semantics - value, address, etc)

        Returns:
            True if address exists in container
        """
        ...


@runtime_checkable
class Sizeable(View, Protocol):
    """Protocol for containers that support size queries.

    Sizeable containers implement __len__ to return the number of items
    using the len() function.

    Example:
        >>> if isinstance(container, Sizeable):
        ...     size = len(container)
    """

    def __len__(self) -> int:
        """Get number of items in container.

        Returns:
            Number of items
        """
        ...


@runtime_checkable
class Deletable[A](View, Protocol):
    """Protocol for containers that support item deletion.

    Deletable containers implement __delitem__ to remove items by
    address using the del statement.

    Type Parameters:
        A: The type of address to delete

    Example:
        >>> if isinstance(container, Deletable):
        ...     del container["key"]
        ...     # or: del container[0]
    """

    def __delitem__(self, address: A) -> None:
        """Delete item at address.

        Args:
            address: Item address to delete

        Raises:
            KeyError: If address doesn't exist
            IndexError: If index out of range
        """
        ...


@runtime_checkable
class Clearable(View, Protocol):
    """Protocol for containers that support clearing all items.

    Clearable containers implement clear() to remove all items at once.

    Example:
        >>> if isinstance(container, Clearable):
        ...     container.clear()
    """

    def clear(self) -> None:
        """Remove all items from container."""
        ...


@runtime_checkable
class Appendable[V](View, Protocol):
    """Protocol for containers that support appending items.

    Appendable containers implement append() to add items to the end
    of a sequence or collection.

    Type Parameters:
        V: The type of value to append

    Example:
        >>> if isinstance(container, Appendable):
        ...     container.append(value)
    """

    def append(self, value: V) -> None:
        """Append value to container.

        Args:
            value: Value to append
        """
        ...


@runtime_checkable
class Watchable(View, Protocol):
    """Protocol for containers that support watching for changes.

    Watchable containers implement watch() to subscribe to changes on the
    container and its descendants, and unwatch() to cancel subscriptions.

    Example:
        >>> if isinstance(container, Watchable):
        ...     sub = container.watch(storage, my_callback)
        ...     # ... later
        ...     container.unwatch(storage, sub)
    """

    def watch(
        self,
        storage: StorageProtocol,
        callback: CallbackFn,
        depth: int = -1,
    ) -> Subscription:
        """Watch changes to this container and its descendants.

        Args:
            storage: Storage instance for subscriptions
            callback: Function called on changes
            depth: Subscription depth (-1=entire tree, 0=exact, N=depth)

        Returns:
            Subscription handle

        Raises:
            StorageOperationError: If subscription fails
        """
        ...

    def unwatch(
        self,
        storage: StorageProtocol,
        subscription: Subscription,
    ) -> None:
        """Unsubscribe from changes.

        Args:
            storage: Storage instance
            subscription: Subscription to cancel

        Raises:
            StorageOperationError: If unsubscribe fails
        """
        ...


@runtime_checkable
class ChildWatchable[A](View, Protocol):
    """Protocol for containers that support watching individual children.

    ChildWatchable containers implement watch_child() to subscribe to changes
    on a specific child and watch_children() to subscribe to multiple children.

    Type Parameters:
        A: The type of address/key for children

    Example:
        >>> if isinstance(container, ChildWatchable):
        ...     sub = container.watch_child(storage, "alice", my_callback)
        ...     subs = container.watch_children(
        ...         storage, "alice", "bob", callback=my_callback
        ...     )
        ...     # ... later
        ...     container.unwatch(storage, sub)
    """

    def watch_child(
        self,
        storage: StorageProtocol,
        address: A,
        callback: CallbackFn,
        depth: int = -1,
    ) -> Subscription:
        """Watch changes to a specific child and its subtree.

        Args:
            storage: Storage instance for subscriptions
            address: Child address to watch
            callback: Function called on changes
            depth: Subscription depth (-1=entire subtree, 0=exact, N=depth)

        Returns:
            Subscription handle

        Raises:
            StorageOperationError: If subscription fails
        """
        ...

    def watch_children(
        self,
        storage: StorageProtocol,
        *addresses: A,
        callback: CallbackFn,
        depth: int = -1,
    ) -> tuple[Subscription, ...]:
        """Watch changes to multiple children and their subtrees.

        Args:
            storage: Storage instance for subscriptions
            *addresses: Child addresses to watch
            callback: Function called on changes
            depth: Subscription depth (-1=entire subtree, 0=exact, N=depth)

        Returns:
            Tuple of subscription handles

        Raises:
            StorageOperationError: If subscription fails
        """
        ...

    def unwatch(
        self,
        storage: StorageProtocol,
        subscription: Subscription,
    ) -> None:
        """Unsubscribe from changes.

        Args:
            storage: Storage instance
            subscription: Subscription to cancel

        Raises:
            StorageOperationError: If unsubscribe fails
        """
        ...


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def is_convertible(obj: object) -> TypeGuard[Convertible]:
    """Check if object supports extract operation.

    Args:
        obj: Object to check

    Returns:
        True if object implements Convertible protocol
    """
    return isinstance(obj, Convertible)


def is_initializable(obj: object) -> TypeGuard[Initializable]:
    """Check if object supports store operation.

    Args:
        obj: Object to check

    Returns:
        True if object implements Initializable protocol
    """
    return isinstance(obj, Initializable)


def is_nestable(obj: object) -> TypeGuard[Nestable]:
    """Check if object supports child navigation.

    Args:
        obj: Object to check

    Returns:
        True if object implements Nestable protocol
    """
    return isinstance(obj, Nestable)


def is_subscriptable(obj: object) -> TypeGuard[Subscriptable]:
    """Check if object supports item access via subscript.

    Args:
        obj: Object to check

    Returns:
        True if object implements Subscriptable protocol
    """
    return isinstance(obj, Subscriptable)


def is_assignable(obj: object) -> TypeGuard[Assignable]:
    """Check if object supports item assignment via subscript.

    Args:
        obj: Object to check

    Returns:
        True if object implements Assignable protocol
    """
    return isinstance(obj, Assignable)


def is_containable(obj: object) -> TypeGuard[Containable]:
    """Check if object supports membership testing.

    Args:
        obj: Object to check

    Returns:
        True if object implements Containable protocol
    """
    return isinstance(obj, Containable)


def is_sizeable(obj: object) -> TypeGuard[Sizeable]:
    """Check if object supports size queries.

    Args:
        obj: Object to check

    Returns:
        True if object implements Sizeable protocol
    """
    return isinstance(obj, Sizeable)


def is_deletable(obj: object) -> TypeGuard[Deletable]:
    """Check if object supports item deletion.

    Args:
        obj: Object to check

    Returns:
        True if object implements Deletable protocol
    """
    return isinstance(obj, Deletable)


def is_clearable(obj: object) -> TypeGuard[Clearable]:
    """Check if object supports clearing all items.

    Args:
        obj: Object to check

    Returns:
        True if object implements Clearable protocol
    """
    return isinstance(obj, Clearable)


def is_appendable(obj: object) -> TypeGuard[Appendable]:
    """Check if object supports appending items.

    Args:
        obj: Object to check

    Returns:
        True if object implements Appendable protocol
    """
    return isinstance(obj, Appendable)


def is_watchable(obj: object) -> TypeGuard[Watchable]:
    """Check if object supports watching for changes.

    Args:
        obj: Object to check

    Returns:
        True if object implements Watchable protocol
    """
    return isinstance(obj, Watchable)


def is_child_watchable(obj: object) -> TypeGuard[ChildWatchable]:
    """Check if object supports watching individual children.

    Args:
        obj: Object to check

    Returns:
        True if object implements ChildWatchable protocol
    """
    return isinstance(obj, ChildWatchable)
