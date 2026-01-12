"""Container capability protocols.

These protocols define optional capabilities for container-like objects.
Not all containers support all operations - check protocol support before use.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, TypeGuard, runtime_checkable

from .view import View


if TYPE_CHECKING:
    from everyshape.loc import key
    from everyshape.storage import Subscription
    from everyshape.types import Empty


__all__ = [
    "Addable",
    "Appendable",
    "Assignable",
    "ChildObservable",
    "Clearable",
    "Containable",
    "Convertible",
    "Deletable",
    "DescendantsObservable",
    "Discardable",
    "Initializable",
    "Insertable",
    "Nestable",
    "Observable",
    "Poppable",
    "Removable",
    "Sizeable",
    "Subscriptable",
    "is_addable",
    "is_appendable",
    "is_assignable",
    "is_child_observable",
    "is_clearable",
    "is_containable",
    "is_convertible",
    "is_deletable",
    "is_descendants_observable",
    "is_discardable",
    "is_initializable",
    "is_insertable",
    "is_nestable",
    "is_observable",
    "is_poppable",
    "is_removable",
    "is_sizeable",
    "is_subscriptable",
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
    address using bracket notation.

    Example:
        >>> if isinstance(container, Subscriptable):
        ...     value = container["key"]
        ...     # or: value = container[0]
    """

    def __getitem__(self, address: A) -> V | Empty:
        """Get item by address.

        Args:
            address: Item address (index or other identifier)

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
    address using bracket notation.

    Example:
        >>> if isinstance(container, Assignable):
        ...     container["key"] = value
        ...     # or: container[0] = value
    """

    def __setitem__(self, address: A, value: V) -> None:
        """Set item at address.

        Args:
            address: Item address (index or other identifier)
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
class Insertable[V](View, Protocol):
    """Protocol for containers that support inserting items at a specific index.

    Insertable containers implement insert() to add items at a given position.

    Type Parameters:
        V: The type of value to insert

    Example:
        >>> if isinstance(container, Insertable):
        ...     container.insert(0, value)
    """

    def insert(self, index: int, value: V) -> None:
        """Insert value at index.

        Args:
            index: Position to insert at
            value: Value to insert
        """
        ...


@runtime_checkable
class Poppable[V](View, Protocol):
    """Protocol for containers that support popping items.

    Poppable containers implement pop() to remove and return items.

    Type Parameters:
        V: The type of value to pop

    Example:
        >>> if isinstance(container, Poppable):
        ...     value = container.pop()
        ...     value = container.pop(0)  # Pop from specific index
    """

    def pop(self, index: int = -1) -> V | Empty:
        """Remove and return item at index.

        Args:
            index: Position to remove from (default: last item)

        Returns:
            Removed value

        Raises:
            IndexError: If index out of range
        """
        ...


@runtime_checkable
class Addable[V](View, Protocol):
    """Protocol for containers that support adding items (sets).

    Addable containers implement add() to add items to a set.

    Type Parameters:
        V: The type of value to add

    Example:
        >>> if isinstance(container, Addable):
        ...     container.add(value)
    """

    def add(self, value: V) -> None:
        """Add value to container.

        Args:
            value: Value to add
        """
        ...


@runtime_checkable
class Removable[V](View, Protocol):
    """Protocol for containers that support removing items by value.

    Removable containers implement remove() to remove items by value.
    Raises KeyError if the value is not present.

    Type Parameters:
        V: The type of value to remove

    Example:
        >>> if isinstance(container, Removable):
        ...     container.remove(value)
    """

    def remove(self, value: V) -> None:
        """Remove value from container.

        Args:
            value: Value to remove

        Raises:
            KeyError: If value not in container
        """
        ...


@runtime_checkable
class Discardable[V](View, Protocol):
    """Protocol for containers that support discarding items by value.

    Discardable containers implement discard() to remove items by value.
    Unlike Removable, does not raise an error if value is not present.

    Type Parameters:
        V: The type of value to discard

    Example:
        >>> if isinstance(container, Discardable):
        ...     container.discard(value)  # No error if missing
    """

    def discard(self, value: V) -> None:
        """Discard value from container (no error if absent).

        Args:
            value: Value to discard
        """
        ...


@runtime_checkable
class Observable(View, Protocol):
    """Protocol for containers that support observing changes.

    Observable containers implement on_change() to subscribe to all
    changes within this view.

    Example:
        >>> if isinstance(container, Observable):
        ...     sub = container.on_change()
        ...     sub.bind(my_callback)
        ...     # ... later
        ...     sub.close()
    """

    def on_change(self) -> Subscription:
        """Subscribe to all changes in this view.

        Returns:
            Subscription handle that can be bound to callbacks

        Example:
            >>> sub = view.on_change()
            >>> sub.bind(callback)
            >>> sub.close()
        """
        ...


@runtime_checkable
class ChildObservable[A](View, Protocol):
    """Protocol for containers that support observing child changes.

    ChildObservable containers implement on_child_change() to subscribe
    to changes on a specific child, and on_children_change() to subscribe
    to all children changes.

    Type Parameters:
        A: The type of address for children

    Example:
        >>> if isinstance(container, ChildObservable):
        ...     sub = container.on_child_change("alice")
        ...     sub.bind(my_callback)
        ...     # ... later
        ...     sub.close()
    """

    def on_child_change(self, address: A) -> Subscription:
        """Watch changes to a specific child and its subtree.

        Args:
            address: Child address to watch

        Returns:
            Subscription handle that can be bound to callbacks

        Example:
            >>> sub = view.on_child_change("users")
            >>> sub.bind(callback)
            >>> sub.close()
        """
        ...

    def on_children_change(self) -> Subscription:
        """Watch changes of all children.

        Returns:
            Subscription handle that can be bound to callbacks

        Example:
            >>> sub = view.on_children_change()
            >>> sub.bind(callback)
            >>> sub.close()
        """
        ...


@runtime_checkable
class DescendantsObservable(View, Protocol):
    """Protocol for containers that support observing descendant changes.

    DescendantsObservable containers implement on_descendents_change() to
    subscribe to changes matching a pattern within descendants.

    Example:
        >>> if isinstance(container, DescendantsObservable):
        ...     sub = container.on_descendents_change("users", "*", "age")
        ...     sub.bind(my_callback)
        ...     # ... later
        ...     sub.close()
    """

    def on_descendents_change(
        self,
        address: key.KeySegment,
        *addresses: key.KeySegment,
    ) -> Subscription:
        """Watch changes of descendants for a given pattern.

        Args:
            address: First address segment in the pattern
            *addresses: Additional address segments (use "*" for wildcards)

        Returns:
            Subscription handle that can be bound to callbacks

        Example:
            >>> sub = view.on_descendents_change("users", "*", "age")
            >>> sub.bind(callback)
            >>> sub.close()
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


