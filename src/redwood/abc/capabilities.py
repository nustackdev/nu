"""Container capability protocols.

These protocols define optional capabilities for container-like objects.
Not all containers support all operations - check protocol support before use.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, TypeGuard, runtime_checkable


if TYPE_CHECKING:
    from redwood.abc import Value


__all__ = [
    "Convertible",
    "Initializable",
    "Nestable",
]

# =============================================================================
# CORE CAPABILITY PROTOCOLS
# =============================================================================


@runtime_checkable
class Convertible(Protocol):
    """Protocol for containers that can convert their contents to Python values.

    Convertible containers can materialize their entire stored state into
    native Python data structures (dict, list, set, etc.).

    Example:
        >>> if isinstance(container, Convertible):
        ...     data = container.extract()
        ...     # data is now a native Python dict/list/etc
    """

    def extract(self, *args: object, **kwargs: object) -> Value:
        """Extract container contents as native Python value.

        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Native Python value representing container contents
        """
        ...


@runtime_checkable
class Initializable(Protocol):
    """Protocol for containers that can be initialized from Python values.

    Initializable containers can populate their contents from native Python
    data structures, handling the conversion and storage automatically.

    Example:
        >>> if isinstance(container, Initializable):
        ...     container.store({"key": "value"}, replace=True)
    """

    def store(
        self, value: object, /, *args: object, replace: bool = False, **kwargs: object
    ) -> None:
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
class Nestable(Protocol):
    """Protocol for containers that support navigation to child containers.

    Nestable containers can navigate their hierarchy, returning appropriate
    container instances for child nodes.

    Example:
        >>> if isinstance(container, Nestable):
        ...     child = container.open_view(key)
        ...     # child is another container at the nested path
    """

    def open_view[ViewT](
        self, key: object, child_view: type[ViewT], *args: object, **kwargs: object
    ) -> ViewT:
        """Navigate to child container.

        Args:
            key: Child container key
            child_view: View to open child container with
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Container instance for child

        Raises:
            KeyError: If child doesn't exist
            TypeError: If child is not a container
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


__all__ = [
    # Protocols
    "Convertible",
    "Initializable",
    "Nestable",
    # Helpers
    "is_convertible",
    "is_initializable",
    "is_nestable",
]
