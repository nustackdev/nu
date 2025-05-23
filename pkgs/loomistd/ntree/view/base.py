"""
Base view implementation for the state management system.

This module defines the BaseView class, which provides common functionality
for all view implementations. Views provide protocol-specific interfaces
for interacting with container nodes.

BaseView is now a pure frozen dataclass that provides shared functionality
without any transaction context manager logic. Transaction handling is
managed by the State class factory methods.
"""

from __future__ import annotations

from abc import ABC

import attrs

from ..node import ContainerNode
from ..path import DataPath
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
    path: DataPath = attrs.field(eq=False, hash=False, alias=None)

    # Container structure type
    structure: ContainerStructure = attrs.field(eq=False, hash=False, alias=None)

    # Container protocol type
    protocol: ContainerProtocol = attrs.field(eq=False, hash=False, alias=None)

    @property
    def container(self) -> ContainerNode:
        """
        Get the container node for this view.

        Creates a ContainerNode with the appropriate configuration
        and ensures it exists.

        Returns:
            ContainerNode: The container node
        """
        container = ContainerNode(
            backend=self.backend,
            path=self.path,
            structure=self.structure,
            protocol=self.protocol,
            tx=self.tx,
        )

        # Ensure container exists
        container.ensure_exists()
        return container