def is_insertable(obj: object) -> TypeGuard[Insertable]:
    """Check if object supports inserting items at index.

    Args:
        obj: Object to check

    Returns:
        True if object implements Insertable protocol
    """
    return isinstance(obj, Insertable)


def is_poppable(obj: object) -> TypeGuard[Poppable]:
    """Check if object supports popping items.

    Args:
        obj: Object to check

    Returns:
        True if object implements Poppable protocol
    """
    return isinstance(obj, Poppable)


def is_addable(obj: object) -> TypeGuard[Addable]:
    """Check if object supports adding items (sets).

    Args:
        obj: Object to check

    Returns:
        True if object implements Addable protocol
    """
    return isinstance(obj, Addable)


def is_removable(obj: object) -> TypeGuard[Removable]:
    """Check if object supports removing items by value.

    Args:
        obj: Object to check

    Returns:
        True if object implements Removable protocol
    """
    return isinstance(obj, Removable)


def is_discardable(obj: object) -> TypeGuard[Discardable]:
    """Check if object supports discarding items by value.

    Args:
        obj: Object to check

    Returns:
        True if object implements Discardable protocol
    """
    return isinstance(obj, Discardable)


def is_observable(obj: object) -> TypeGuard[Observable]:
    """Check if object supports observing changes.

    Args:
        obj: Object to check

    Returns:
        True if object implements Observable protocol
    """
    return isinstance(obj, Observable)


def is_child_observable(obj: object) -> TypeGuard[ChildObservable]:
    """Check if object supports observing child changes.

    Args:
        obj: Object to check

    Returns:
        True if object implements ChildObservable protocol
    """
    return isinstance(obj, ChildObservable)


def is_descendants_observable(obj: object) -> TypeGuard[DescendantsObservable]:
    """Check if object supports observing descendant changes.

    Args:
        obj: Object to check

    Returns:
        True if object implements DescendantsObservable protocol
    """
    return isinstance(obj, DescendantsObservable)
