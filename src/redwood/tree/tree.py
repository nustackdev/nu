"""This module implement Tree class - the primary interface for accessing the tree storage.

This module defines the Tree class, which is the primary interface for accessing
and manipulating the tree storage. It provides methods for navigation, accessing nodes,
checking types, and creating views with clean separation between context manager
and direct access patterns.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Self

import attrs

from redwood.abc import EMPTY, CallbackFn, Empty, KeyComponent, TupleKey, Value
from redwood.exceptions import StorageKeyError

from .context import ContextualBase
from .path import Path
from .registry import ViewRegistry
from .view import create_view_context_manager


if TYPE_CHECKING:
    from contextlib import AbstractContextManager

    from redwood.be import (
        SnapshotContextManagerProtocol,
        SnapshotProtocol,
        StorageContextType,
        SubscriptionProtocol,
        TransactionContextManagerProtocol,
        TransactionProtocol,
    )

    from .view import View

__all__ = [
    "Tree",
]


@attrs.define(frozen=True, kw_only=True)
class Tree(ContextualBase):
    """Primary interface for accessing the tree storage.

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

    path: TupleKey = attrs.field(factory=Path.create, eq=False, hash=False, alias=None)

    registry: ViewRegistry = attrs.field(factory=ViewRegistry, eq=False, hash=False)

    # =========================================================================
    # TREE NAVIGATION METHODS
    # =========================================================================

    def at(self, *paths: KeyComponent, ctx: StorageContextType | None = None) -> Self:
        """Navigate to a path (relative to current path).

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
        new_path = Path.join(self.path, *paths)
        return attrs.evolve(self, path=new_path, ctx=ctx or self.ctx)

    def parent(self, *, ctx: StorageContextType | None = None) -> Self:
        """Navigate to parent path.

        Returns:
            State: State for the parent path, or self if already at root

        Example:
            ```python
            user = tree.at("users", "alice")
            users = user.parent()
            ```
        """
        parent_path = Path.parent(self.path)
        if parent_path is None:
            # Already at root
            return self
        return attrs.evolve(self, path=parent_path, ctx=ctx or self.ctx)

    def root(self, *, ctx: StorageContextType | None = None) -> Self:
        """Navigate to root path.

        Returns:
            State: State for the root path

        Example:
            ```python
            root = tree.at("deeply", "nested", "path").root()
            ```
        """
        return attrs.evolve(self, path=Path(), ctx=ctx or self.ctx)

    # =========================================================================
    # CONTEXT MANAGERS FOR VIEWS (automatic context management)
    # =========================================================================

    def with_view[ViewT: View](
        self,
        view_type: type[ViewT],
        /,
        *,
        snapshot: bool = False,
    ) -> AbstractContextManager[ViewT]:
        """Access container as specified view type with automatic transaction or snapshot management.

        Returns a context manager that yields a view of the specified type.
        If path doesn't exist, creates a new container of the specified type.

        Args:
            view_type: Type of view to create
            snapshot: If True, creates a read-only snapshot view instead of a transaction view

        Returns:
            Context manager yielding View for the container

        Example:
            ```python
            # Automatic transaction - recommended for mutations
            with tree.at("users").with_view(DictView) as users:
                users.set("alice", {"email": "alice@example.com"})
                users.set("bob", {"email": "bob@example.com"})

                # Nested operations inherit the transaction
                alice_profile = users.dict_view("alice")
                alice_profile.set("location", "San Francisco")
            # Transaction automatically committed on success

            # Read-only snapshot - recommended for consistent reads
            with tree.at("users").with_view(DictView, snapshot=True) as users:
                user_count = len(users.keys())
                users_dict = users.to_dict()
                # Read-only operations only
            # Snapshot automatically cleaned up

            # Error handling
            try:
                with tree.at("users").with_view(DictView) as users:
                    users.set("invalid", None)  # This might raise an error
                    raise ValueError("Something went wrong")
            except ValueError:
                # Transaction automatically rolled back
                pass
            ```
        """
        return create_view_context_manager(
            view_type,
            snapshot=snapshot,
            backend=self.backend,
            path=self.path,
            ctx=self.ctx,
            tree=self,
        )

    # =========================================================================
    # DIRECT VIEW ACCESS (manual context management)
    # =========================================================================

    def view[ViewT: View](
        self,
        view_type: type[ViewT],
        /,
        *,
        ctx: StorageContextType | None = None,
    ) -> ViewT:
        """Access container as specified view type with manual context (transaction/snapshot) management.

        Returns a view object directly. No automatic context handling.
        If path doesn't exist, creates a new container of the specified type.

        Args:
            view_type: Type of view to create
            ctx: Optional context (defaults to current context)

        Returns:
            View for the container

        Example:
            ```python
            # Direct usage - good for reads
            users = tree.at("users").view(DictView)
            user_count = len(users.keys())
            users_dict = users.to_dict()

            # Manual transaction management
            tx = tree.begin_transaction()
            try:
                users = tree.at("users").view(DictView, ctx=tx)
                users.set("alice", {"email": "alice@example.com"})
                tx.commit()
            except Exception:
                tx.rollback()
                raise
            ```
        """
        return view_type(backend=self.backend, path=self.path, ctx=ctx or self.ctx, tree=self)

    # =========================================================================
    # CONTEXT METHODS (unified transaction and snapshot support)
    # =========================================================================

    def begin_context(self, *, snapshot: bool = False) -> StorageContextType:
        """Start a new context (transaction or snapshot).

        Args:
            snapshot: If True, creates read-only snapshot. If False, creates transaction.

        Returns:
            Context instance (transaction or snapshot)

        Example:
            ```python
            # Transaction context
            ctx = tree.begin_context()
            try:
                view = tree.dict_view(ctx=ctx)
                view.set("key", "value")
                ctx.commit()
            except Exception:
                ctx.rollback()
                raise

            # Snapshot context
            ctx = tree.begin_context(snapshot=True)
            try:
                view = tree.dict_view(ctx=ctx)
                value = view.get("key")
            finally:
                ctx.close()
            ```
        """
        if snapshot:
            return self.backend.begin_snapshot()
        else:
            return self.backend.begin_transaction()

    # =========================================================================
    # TRANSACTION METHODS
    # =========================================================================

    def begin_transaction(self) -> TransactionProtocol:
        """Start a new transaction.

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

    def begin_snapshot(self) -> SnapshotProtocol:
        """Start a new read-only snapshot.

        Returns:
            Snapshot instance for read-only operations

        Example:
            ```python
            snap = tree.begin_snapshot()
            try:
                view = tree.dict_view(ctx=snap)
                value = view.get("key")
            finally:
                snap.close()
            ```
        """
        return self.backend.begin_snapshot()

    def transaction(self) -> TransactionContextManagerProtocol:
        """Get transaction context manager for combined storage and notification handling.

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

    def snapshot(self) -> SnapshotContextManagerProtocol:
        """Get snapshot context manager for read-only operations.

        Returns:
            Snapshot context manager for use in with statements

        Example:
            ```python
            with tree.snapshot() as snap:
                view = tree.dict_view(ctx=snap)
                value = view.get("key")
                # Read-only operations only
                # Auto-cleanup on exit
            ```
        """
        return self.backend.snapshot()

    # =========================================================================
    # OBSERVATION METHODS
    # =========================================================================

    def subscribe(self, callback: CallbackFn, depth: int = 0) -> SubscriptionProtocol:
        """Subscribe to changes at the current path.

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
        return self.backend.subscribe(self.path, callback, depth)

    def unsubscribe(self, subscription: SubscriptionProtocol) -> None:
        """Unsubscribe from changes under key prefix.

        Args:
            subscription: Subscription to cancel

        Raises:
            ObserverError: If unsubscribe fails
        """
        self.backend.unsubscribe(subscription)

    # =========================================================================
    # SHORTCUTS FOR COMMON OPERATIONS
    # =========================================================================

    def has_primitive(self, *paths: KeyComponent) -> bool:
        """Check if a path exists.

        Args:
            *paths: Path components to check

        Returns:
            bool: True if path exists, False otherwise

        Example:
            ```python
            if tree.at("users").has("alice"):
                print("Alice exists")
            else:
                print("Alice does not exist")
            ```
        """
        return self.backend.exists(Path.join(self.path, *paths))

    def get_primitive(self, *paths: KeyComponent, default: Value | Empty = EMPTY) -> Value | Empty:
        """Get value at a path.

        Args:
            *paths: Path components to get
            default: Default value if path does not exist

        Returns:
            Value at the path, or default if not found

        Example:
            ```python
            email = tree.at("users", "alice").get("email", default="not found")
            if email is None:
                print("Alice's email not found")
            else:
                print(f"Alice's email: {email}")
            ```
        """
        try:
            return self.backend.get(Path.join(self.path, *paths))
        except StorageKeyError:
            return default

    # IMPORTANT:
    # - Mutation operations (e.g. `set` and `remove`) are not implemented, as they are handled by View's specific methods.
    #   Views might implement specific logic for setting and removing values (e.g. indexed Views keeping aggregated data),
    #   so we don't want to bypass them here.
    #   Instead, users should use corresponding Views to perform these operations in a consistent manner.
    # - Hypothetically, `has` and `read` operations might also have specific logic in Views, but until we have a use case for that,
    #   we keep shortcut methods here for simplicity.

    def is_primitive(self, *paths: KeyComponent) -> bool:
        """Check if a path is a primitive (non-container).

        Args:
            *paths: Path components to check

        Returns:
            bool: True if path is a primitive, False otherwise

        Example:
            ```python
            if tree.at("users").is_primitive("alice", "email"):
                print("Alice's email is a primitive value")
            else:
                print("Alice's email is not a primitive value")
            ```
        """
        return self.backend.exists(Path.join(self.path, *paths))
