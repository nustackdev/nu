"""Base View implementation for Layer 3.

Views are thin wrappers over Container providing protocol-based capabilities.
"""

from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING, ClassVar, Self, cast

import attrs

from redwood.loc import key as key_
from redwood.loc import path as path_
from redwood.tree import Container, ContainerProtocol, ContainerStructure

from .registry import ViewRegistry


if TYPE_CHECKING:
    from redwood.storage import (
        StorageContextType,
    )

__all__ = [
    "View",
]


@attrs.frozen
class View(ABC):
    """Base class for all views.

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
        ...             key: self._get_child_value(key)
        ...             for key in self.container.list_child_keys()
        ...         }
        ...
        ...     def store(self, value: dict[K, V], /, *, replace: bool = False) -> None:
        ...         if replace:
        ...             self.container.clear_children()
        ...         for k, v in value.items():
        ...             self._set_child_value(k, v)
    """

    container: Container
    registry: ViewRegistry

    # =========================================================================
    # STRUCTURE & PROTOCOL
    # =========================================================================

    STRUCTURE: ClassVar[ContainerStructure]
    PROTOCOL: ClassVar[ContainerProtocol] = ContainerProtocol.NONE
    CONTAINER_CLS: ClassVar[type | None] = None

    @classmethod
    def get_default_parent_view(cls) -> type[View] | None:
        """Returns view used to create missing parents."""
        return None

    @classmethod
    def get_available_views(cls) -> tuple[type[View], ...]:
        """Returns tuple of avaible views to use for reading and writing data to tree."""
        return ()

    @classmethod
    def get_structure(cls) -> ContainerStructure:
        """Get view structure."""
        if cls.STRUCTURE is None:
            raise
        return cls.STRUCTURE

    @classmethod
    def get_protocol(cls) -> ContainerProtocol:
        """Get view protocol hints."""
        return cls.PROTOCOL

    @classmethod
    def get_container_cls(cls) -> type | None:
        """Get container type, associated with this view."""
        return cls.CONTAINER_CLS

    # =========================================================================
    # Initialization
    # =========================================================================

    @classmethod
    def open_root(
        cls,
        ctx: StorageContextType,
        *,
        views: tuple[type[View], ...] = (),
        default_parent_view: type[View] | None = None,
    ) -> Self:
        """Create a new View instance of this type on a root path."""
        if default_parent_view is None:
            default_parent_view = cls.get_default_parent_view()

        if default_parent_view is None:
            raise ValueError(
                "default_parent_view is None, either provide default_parent_view or override get_default_parent_view method."
            )

        container = Container.create(
            (key_.DATA_ROOT,),
            ctx,
            cls.get_structure(),
            cls.get_protocol(),
            default_parent_structure=default_parent_view.get_structure(),
            default_parent_protocol=default_parent_view.get_protocol(),
            ensure_healthy_parents=True,
        )

        registry = ViewRegistry()
        for view in cls.get_available_views() + views:
            registry.register(view)

        return cls(container, registry)

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
            ctx: Storage context (transaction or snapshot)
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
        # root view
        root_view_cls = default_parent_view or cls.get_default_parent_view()
        if not root_view_cls:
            raise ValueError(
                "default_parent_view is None, either provide default_parent_view or override get_default_parent_view method."
            )

        # Create root view of the first segment's type
        root_view = root_view_cls.open_root(
            ctx,
            views=views,
            default_parent_view=default_parent_view,
        )

        # Navigate through remaining segments
        full_path = (*parent_path, (address, cls))
        return cast("Self", path_.navigate_view(root_view, full_path))

    @classmethod
    def open_at_key(
        cls,
        key: key_.Key,
        ctx: StorageContextType,
        *,
        views: tuple[type[View], ...] = (),
        default_parent_view: type[View] | None = None,
    ) -> Self:
        """Create a View at the specified container key.

        Creates all necessary intermediate containers along the key path and
        returns the View instance at the final container location.

        Args:
            ctx: Storage context (transaction or snapshot)
            key: Container key tuple (raw storage path)
            views: Tuple of available views
            default_parent_view: View type for intermediate parent containers

        Returns:
            View instance at the final container location

        Raises:
            ValueError: If key is empty or only root
            TypeError: If default_parent_view cannot provide structure/protocol

        Example:
            >>> key = ("/", "users", "alice")
            >>> alice_view = DictView.create_at_key(tx, key, DictView)
        """
        if not key:
            raise ValueError("Key is empty, provide a complete key")

        if key[0] != key_.DATA_ROOT:
            raise ValueError("Key must start with DATA_ROOT ('/')")

        if default_parent_view is None:
            default_parent_view = cls.get_default_parent_view()

        if default_parent_view is None:
            raise ValueError(
                "default_parent_view is None, either provide default_parent_view or override get_default_parent_view method."
            )

        # Create the target container with proper structure and protocol
        container = Container.create(
            key,
            ctx,
            cls.get_structure(),
            cls.get_protocol(),
            default_parent_structure=default_parent_view.get_structure(),
            default_parent_protocol=default_parent_view.get_protocol(),
            ensure_healthy_parents=True,
        )

        # Build registry from default_parent_view
        registry = ViewRegistry()
        for view in cls.get_available_views() + views:
            registry.register(view)

        return cls(container, registry)

    # =========================================================================
    # NAVIGATION HELPERS
    # =========================================================================

    def open_parent(self) -> View:
        """Navigate to parent container.

        Returns:
            View instance for parent container

        Raises:
            ValueError: If already at root (no parent)
        """
        parent_path = key_.get_parent(self.container.path)
        if parent_path is None:
            raise ValueError("Cannot navigate to parent - already at root")

        # Create parent container
        parent_container = Container(ctx=self.container.ctx, path=parent_path)

        # Get parent's structure ID to find correct view type
        parent_info = parent_container.info()
        if parent_info.structure is None:
            raise ValueError(f"Parent container at {parent_path} has no structure ID")

        # Use registry to create appropriate view
        view_class = self.registry.get_view_for_structure(parent_info.structure)
        return view_class(container=parent_container, registry=self.registry)
