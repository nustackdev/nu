"""
Base view implementation for the state management system.

This module defines the BaseView class, which provides common functionality
for all view implementations. Views provide protocol-specific interfaces
for interacting with container nodes.

IMPORTANT: This implementation uses immutable views with smart transaction handling
to provide thread-safe operations and consistent data access patterns.

**Immutability & Thread Safety**
DictView instances are frozen (attrs.frozen=True) and cannot be modified after creation.
All operations return new data or modify the underlying storage through transactions,
never changing the view object itself. This eliminates race conditions in concurrent
environments since multiple threads can safely share the same view instance.

**Automatic Transaction Management**
Every operation uses with_transaction() to ensure proper transaction handling.
If the view has no transaction, the context manager creates one automatically and
commits/rollbacks based on success or failure. If a transaction already exists,
it reuses that transaction without additional management. This provides both
convenience for simple operations and flexibility for complex multi-operation scenarios.

**Cache and Performance**
The container property is cached using @cached_property to avoid repeated lookups.
cached_property is thread-safe and ensures the container node creation can not be
intervened by other threads.
"""

from __future__ import annotations

from abc import ABC
from functools import cached_property
from typing import TYPE_CHECKING, Any, Generic, Optional

import attrs

from ..context import ContextualBase
from ..context.protocols import ContextType
from ..exceptions import ContainerProtocolError
from ..node import ChildType, ContainerNode
from ..path import Path
from ..types import EMPTY, ContainerProtocol, ContainerStructure, Empty, PathComponent, TreeT, Value
from .types import AccessibleViewProtocol

if TYPE_CHECKING:
    pass

__all__ = [
    "BaseView",
]


class ViewError(Exception):
    """Base exception for view-related errors."""

    pass


