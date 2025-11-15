"""Base View implementation for Layer 3.

Views are thin wrappers over Container providing protocol-based capabilities.
"""

from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING, ClassVar, Self, cast

import attrs

from redwood.loc import key as key_
from redwood.tree import Container, ContainerProtocol, ContainerStructure, NodeType
from redwood.types import Convertible, Empty, Initializable, is_empty

from .registry import ViewRegistry


if TYPE_CHECKING:
    from redwood.storage import CallbackFn, StorageContextType, StorageProtocol, SubscriptionProtocol
    from redwood.types import Value

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
    def create(
        cls,
        ctx: StorageContextType,
        views: tuple[type[View], ...],
        default_parent_view: type[View],
    ) -> Self:
        """Create a new View instance of this type on a root path."""
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
        for view in views:
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

    # =========================================================================
    # HELPER METHODS FOR SUBCLASSES
    # =========================================================================

    def _get_child_value(self, key: key_.KeySegment) -> object | Empty:
        """Get child value, auto-extracting containers.

        Helper for subclasses implementing dict-like or list-like access.
        Automatically extracts nested containers using registry.

        Args:
            key: Child key

        Returns:
            Primitive value or extracted container contents

        Raises:
            KeyError: If child doesn't exist
        """
        child_type = self.container.get_child_type(key)

        if child_type == NodeType.NOT_FOUND:
            raise KeyError(key)

        if child_type == NodeType.PRIMITIVE:
            value = self.container.get_child_primitive(key)
            if is_empty(value):
                raise KeyError(key)
            return value

        # Child is container - extract it
        return self._extract_child_container(key)

    def _set_child_value(self, key: key_.KeySegment, value: object) -> None:
        """Set child value, auto-creating containers for complex types.

        Helper for subclasses implementing dict-like or list-like mutation.
        Automatically populates nested containers using registry.

        Args:
            key: Child key
            value: Value to store (primitive or container)
        """
        if self.registry.is_container_type(value):
            # Value is a container type - populate it
            self._populate_child_container(key, value)
        else:
            # Primitive value - store directly
            self.container.set_child_primitive(key, cast("Value", value))

    def _extract_child_container(self, key: key_.KeySegment) -> object:
        """Extract child container contents using registry.

        Args:
            key: Child key

        Returns:
            Extracted Python value
        """
        # Get child container
        child_path = (*self.container.path, key)
        child_container = Container(ctx=self.container.ctx, path=child_path)

        # Get structure ID
        child_info = child_container.info()
        if child_info.structure is None:
            raise ValueError(f"Child container '{key}' has no structure ID")

        # Find appropriate view
        view_class = self.registry.get_view_for_structure(child_info.structure)
        child_view = view_class(container=child_container, registry=self.registry)

        # Extract if supported
        if not isinstance(child_view, Convertible):
            raise TypeError(f"Child view {view_class.__name__} does not support extraction")

        return child_view.extract()

    def _populate_child_container(self, key: key_.KeySegment, value: object) -> None:
        """Populate child container from Python value using registry.

        Args:
            key: Child key
            value: Container value to store
        """
        # Get view class and structure for this value type
        value_type = type(value)
        view_class = self.registry.get_view_for_type(value_type)
        structure_id = view_class.get_structure()
        protocol_hints = view_class.get_protocol()

        # Create child container
        child_container = self.container.create_child_container(
            key=key,
            structure=ContainerStructure(structure_id),
            protocol=protocol_hints,
        )

        # Create view and populate
        child_view = view_class(container=child_container, registry=self.registry)

        # Store if supported
        if not isinstance(child_view, Initializable):
            raise TypeError(f"Child view {view_class.__name__} does not support initialization")

        child_view.store(value)

    # =========================================================================
    # WATCH METHODS: SUBSCRIPTIONS
    # =========================================================================

    def watch_child(
        self,
        storage: StorageProtocol,
        key: key_.KeySegment,
        callback: CallbackFn,
        depth: int = -1,
    ) -> SubscriptionProtocol:
        """Watch changes to a specific child and its subtree.

        Args:
            storage: Storage instance for subscriptions
            key: Child key to watch
            callback: Function called on changes
            depth: Subscription depth (-1=entire subtree, 0=exact, N=depth)

        Returns:
            Subscription handle

        Raises:
            StorageOperationError: If subscription fails

        Example:
            >>> sub = view.watch_child(storage, "alice", my_callback)
            >>> # Callback fires on changes to child and its subtree
        """
        return self.container.watch_child(storage, key, callback, depth)

    def watch_children(
        self,
        storage: StorageProtocol,
        *keys: key_.KeySegment,
        callback: CallbackFn,
        depth: int = -1,
    ) -> tuple[SubscriptionProtocol, ...]:
        """Watch changes to multiple children and their subtrees.

        Args:
            storage: Storage instance for subscriptions
            *keys: Child keys to watch
            callback: Function called on changes
            depth: Subscription depth (-1=entire subtree, 0=exact, N=depth)

        Returns:
            Tuple of subscription handles

        Raises:
            StorageOperationError: If subscription fails

        Example:
            >>> subs = view.watch_children(storage, "alice", "bob", callback=my_callback)
            >>> # subs is (sub1, sub2)
        """
        return self.container.watch_children(storage, *keys, callback=callback, depth=depth)

    def watch_descendants(
        self,
        storage: StorageProtocol,
        callback: CallbackFn,
        depth: int = -1,
    ) -> SubscriptionProtocol:
        """Watch changes to all descendants of this view's container.

        Args:
            storage: Storage instance for subscriptions
            callback: Function called on changes
            depth: Subscription depth (-1=entire tree, 0=exact, N=depth)

        Returns:
            Subscription handle

        Raises:
            StorageOperationError: If subscription fails

        Example:
            >>> sub = view.watch_descendants(storage, my_callback)
            >>> # Callback fires on any change under this view
        """
        return self.container.watch_descendants(storage, callback, depth)

    def unwatch(
        self,
        storage: StorageProtocol,
        subscription: SubscriptionProtocol,
    ) -> None:
        """Unsubscribe from changes.

        Convenience wrapper for storage.unsubscribe().

        Args:
            storage: Storage instance
            subscription: Subscription to cancel

        Raises:
            StorageOperationError: If unsubscribe fails

        Example:
            >>> sub = view.watch_child(storage, "alice", callback)
            >>> view.unwatch(storage, sub)
        """
        self.container.unwatch(storage, subscription)
