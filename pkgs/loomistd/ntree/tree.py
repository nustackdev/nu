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

from .backend import SubscriptionProtocol, TransactionContextManagerProtocol, TransactionProtocol
from .path import Path
from .transaction import TransactionalBase
from .types import CallbackFn, PathComponent
from .view import DictView, ListView, create_view_context_manager

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

    path: Path = attrs.field(factory=Path, eq=False, hash=False, alias=None)

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
        return attrs.evolve(self, path=Path(), tx=tx or self.tx)

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

    def with_list_view(self) -> AbstractContextManager[ListView]:
        """
        Access container as list view with automatic transaction management.

        Returns a context manager that yields a ListView with transaction context.
        If path doesn't exist, creates a new sequence container.

        Returns:
            Context manager yielding ListView with transaction

        Example:
            ```python
            # Automatic transaction - recommended for mutations
            with tree.at("tasks").with_list_view() as tasks:
                tasks.append("Setup project")
                tasks.append("Write documentation")
                tasks.insert(1, "Create tests")
            # Transaction automatically committed on success

            # Nested container operations
            with tree.at("projects").with_list_view() as projects:
                projects.append({"name": "Project 1", "tasks": []})

                # Access nested dict in list
                project_dict = projects.dict_view(0)
                project_dict.set("status", "active")
            ```
        """
        return create_view_context_manager(
            ListView, backend=self.backend, path=self.path, tx=self.tx
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

    def list_view(self, *, tx: Optional[TransactionProtocol] = None) -> ListView:
        """
        Access container as list view with manual transaction management.

        Returns a ListView object directly. No automatic transaction handling.
        If path doesn't exist, creates a new sequence container when accessed.

        Args:
            tx: Optional transaction (defaults to current transaction)

        Returns:
            ListView: List view for the container

        Example:
            ```python
            # Direct usage - good for reads
            tasks = tree.at("tasks").list_view()
            task_count = tasks.length()
            tasks_list = tasks.to_list()

            # Manual transaction management
            tx = tree.begin_transaction()
            try:
                tasks = tree.at("tasks").list_view(tx=tx)
                tasks.append("New task")
                tx.commit()
            except Exception:
                tx.rollback()
                raise

            # Accessing nested containers
            tasks = tree.at("tasks").list_view()
            if tasks.length() > 0:
                first_task_dict = tasks.dict_view(0)  # Access first item as dict
                first_task_dict.set("completed", True)
            ```
        """
        return ListView(backend=self.backend, path=self.path, tx=tx or self.tx)

    # =========================================================================
    # Transaction Methods
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

                tags = tree.at("tags").set_view(tx=tx)
                tags.add("user_management")

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

    def transaction(self) -> TransactionContextManagerProtocol:
        """
        Get transaction context manager for combined storage and notification handling.

        Returns:
            Transaction context manager for use in with statements

        Example:
            ```python
            with kv.transaction() as txn:
                txn.set(key1, value1)
                txn.set(key2, value2)
                # Auto-commits and notifies on success
                # Auto-rollbacks with no notifications on failure
            ```
        """
        return self.backend.transaction()

    # =========================================================================
    # Subscription Methods
    # =========================================================================

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

            with tree.at("tasks").with_list_view() as tasks:
                tasks.append("New task")  # Triggers callback if subscribed to root

            # Later, unsubscribe
            sub.unsubscribe()
            ```
        """
        return self.backend.subscribe(self.path.to_tuple(), callback, depth)

    def unsubscribe(self, subscription: SubscriptionProtocol) -> None:
        """
        Unsubscribe from changes under key prefix.

        Args:
            subscription: Subscription to cancel

        Raises:
            ObserverError: If unsubscribe fails
        """
        self.backend.unsubscribe(subscription)
