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

from abc import ABC

import attrs

from ..node import ContainerNode
from ..path import Path
from ..transaction import TransactionalBase
from ..types import ContainerProtocol, ContainerStructure

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

        container = ContainerNode.create(
            backend=self.backend,
            path=self.path,
            structure=self.structure,
            protocol=self.protocol,
            tx=self.tx,
        )

        # Ensure container exists
        container.ensure_exists()

        return container
