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

from abc import ABC, abstractmethod
from functools import cached_property
from typing import TYPE_CHECKING

import attrs

from ..exceptions import ContainerProtocolError
from ..node import ChildType, ContainerNode
from ..path import Path
from ..transaction import TransactionalBase
from ..types import EMPTY, ContainerProtocol, ContainerStructure, Empty, PathComponent, Value

if TYPE_CHECKING:
    from .dict import DictView
    from .list import ListView

__all__ = [
    "BaseView",
]


@attrs.define(frozen=True, kw_only=True)
class BaseView(TransactionalBase, ABC):
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
    structure: ContainerStructure = attrs.field()

    # Container protocol type
    protocol: ContainerProtocol = attrs.field()

    @cached_property
    def container(self) -> ContainerNode:
        """
        Get the container node for this view.

        Creates a ContainerNode with the appropriate configuration
        and ensures it exists.

        Returns:
            ContainerNode: The container node
        """

        if self.tx is None:
            raise ValueError("Cannot access container without a transaction")
            # TODO: Improve error message to indicate that a transaction is required for views

        container = ContainerNode.create(
            backend=self.backend,
            path=self.path,
            structure=self.structure,
            protocol=self.protocol,
            tx=self.tx,
            ensure_exists=True,
        )

        return container

    # =========================================================================
    # COMMON CHILD MANAGEMENT OPERATIONS
    # =========================================================================

    def _get_child_value(
        self, key: PathComponent, /, *, default: Value | Empty = EMPTY
    ) -> Value | Empty:
        """
        Common logic for getting child values (primitive or extracted container).

        Args:
            key: Child key to retrieve
            default: Default value if child doesn't exist

        Returns:
            Value or default - primitives returned directly, containers extracted
        """
        # First check if child is a primitive, as this is the most common case
        child_info = self.container.get_child_info(key)

        if child_info.child_type == ChildType.NOT_FOUND:
            # Child does not exist, return default value
            return default

        # Check if child is a primitive value
        if child_info.child_type == ChildType.PRIMITIVE:
            # Child is a primitive, return its value directly
            return child_info.value

        # Child is not a primitive, check if it is a container
        if child_info.child_type == ChildType.CONTAINER:
            # Child is a container, extract its structure and protocol
            child_structure = child_info.stored_structure
            child_protocol = child_info.stored_protocol

            if child_structure is None or child_protocol is None:
                raise ContainerProtocolError(f"Container '{key}' has malformed structure/protocol")

            # Get the appropriate view for the existing container
            view = self._get_view_for_container(key, child_structure, child_protocol)
            # Extract the container value using the view
            return view.extract()

        raise ValueError(
            f"Unexpected child type '{child_info.child_type}' for key '{key}'. "
            "Expected primitive or container."
        )

    def _set_child_value(self, key: PathComponent, value: Value, /) -> None:
        """
        Common logic for setting child values (primitive or nested container).

        Args:
            key: Child key to set
            value: Value to store

        Raises:
            ValueError: If trying to overwrite container with primitive
        """
        if self._is_value_primitive(value):
            # Store the primitive value
            # If container has a container with the same key, it will raise an error
            self.container.set_primitive_child(key, value)
        else:
            # Value is a container (dict, list, etc.)

            # Check if a primitive with the same key does not exist
            if self.container.has_primitive_child(key):
                # If a primitive exists, we cannot overwrite it with a container
                raise ValueError(
                    f"Cannot overwrite primitive value with container at key '{key}'. "
                    "Use a different key for the container."
                )

            child_view = self._get_view_for_value(key, value)
            child_view.store(value, replace=False)

    # =========================================================================
    # NESTED VIEW CREATION
    # =========================================================================

    def _dict_view(self, key: PathComponent, /) -> "DictView":
        """Create nested dictionary view."""
        from .dict import DictView

        return DictView(backend=self.backend, path=self.path.join(key), tx=self.tx)

    def _list_view(self, key: PathComponent, /) -> "ListView":
        """Create nested list view."""
        from .list import ListView

        return ListView(backend=self.backend, path=self.path.join(key), tx=self.tx)

    # =========================================================================
    # UTILITY METHODS
    # =========================================================================

    def _get_view_for_container(
        self,
        key: PathComponent,
        structure: ContainerStructure,
        protocol: ContainerProtocol,
        /,
    ) -> BaseView:
        """
        Get appropriate view for existing container.

        Args:
            key: Child key to retrieve
            structure: Container structure type
            protocol: Container protocol type

        Returns:
            BaseView: The view for the specified container type

        Raises:
            ValueError: If structure/protocol combination is unsupported
        """
        from .dict import DictView
        from .list import ListView

        if self._satisfies_dict_view(structure, protocol):
            return DictView(
                backend=self.backend,
                path=self.path.join(key),
                tx=self.tx,
            )
        elif self._satisfies_list_view(structure, protocol):
            return ListView(
                backend=self.backend,
                path=self.path.join(key),
                tx=self.tx,
            )
        else:
            raise ValueError(
                f"Unsupported structure `{structure}` and protocol `{protocol}` for view creation"
            )

    def _get_view_for_value(self, key: PathComponent, value: Value, /) -> BaseView:
        """
        Get appropriate view for a value being stored.

        Args:
            key: Child key to retrieve
            value: Value to store (can be primitive or container)

        Returns:
            BaseView: The view for the specified value type

        Raises:
            ValueError: If value type is unsupported for view creation
        """
        from .dict import DictView
        from .list import ListView

        child_path = self.path.join(key)
        if isinstance(value, dict):
            return DictView(backend=self.backend, path=child_path, tx=self.tx)
        elif isinstance(value, list):
            return ListView(backend=self.backend, path=child_path, tx=self.tx)
        else:
            raise ValueError(f"Unsupported value type `{type(value)}` for view creation")

    def _is_value_primitive(self, value: Value, /) -> bool:
        """
        Check if value should be stored as primitive.

        Args:
            value: Value to check

        Returns:
            bool: True if value is primitive (not a container), False otherwise
        """
        return not isinstance(value, (dict, list, set, tuple))

    @staticmethod
    def _satisfies_dict_view(structure: ContainerStructure, protocol: ContainerProtocol, /) -> bool:
        """
        Check if structure/protocol supports dictionary view.

        Args:
            structure: Container structure type
            protocol: Container protocol type

        Returns:
            bool: True if structure/protocol supports dictionary view
        """
        return structure == ContainerStructure.MAPPING_CONTAINER

    @staticmethod
    def _satisfies_list_view(structure: ContainerStructure, protocol: ContainerProtocol, /) -> bool:
        """
        Check if structure/protocol supports list view.

        Args:
            structure: Container structure type
            protocol: Container protocol type

        Returns:
            bool: True if structure/protocol supports list view
        """
        return structure == ContainerStructure.INDEXED_CONTAINER

    # =========================================================================
    # ABSTRACT INTERFACE
    # =========================================================================

    @abstractmethod
    def store(self, value: Value, /, *, replace: bool = False) -> None:
        """
        Store value in the view. Implemented by subclasses.

        Args:
            value: Value to store in the view
            replace: If True, replaces existing value at the path. Otherwise appends to existing list. Default is False.
        """
        raise NotImplementedError("Subclasses must implement store()")

    @abstractmethod
    def extract(self) -> Value | Empty:
        """
        Extract value from the view. Implemented by subclasses.

        Returns:
            Value or Empty: Extracted value from the view, or EMPTY if not found
        """
        raise NotImplementedError("Subclasses must implement extract()")
