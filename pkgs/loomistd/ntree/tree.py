"""
This module implement Tree class - the primary interface for accessing the tree storage.

This module defines the Tree class, which is the primary interface for accessing
and manipulating the tree storage. It provides methods for navigation, accessing nodes,
checking types, and creating views with clean separation between context manager
and direct access patterns.
"""

from __future__ import annotations

from contextlib import AbstractContextManager
from typing import Optional, Self

import attrs

from .backend import SubscriptionProtocol, TransactionProtocol
from .path import DataPath
from .transaction import TransactionalBase
from .types import CallbackFn, PathComponent
from .view import DictView, create_view_context_manager

__all__ = [
    "Tree",
]


@attrs.define(frozen=True, kw_only=True)
class Tree(TransactionalBase):
    """
    Primary interface for accessing the tree storage.

    Tree provides methods for navigating the tree, querying and manipulating nodes,
    and creating appropriate views for container nodes. It follows a filesystem-like
    mental model, where containers are like directories and primitives are like files.

    The Tree class provides two patterns for accessing views:
    1. Context manager methods (with_*_view) - Automatic transaction management
    2. Direct access methods (*_view) - Manual transaction management

    Example:
        ```python
        # Navigation
        users = tree.at("users")
        alice = users.at("alice")

        # Context manager usage (recommended for mutations)
        with tree.at("users").with_dict_view() as users:
            users.set("alice", {"email": "alice@example.com"})
            users.set("bob", {"email": "bob@example.com"})

        # Direct usage (for reads or manual transaction management)
        users = tree.at("users").dict_view()
        user_count = len(users.keys())
        users_dict = users.to_dict()

        # Navigation with context manager
        with tree.at("users").with_dict_view() as users:
            if users.has("alice"):
                alice_profile = users.dict_view("alice")  # Inherits transaction
                alice_profile.set("location", "San Francisco")

        # Manual transaction management
        tx = tree.begin_transaction()
        try:
            users = tree.at("users").dict_view(tx=tx)
            users.set("charlie", {"email": "charlie@example.com"})
            tx.commit()
        except Exception:
            tx.rollback()
            raise
        ```
    """

    path: DataPath = attrs.field(factory=DataPath, eq=False, hash=False, alias=None)

    def at(self, *paths: PathComponent, tx: Optional[TransactionProtocol] = None) -> Self:
        """
        Navigate to a path (relative to current path).

        This creates a new State instance pointing to the specified path.

        Args:
            *paths: Path components to navigate to
            tx: Optional transaction (defaults to current transaction)

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
        return attrs.evolve(self, path=new_path, tx=tx or self.tx)

    def parent(self, *, tx: Optional[TransactionProtocol] = None) -> Self:
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
            return self
        return attrs.evolve(self, path=parent_path, tx=tx or self.tx)

    def root(self, *, tx: Optional[TransactionProtocol] = None) -> Self:
        """
        Navigate to root path.

        Returns:
            State: State for the root path

        Example:
            ```python
            root = tree.at("deeply", "nested", "path").root()
            ```
        """
        return attrs.evolve(self, path=DataPath(), tx=tx or self.tx)

    # =========================================================================
    # Context Manager Methods (Automatic Transaction Management)
    # =========================================================================

    def with_dict_view(self) -> AbstractContextManager[DictView]:
        """
        Access container as dictionary view with automatic transaction management.

        Returns a context manager that yields a DictView with transaction context.
        If path doesn't exist, creates a new mapping container.

        Returns:
            Context manager yielding DictView with transaction

        Example:
            ```python
            # Automatic transaction - recommended for mutations
            with tree.at("users").with_dict_view() as users:
                users.set("alice", {"email": "alice@example.com"})
                users.set("bob", {"email": "bob@example.com"})

                # Nested operations inherit the transaction
                alice_profile = users.dict_view("alice")
                alice_profile.set("location", "San Francisco")
            # Transaction automatically committed on success

            # Error handling
            try:
                with tree.at("users").with_dict_view() as users:
                    users.set("invalid", None)  # This might raise an error
                    raise ValueError("Something went wrong")
            except ValueError:
                # Transaction automatically rolled back
                pass
            ```
        """
        return create_view_context_manager(
            DictView, backend=self.backend, path=self.path, tx=self.tx
        )

    # =========================================================================
    # Direct Access Methods (Manual Transaction Management)
    # =========================================================================

    def dict_view(self, *, tx: Optional[TransactionProtocol] = None) -> DictView:
        """
        Access container as dictionary view with manual transaction management.

        Returns a DictView object directly. No automatic transaction handling.
        If path doesn't exist, creates a new mapping container when accessed.

        Args:
            tx: Optional transaction (defaults to current transaction)

        Returns:
            DictView: Dictionary view for the container

        Example:
            ```python
            # Direct usage - good for reads
            users = tree.at("users").dict_view()
            user_count = len(users.keys())
            users_dict = users.to_dict()

            # Manual transaction management
            tx = tree.begin_transaction()
            try:
                users = tree.at("users").dict_view(tx=tx)
                users.set("alice", {"email": "alice@example.com"})
                tx.commit()
            except Exception:
                tx.rollback()
                raise

            # Use existing transaction from context
            with tree.with_dict_view() as root_dict:
                # This inherits the transaction from the context
                users = tree.at("users").dict_view()
                users.set("bob", {"email": "bob@example.com"})
            ```
        """
        return DictView(backend=self.backend, path=self.path, tx=tx or self.tx)

    # =========================================================================
    # Transaction and Subscription Methods
    # =========================================================================

    def begin_transaction(self) -> TransactionProtocol:
        """
        Start a new transaction.

        Returns:
            TransactionProtocol: New transaction

        Example:
            ```python
            # Manual transaction management
            tx = tree.begin_transaction()
            try:
                users = tree.at("users").dict_view(tx=tx)
                users.set("alice", {"name": "Alice"})

                tasks = tree.at("tasks").list_view(tx=tx)
                tasks.append("Greet Alice")

                tx.commit()
            except Exception:
                tx.rollback()
                raise

            # Or use context manager for automatic management
            with tree.at("users").with_dict_view() as users:
                users.set("alice", {"name": "Alice"})
            # Much cleaner!
            ```
        """
        return self.backend.begin_transaction()

    def subscribe(self, callback: CallbackFn, depth: int = 0) -> SubscriptionProtocol:
        """
        Subscribe to changes at the current path.

        Args:
            callback: Function to call when changes occur
            depth: Depth of topic pattern matching
                0 for exact match
                1 for immediate children
                -1 for all descendants

        Returns:
            SubscriptionProtocol: Subscription for unsubscribing

        Example:
            ```python
            def on_user_change(path):
                print(f"User path {path} changed")

            # Subscribe to changes in the users container
            sub = tree.at("users").subscribe(on_user_change, depth=1)

            # Make some changes (will trigger callback)
            with tree.at("users").with_dict_view() as users:
                users.set("alice", {"name": "Alice"})  # Triggers callback

            # Later, unsubscribe
            sub.unsubscribe()
            ```
        """
        return self.backend.subscribe(self.path.to_tuple(), callback, depth)
