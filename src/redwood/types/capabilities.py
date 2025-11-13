"""Container capability protocols.

These protocols define optional capabilities for container-like objects.
Not all containers support all operations - check protocol support before use.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, TypeGuard, runtime_checkable


if TYPE_CHECKING:
    from redwood.view import View

    from .special import Empty


__all__ = [
    "Assignable",
    "Convertible",
    "Initializable",
    "Nestable",
    "Subscriptable",
    "is_assignable",
    "is_convertible",
    "is_initializable",
    "is_nestable",
    "is_subscriptable",
]


# =============================================================================
# CORE CAPABILITY PROTOCOLS
# =============================================================================


@runtime_checkable
class Convertible[V](Protocol):
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
class Initializable[V](Protocol):
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
class Nestable[A](Protocol):
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
class Subscriptable[A, V](Protocol):
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
class Assignable[A, V](Protocol):
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
