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

**Transaction Context Pattern**
Methods like get(), set(), and to_dict() wrap their operations with:
- `with with_transaction(self.container) as container:`
This pattern ensures every storage access happens within a transaction boundary,
providing ACID guarantees while allowing operations to be composed safely within
larger transaction scopes.

**Trade-off: Safety vs Performance**
The immutable design trades some performance for safety and correctness. Each
operation may create temporary objects, but this overhead is minimal compared to
the benefits of eliminating concurrency bugs, providing predictable behavior,
and enabling safe caching strategies throughout the system.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

import attrs

from ..node import ContainerNode
from ..path import Path
from ..transaction import TransactionalBase
from ..types import ContainerProtocol, ContainerStructure, Empty, PathComponent, Value

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

    def get_view_for_container(
        self,
        key: PathComponent,
        structure: ContainerStructure,
        protocol: ContainerProtocol,
        /,
    ) -> BaseView:
        """
        Get the appropriate view class for the given container.

        Args:
            container (ContainerNode): The container node to get the view for.
            tx (TransactionalBase | None): Optional transaction context.

        Returns:
            BaseView: An instance of the appropriate view class.
        """
        from .dict import DictView
        from .list import ListView

        if self.satisfies_dict_view(structure, protocol):
            view = DictView(
                backend=self.backend,
                path=self.path.join(key),
                tx=self.tx,
            )
        elif self.satisfies_list_view(structure, protocol):
            view = ListView(
                backend=self.backend,
                path=self.path.join(key),
                tx=self.tx,
            )
        else:
            raise ValueError(
                f"Unsupported structure `{structure}` and protocol `{protocol}` for view creation"
            )

        return view

    def get_view_for_value(self, key: PathComponent, value: Value, /) -> BaseView:
        """
        Get the appropriate view for a given key and value.

        Args:
            key (PathComponent): The key for the value.
            value (Value): The value to create a view for.
        Returns:
            BaseView: An instance of the appropriate view class for the value type.
        Raises:
            ValueError: If the value type is unsupported.
        """
        from .dict import DictView
        from .list import ListView

        child_key = self.path.join(key)
        if isinstance(value, dict):
            # Create nested mapping container
            child_view = DictView(
                backend=self.backend,
                path=child_key,
                tx=self.tx,
            )
        elif isinstance(value, list):
            child_view = ListView(
                backend=self.backend,
                path=child_key,
                tx=self.tx,
            )
        else:
            raise ValueError(f"Unsupported value type `{type(value)}` for view creation")
        return child_view

    def is_value_primitive(self, value: Value, /) -> bool:
        """
        Check if the value is a primitive type.
        Args:
            value (Value): The value to check.
        Returns:
            bool: True if the value is a primitive type, False otherwise.
        """
        return not isinstance(value, (dict, list, set, tuple))

    @staticmethod
    def satisfies_dict_view(structure: ContainerStructure, protocol: ContainerProtocol) -> bool:
        """
        Check if the current view satisfies the dictionary view requirements.

        Returns:
            bool: True if the view can be treated as a dictionary, False otherwise.
        """
        return structure == ContainerStructure.MAPPING_CONTAINER

    @staticmethod
    def satisfies_list_view(structure: ContainerStructure, protocol: ContainerProtocol) -> bool:
        """
        Check if the current view satisfies the list view requirements.

        Returns:
            bool: True if the view can be treated as a list, False otherwise.
        """
        return structure == ContainerStructure.SEQUENCE_CONTAINER

    @abstractmethod
    def store(self, value: Value, /) -> None:
        """
        Store the value in the view.

        This method should be implemented by subclasses to persist
        the value in the underlying storage.

        Raises:
            NotImplementedError: If not implemented by subclass
        """

        raise NotImplementedError("Subclasses must implement the store method")

    @abstractmethod
    def extract(self) -> Value | Empty:
        """
        Extract the value from the view.

        This method should be implemented by subclasses to return
        the value stored in the view.

        Returns:
            Value: The value extracted from the view
        """
        raise NotImplementedError("Subclasses must implement the extract method")

    @property
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
