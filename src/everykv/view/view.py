"""Base View implementation for Layer 3.

Views are thin wrappers over Container providing protocol-based capabilities.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, Self, runtime_checkable


if TYPE_CHECKING:
    from everykv.container import Container, ContainerProtocol, ContainerStructure
    from everykv.loc import path as path_
    from everykv.loc import site as site_
    from everykv.storage import (
        StorageContextType,
    )

    from .registry import ViewRegistry

__all__ = [
    "View",
]


@runtime_checkable
class View(Protocol):
    """View Protocol.

    Views are thin wrappers over Container that provide familiar Python
    interfaces. All storage operations are delegated to the Container API.

    Type Parameters:
        AddressT: Type of addresses this view accept
            - Types of objects indicating children node's location, e.g. set(address=address, ...)
            - For example, int in case of ListView, int | str in case of DictView, None in case of QueueView, ...
        ValueT: Type of values this view stores/returns

    Design:
    - Stateless: No cached data, always delegates to container
    - Immutable: View instances don't change (NamedTuple)
    - Registry-aware: Can create nested views automatically
    - Protocol-based: Subclasses implement Convertible/Initializable/Nestable as needed

    Attributes:
        container: Container instance for storage operations
        registry: Registry for nested view creation

    Example:
        >>> class DictView[K, V](View[K, V]):
        ...     def extract(self) -> dict[K, V]:
        ...         return {
        ...             address: self._get_child_value(address)
        ...             for address in self.container.iter_child_keys()
        ...         }
        ...
        ...     def store(self, value: dict[K, V], /, *, replace: bool = False) -> None:
        ...         if replace:
        ...             self.container.clear_children()
        ...         for address, v in value.items():
        ...             self._set_child_value(address, v)
    """

    @classmethod
    def get_default_parent_view(cls) -> type[View] | None:
        """Returns view used to create missing parents."""
        ...

    @classmethod
    def get_available_views(cls) -> tuple[type[View], ...]:
        """Returns tuple of avaible views to use for reading and writing data to tree."""
        ...

    @classmethod
    def get_structure(cls) -> ContainerStructure:
        """Get view structure."""
        ...

    @classmethod
    def get_protocol(cls) -> ContainerProtocol:
        """Get view protocol hints."""
        ...

    @classmethod
    def get_container_cls(cls) -> type | None:
        """Get container type, associated with this view."""
        ...

    @classmethod
    def open_root(
        cls,
        ctx: StorageContextType,
        *,
        views: tuple[type[View], ...] = (),
        default_parent_view: type[View] | None = None,
    ) -> Self:
        """Create a new View instance of this type on a root path."""
        ...

    @classmethod
    def open_at(
        cls,
        parent_path: path_.PathToView,
        address: path_.PathAddress,
        ctx: StorageContextType,
        *,
        views: tuple[type[View], ...] = (),
        default_parent_view: type[View] | None = None,
    ) -> Self:
        """Create a View at the specified path.

        Creates all necessary intermediate containers along the path and returns
        the View instance at the final path location.

        Args:
            parent_path: ViewPath to navigate - sequence of (address, ViewType) pairs
            address: Address in the parent path view
            ctx: Storage context (transaction, snapshot or write batch)
            views: Tuple of available views
            default_parent_view: View type to use for default parent containers

        Returns:
            View instance at the final path location

        Raises:
            TypeError: If parent view is not Nestable
            KeyError/IndexError: If address is invalid after normalization

        Example:
            >>> path = (("users", DictView), ("alice", DictView))
            >>> alice_view = DictView.create_at_path(tx, path, DictView)
        """
        ...

    @classmethod
    def open_at_site(
        cls,
        site: site_.Site,
        ctx: StorageContextType,
        *,
        views: tuple[type[View], ...] = (),
        default_parent_view: type[View] | None = None,
    ) -> Self:
        """Create a View at the specified container site.

        Creates all necessary intermediate containers along the site path and
        returns the View instance at the final container location.

        Args:
            ctx: Storage context (transaction, snapshot or write batch)
            site: Container site tuple (raw storage path)
            views: Tuple of available views
            default_parent_view: View type for intermediate parent containers

        Returns:
            View instance at the final container location

        Raises:
            ValueError: If site is empty or only root
            TypeError: If default_parent_view cannot provide structure/protocol

        Example:
            >>> site = ("/", "users", "alice")
            >>> alice_view = DictView.create_at_site(tx, site, DictView)
        """
        ...

    def open_parent(self) -> View:
        """Navigate to parent container.

        Returns:
            View instance for parent container

        Raises:
            ValueError: If already at root (no parent)
        """
        ...

    def __init__(self, container: Container, registry: ViewRegistry) -> None:
        """Initializes a new View with given container and protocol."""
        pass
