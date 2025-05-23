"""
State implementation for the state management system.

This module defines the State class, which is the primary interface for accessing
and manipulating the state tree. It provides methods for navigation, accessing nodes,
checking types, and creating views with clean separation between context manager
and direct access patterns.
"""

from __future__ import annotations

from typing import Optional

import attrs

from loomi.interfaces.state.observer import SyncSubscriptionProtocol

from .._core.path import StatePath
from .._core.transaction import TransactionalBase, create_view_context_manager
from .._state.backend import ObservableKVTransaction
from .._types import PathComponent, StateCallbackFn
from .._views.dict_view import DictView

# from .._views.list_view import ListView
# from .._views.set_view import SetView

__all__ = ["State"]


@attrs.define(frozen=True, kw_only=True)
class State(TransactionalBase):
    """
    Primary interface for accessing the state tree.

    State provides methods for navigating the tree, querying and manipulating nodes,
    and creating appropriate views for container nodes. It follows a filesystem-like
    mental model, where containers are like directories and primitives are like files.

    The State class now provides two patterns for accessing views:
    1. Context manager methods (with_*_view) - Automatic transaction management
    2. Direct access methods (*_view) - Manual transaction management

    Example:
        ```python
        state = state_service.state

        # Navigation
        users = state.at("users")
        alice = users.at("alice")

        # Context manager usage (recommended for mutations)
        with state.at("users").with_dict_view() as users:
            users.set("alice", {"email": "alice@example.com"})
            users.set("bob", {"email": "bob@example.com"})

        # Direct usage (for reads or manual transaction management)
        users = state.at("users").dict_view()
        user_count = len(users.keys())
        users_dict = users.to_dict()

        # Navigation with context manager
        with state.at("users").with_dict_view() as users:
            if users.has("alice"):
                alice_profile = users.dict_view("alice")  # Inherits transaction
                alice_profile.set("location", "San Francisco")

        # Manual transaction management
        tx = state.begin_transaction()
        try:
            users = state.at("users").dict_view(tx=tx)
            users.set("charlie", {"email": "charlie@example.com"})
            tx.commit()
        except Exception:
            tx.rollback()
            raise
        ```
    """

    path: StatePath = attrs.field(factory=StatePath, eq=False, hash=False, alias=None)

    def at(self, *paths: PathComponent, tx: Optional[ObservableKVTransaction] = None) -> State:
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
            user = state.at("users", "alice")
            email = state.at("users", "alice", "email")

            # Navigation with context manager
            with state.at("users").with_dict_view() as users:
                # Operations with transaction
                users.set("alice", {"name": "Alice"})

            # Navigation with direct access
            users = state.at("users").dict_view()
            alice_data = users.get("alice")
            ```
        """
        new_path = self.path.join(*paths)
        return attrs.evolve(self, path=new_path, tx=tx or self.tx)

    def parent(self, *, tx: Optional[ObservableKVTransaction] = None) -> State:
        """
        Navigate to parent path.

        Returns:
            State: State for the parent path, or self if already at root

        Example:
            ```python
            user = state.at("users", "alice")
            users = user.parent()
            ```
        """
        parent_path = self.path.parent()
        if parent_path is None:
            # Already at root
            return self
        return attrs.evolve(self, path=parent_path, tx=tx or self.tx)

    def root(self, *, tx: Optional[ObservableKVTransaction] = None) -> State:
        """
        Navigate to root path.

        Returns:
            State: State for the root path

        Example:
            ```python
            root = state.at("deeply", "nested", "path").root()
            ```
        """
        return attrs.evolve(self, path=StatePath(), tx=tx or self.tx)

    # =========================================================================
    # Context Manager Methods (Automatic Transaction Management)
    # =========================================================================

    def with_dict_view(self):
        """
        Access container as dictionary view with automatic transaction management.

        Returns a context manager that yields a DictView with transaction context.
        If path doesn't exist, creates a new mapping container.

        Returns:
            Context manager yielding DictView with transaction

        Example:
            ```python
            # Automatic transaction - recommended for mutations
            with state.at("users").with_dict_view() as users:
                users.set("alice", {"email": "alice@example.com"})
                users.set("bob", {"email": "bob@example.com"})

                # Nested operations inherit the transaction
                alice_profile = users.dict_view("alice")
                alice_profile.set("location", "San Francisco")
            # Transaction automatically committed on success

            # Error handling
            try:
                with state.at("users").with_dict_view() as users:
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

    # def with_list_view(self):
    #     """
    #     Access container as list view with automatic transaction management.

    #     Returns a context manager that yields a ListView with transaction context.
    #     If path doesn't exist, creates a new sequence container.

    #     Returns:
    #         Context manager yielding ListView with transaction

    #     Example:
    #         ```python
    #         with state.at("tasks").with_list_view() as tasks:
    #             tasks.append("Buy groceries")
    #             tasks.append("Walk the dog")
    #         # Transaction automatically committed
    #         ```
    #     """
    #     return create_view_context_manager(
    #         ListView,
    #         _backend=self._backend,
    #         _path=self._path,
    #         _tx=self.tx
    #     )

    # def with_set_view(self):
    #     """
    #     Access container as set view with automatic transaction management.

    #     Returns a context manager that yields a SetView with transaction context.
    #     If path doesn't exist, creates a new set container.

    #     Returns:
    #         Context manager yielding SetView with transaction

    #     Example:
    #         ```python
    #         with state.at("tags").with_set_view() as tags:
    #             tags.add("important")
    #             tags.add("urgent")
    #         # Transaction automatically committed
    #         ```
    #     """
    #     return create_view_context_manager(
    #         SetView,
    #         _backend=self._backend,
    #         _path=self._path,
    #         _tx=self.tx
    #     )

    # =========================================================================
    # Direct Access Methods (Manual Transaction Management)
    # =========================================================================

    def dict_view(self, *, tx: Optional[ObservableKVTransaction] = None) -> DictView:
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
            users = state.at("users").dict_view()
            user_count = len(users.keys())
            users_dict = users.to_dict()

            # Manual transaction management
            tx = state.begin_transaction()
            try:
                users = state.at("users").dict_view(tx=tx)
                users.set("alice", {"email": "alice@example.com"})
                tx.commit()
            except Exception:
                tx.rollback()
                raise

            # Use existing transaction from context
            with state.with_dict_view() as root_dict:
                # This inherits the transaction from the context
                users = state.at("users").dict_view()
                users.set("bob", {"email": "bob@example.com"})
            ```
        """
        return DictView(backend=self.backend, path=self.path, tx=tx or self.tx)

    # def list_view(self, *, tx: Optional[ObservableKVTransaction] = None) -> ListView:
    #     """
    #     Access container as list view with manual transaction management.

    #     Returns a ListView object directly. No automatic transaction handling.
    #     If path doesn't exist, creates a new sequence container when accessed.

    #     Args:
    #         tx: Optional transaction (defaults to current transaction)

    #     Returns:
    #         ListView: List view for the container

    #     Example:
    #         ```python
    #         # Direct usage
    #         tasks = state.at("tasks").list_view()
    #         task_count = len(tasks)

    #         # Manual transaction
    #         tx = state.begin_transaction()
    #         try:
    #             tasks = state.at("tasks").list_view(tx=tx)
    #             tasks.append("Buy groceries")
    #             tx.commit()
    #         except Exception:
    #             tx.rollback()
    #             raise
    #         ```
    #     """
    #     return ListView(
    #         _backend=self._backend,
    #         _path=self._path,
    #         _tx=tx or self.tx
    #     )

    # def set_view(self, *, tx: Optional[ObservableKVTransaction] = None) -> SetView:
    #     """
    #     Access container as set view with manual transaction management.

    #     Returns a SetView object directly. No automatic transaction handling.
    #     If path doesn't exist, creates a new set container when accessed.

    #     Args:
    #         tx: Optional transaction (defaults to current transaction)

    #     Returns:
    #         SetView: Set view for the container

    #     Example:
    #         ```python
    #         # Direct usage
    #         tags = state.at("tags").set_view()
    #         has_important = tags.contains("important")

    #         # Manual transaction
    #         tx = state.begin_transaction()
    #         try:
    #             tags = state.at("tags").set_view(tx=tx)
    #             tags.add("urgent")
    #             tx.commit()
    #         except Exception:
    #             tx.rollback()
    #             raise
    #         ```
    #     """
    #     return SetView(
    #         _backend=self._backend,
    #         _path=self._path,
    #         _tx=tx or self.tx
    #     )

    # =========================================================================
    # Transaction and Subscription Methods
    # =========================================================================

    def begin_transaction(self) -> ObservableKVTransaction:
        """
        Start a new transaction.

        Returns:
            ObservableKVTransaction: New transaction

        Example:
            ```python
            # Manual transaction management
            tx = state.begin_transaction()
            try:
                users = state.at("users").dict_view(tx=tx)
                users.set("alice", {"name": "Alice"})

                tasks = state.at("tasks").list_view(tx=tx)
                tasks.append("Greet Alice")

                tx.commit()
            except Exception:
                tx.rollback()
                raise

            # Or use context manager for automatic management
            with state.at("users").with_dict_view() as users:
                users.set("alice", {"name": "Alice"})
            # Much cleaner!
            ```
        """
        return self.backend.begin_transaction()

    def subscribe(self, callback: StateCallbackFn, depth: int = 0) -> SyncSubscriptionProtocol:
        """
        Subscribe to changes at the current path.

        Args:
            callback: Function to call when changes occur
            depth: Depth of topic pattern matching
                0 for exact match
                1 for immediate children
                -1 for all descendants

        Returns:
            SyncSubscriptionProtocol: Subscription for unsubscribing

        Example:
            ```python
            def on_user_change(path):
                print(f"User path {path} changed")

            # Subscribe to changes in the users container
            sub = state.at("users").subscribe(on_user_change, depth=1)

            # Make some changes (will trigger callback)
            with state.at("users").with_dict_view() as users:
                users.set("alice", {"name": "Alice"})  # Triggers callback

            # Later, unsubscribe
            sub.unsubscribe()
            ```
        """
        return self.backend.subscribe(self.path.to_tuple(), callback, depth)