@attrs.define(frozen=True, kw_only=True)
class BaseView(Generic[TreeT], ContextualBase, ABC):
    """
    Base class for all container views.

    Views provide protocol-specific interfaces for interacting with
    container nodes. Each view type implements specific operations
    appropriate for a particular container protocol.

    The BaseView provides common functionality used by all view types,
    including path access, container creation, and navigation utilities.
    It is now a pure frozen dataclass with no context manager logic.

    Transaction handling is provided by State class factory methods:
    - Context manager methods: with_dict_view(), with_list_view(), etc.
    - Direct access methods: dict_view(), list_view(), etc.

    Example:
        ```python
        # Context manager usage (automatic transaction)
        with state.at("users").with_dict_view() as users:
            users.set("alice", {"name": "Alice"})
            users.set("bob", {"name": "Bob"})

        # Direct usage (manual transaction management)
        users = state.at("users").dict_view()
        user_data = users.get("alice")

        # Manual transaction with direct usage
        tx = state.begin_transaction()
        try:
            users = state.at("users").dict_view(tx=tx)
            users.set("alice", {"name": "Alice"})
            tx.commit()
        except Exception:
            tx.rollback()
            raise
        ```
    """

    # Path to the container
    path: Path = attrs.field()

    # Container structure type
    structure: ContainerStructure = attrs.field(init=False)

    # Container protocol type
    protocol: ContainerProtocol = attrs.field(init=False)

    # Tree class this view operates on
    tree: TreeT = attrs.field()

    # =========================================================================
    # CONTAINER NODE ACCESS
    # =========================================================================

    @cached_property
    def container(self) -> ContainerNode:
        """
        Get the container node for this view.

        Creates a ContainerNode with the appropriate configuration
        and ensures it exists.

        Returns:
            ContainerNode: The container node
        """

        if self.ctx is None:
            raise ValueError("Cannot access container without a context")
            # TODO: Improve error message to indicate that a context is required for views

        container = ContainerNode.create(
            backend=self.backend,
            path=self.path,
            structure=self.structure,
            protocol=self.protocol,
            ctx=self.ctx,
            ensure_exists=True,
        )

        return container

    # =========================================================================
    # TREE NAVIGATION METHODS (return new Tree instances)
    # =========================================================================

    def at(self, *paths: PathComponent, ctx: Optional[ContextType] = None) -> TreeT:
        """
        Navigate to a path (relative to current path).

        This creates a new State instance pointing to the specified path.

        Args:
            *paths: Path components to navigate to
            ctx: Optional context (defaults to current context)

        Returns:
            State: New State for the specified path

        Example:
            ```python
            # Basic navigation
            user = tree.at("users", "alice")
            email = tree.at("users", "alice", "email")

            # Navigation with context manager
            with tree.at("users").with_dict_view() as users:
                # Operations with transaction
                users.set("alice", {"name": "Alice"})

            # Navigation with direct access
            users = tree.at("users").dict_view()
            alice_data = users.get("alice")
            ```
        """
        new_path = self.path.join(*paths)
        return self.tree.at(*new_path, ctx=ctx or self.ctx)

    def parent(self, *, ctx: Optional[ContextType] = None) -> TreeT:
        """
        Navigate to parent path.

        Returns:
            State: State for the parent path, or self if already at root

        Example:
            ```python
            user = tree.at("users", "alice")
            users = user.parent()
            ```
        """
        parent_path = self.path.parent()
        if parent_path is None:
            # Already at root
            parent_path = self.path
        return self.tree.parent(ctx=ctx or self.ctx)

    def root(self, *, ctx: Optional[ContextType] = None) -> TreeT:
        """
        Navigate to root path.

        Returns:
            State: State for the root path

        Example:
            ```python
            root = tree.at("deeply", "nested", "path").root()
            ```
        """
        return self.tree.root(ctx=ctx or self.ctx)

    # =========================================================================
    # COMMON CHILD MANAGEMENT OPERATIONS (using registry)
    # =========================================================================

    def _get_child_value(
        self, key: PathComponent, /, *, default: Value | Empty = EMPTY
    ) -> Value | Empty:
        """
        Common logic for getting child values using registry for view resolution.

        Args:
            key: Child key to retrieve
            default: Default value if child doesn't exist

        Returns:
            Value or default - primitives returned directly, containers extracted

        Raises:
            ViewError: If registry lookups fail
        """
        child_info = self.container.get_child_info(key)

        if child_info.child_type == ChildType.NOT_FOUND:
            return default

        if child_info.child_type == ChildType.PRIMITIVE:
            return child_info.value

        if child_info.child_type == ChildType.CONTAINER:
            # Use structure ID from child info
            structure_id = child_info.stored_structure

            if structure_id is None:
                raise ContainerProtocolError(f"Container '{key}' has no structure ID")

            # Use registry to get appropriate view
            try:
                view = self._get_view_for_structure_id(key, structure_id)

                # Ensure the view implements the AccessibleViewProtocol
                if not isinstance(view, AccessibleViewProtocol):
                    raise ViewError(
                        f"View {type(view).__name__} doesn't implement AccessibleViewProtocol. Required methods for nested value extraction are missing."
                    )

                return view.extract()
            except ValueError as e:
                raise ViewError(f"Cannot create view for structure ID {structure_id}") from e

        raise ValueError(f"Unexpected child type '{child_info.child_type}' for key '{key}'")

    def _set_child_value(self, key: PathComponent, value: Value, /) -> None:
        """
        Common logic for setting child values using registry for view resolution.

        Args:
            key: Child key to set
            value: Value to store

        Raises:
            ViewError: If registry lookups fail or conflicts detected
        """
        if self._is_value_primitive(value):
            # Store primitive value directly
            self.container.set_primitive_child(key, value)
        else:
            # Value is a container - need to find appropriate view

            # Check if primitive with same key exists (conflict)
            if self.container.has_primitive_child(key):
                raise ValueError(
                    f"Cannot overwrite primitive value with container at key '{key}'. "
                    "Use a different key for the container."
                )

            # Use registry to find view for this value type
            try:
                child_view = self._get_view_for_container_value(key, value)

                # Ensure the view implements the AccessibleViewProtocol
                if not isinstance(child_view, AccessibleViewProtocol):
                    raise ViewError(
                        f"View for value type {type(value).__name__} doesn't implement AccessibleViewProtocol. Required methods for nested value storage are missing."
                    )

                child_view.store(value, replace=False)
            except ValueError as e:
                raise ViewError(f"Cannot create view for value type {type(value)}") from e

    # =========================================================================
    # REGISTRY-BASED VIEW CREATION
    # =========================================================================

    def _get_view_for_structure_id(self, key: PathComponent, structure_id: int, /) -> BaseView:
        """
        Get view for existing container using registry and structure ID.

        Args:
            key: Child key
            structure_id: Container structure ID from storage

        Returns:
            BaseView: Appropriate view for the structure ID

        Raises:
            ValueError: If structure ID not registered
        """
        view_class = self.tree.registry.get_view_for_structure(structure_id)
        return self._create_view(key, view_class)

    def _get_view_for_container_value(self, key: PathComponent, value: Value, /) -> BaseView:
        """
        Get view for container value using registry.

        Args:
            key: Child key
            value: Container value to store

        Returns:
            BaseView: Appropriate view for the value

        Raises:
            ValueError: If no container type matches the value
        """
        # Find matching container type using isinstance checks
        registry = self.tree.registry

        for container_type in registry.get_registered_container_types():
            if isinstance(value, container_type):
                view_class = registry.get_view_for_container_type(container_type)
                return self._create_view(key, view_class)

        # No direct match found - this is an error since we removed fallback logic
        raise ValueError(
            f"No container type registered for value type {type(value).__name__}. "
            f"Register a container type that matches isinstance({type(value).__name__}, container_type)."
        )

    def _get_view_for_component_type(self, key: PathComponent, component: Any, /) -> BaseView:
        """
        Get view that can handle a specific component type during navigation.

        Args:
            key: Child key
            component: Component/key object for navigation

        Returns:
            BaseView: View that can handle this component type

        Raises:
            ValueError: If no component type matches the component
        """
        # Find matching component type using isinstance checks
        registry = self.tree.registry

        for component_type in registry.get_registered_component_types():
            if isinstance(component, component_type):
                # Get primary view for this component type
                view_class = registry.get_primary_view_for_component_type(component_type)
                return self._create_view(key, view_class)

        raise ValueError(
            f"No component type registered for component type {type(component).__name__}. "
            f"Register a component type that matches isinstance({type(component).__name__}, component_type)."
        )

    def _create_view(self, key: PathComponent, view_class: type[BaseView]) -> BaseView:
        """
        Generic view creation method.

        Args:
            key: Child key
            view_class: View class to instantiate

        Returns:
            BaseView: New view instance
        """
        return view_class(
            backend=self.backend, path=self.path.join(key), ctx=self.ctx, tree=self.tree
        )

    def _is_value_primitive(self, value: Value, /) -> bool:
        """
        Check if value should be stored as primitive.

        A value is primitive if it doesn't match any registered container type.

        Args:
            value: Value to check

        Returns:
            bool: True if value is primitive (no matching container type)
        """
        registry = self.tree.registry

        # Check if value matches any registered container type
        for container_type in registry.get_registered_container_types():
            if isinstance(value, container_type):
                return False  # Matches a container type, not primitive

        return True  # No container type matches, treat as primitive
