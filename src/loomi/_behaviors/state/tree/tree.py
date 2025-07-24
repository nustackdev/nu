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

from loomistd.kv import StorageKeyError

from ..backend import (
    SnapshotContextManagerProtocol,
    SnapshotProtocol,
    SubscriptionProtocol,
    TransactionContextManagerProtocol,
    TransactionProtocol,
)
from .context import ContextType, ContextualBase
from .node import ContainerNode
from .path import Path
from .types import EMPTY, CallbackFn, Empty, PathComponent, Value
from .view import DictView, ListView, create_view_context_manager

__all__ = [
    "Tree",
]


@attrs.define(frozen=True, kw_only=True)
class Tree(ContextualBase):
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

    # =========================================================================
    # TREE NAVIGATION METHODS
    # =========================================================================

    def at(self, *paths: PathComponent, ctx: Optional[ContextType] = None) -> Self:
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
        return attrs.evolve(self, path=new_path, ctx=ctx or self.ctx)

    def parent(self, *, ctx: Optional[ContextType] = None) -> Self:
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
        return attrs.evolve(self, path=parent_path, ctx=ctx or self.ctx)

    def root(self, *, ctx: Optional[ContextType] = None) -> Self:
        """
        Navigate to root path.

        Returns:
            State: State for the root path

        Example:
            ```python
            root = tree.at("deeply", "nested", "path").root()
            ```
        """
        return attrs.evolve(self, path=Path(), ctx=ctx or self.ctx)

    # =========================================================================
    # CONTEXT MANAGERS FOR VIEWS (automatic transaction management)
    # =========================================================================

    def with_dict_view(self, *, snapshot: bool = False) -> AbstractContextManager[DictView[Self]]:
        """
        Access container as dictionary view with automatic transaction or snapshot management.

        Returns a context manager that yields a DictView with transaction or snapshot context.
        If path doesn't exist, creates a new mapping container.

        Args:
            snapshot: If True, creates a read-only snapshot view instead of a transaction view

        Returns:
            Context manager yielding DictView with transaction or snapshot

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

            # Read-only snapshot - recommended for consistent reads
            with tree.at("users").with_dict_view(snapshot=True) as users:
                user_count = len(users.keys())
                users_dict = users.to_dict()
                # Read-only operations only
            # Snapshot automatically cleaned up

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
            DictView,
            snapshot=snapshot,
            backend=self.backend,
            path=self.path,
            ctx=self.ctx,
            tree=self.__class__,
        )

    def with_list_view(self, *, snapshot: bool = False) -> AbstractContextManager[ListView[Self]]:
        """
        Access container as list view with automatic transaction or snapshot management.

        Returns a context manager that yields a ListView with transaction or snapshot context.
        If path doesn't exist, creates a new sequence container.

        Args:
            snapshot: If True, creates a read-only snapshot view instead of a transaction view

        Returns:
            Context manager yielding ListView with transaction or snapshot

        Example:
            ```python
            # Automatic transaction - recommended for mutations
            with tree.at("tasks").with_list_view() as tasks:
                tasks.append("Setup project")
                tasks.append("Write documentation")
                tasks.insert(1, "Create tests")
            # Transaction automatically committed on success

            # Read-only snapshot - recommended for consistent reads
            with tree.at("tasks").with_list_view(snapshot=True) as tasks:
                task_count = tasks.length()
                tasks_list = tasks.to_list()
                # Read-only operations only
            # Snapshot automatically cleaned up

            # Nested container operations
            with tree.at("projects").with_list_view() as projects:
                projects.append({"name": "Project 1", "tasks": []})

                # Access nested dict in list
                project_dict = projects.dict_view(0)
                project_dict.set("status", "active")
            ```
        """
        return create_view_context_manager(
            ListView,
            snapshot=snapshot,
            backend=self.backend,
            path=self.path,
            ctx=self.ctx,
            tree=self.__class__,
        )

    # =========================================================================
    # DIRECT VIEW ACCESS (manual transaction management)
    # =========================================================================

    def dict_view(self, *, ctx: Optional[ContextType] = None) -> DictView[Self]:
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
        return DictView(
            backend=self.backend, path=self.path, ctx=ctx or self.ctx, tree=self.__class__
        )

    def list_view(self, *, ctx: Optional[ContextType] = None) -> ListView[Self]:
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
        return ListView(
            backend=self.backend, path=self.path, ctx=ctx or self.ctx, tree=self.__class__
        )

    # =========================================================================
    # CONTEXT METHODS (unified transaction and snapshot support)
    # =========================================================================

    def begin_context(self, *, snapshot: bool = False) -> ContextType:
        """
        Start a new context (transaction or snapshot).

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

    def begin_snapshot(self) -> SnapshotProtocol:
        """
        Start a new read-only snapshot.

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

    def snapshot(self) -> SnapshotContextManagerProtocol:
        """
        Get snapshot context manager for read-only operations.

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

    # =========================================================================
    # SHORTCUTS FOR COMMON OPERATIONS
    # =========================================================================

    def has_primitive(self, *paths: PathComponent) -> bool:
        """
        Check if a path exists.

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
        return self.backend.exists(self.path.join(*paths).to_tuple())

    def get_primitive(self, *paths: PathComponent, default: Value | Empty = EMPTY) -> Value | Empty:
        """
        Get value at a path.

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
            return self.backend.get(self.path.join(*paths).to_tuple())
        except StorageKeyError:
            return default

    # IMPORTANT:
    # - Set and remove operations are not implemented, as they are handled by specific Views.
    #   Views might implement specific logic for setting and removing values (e.g. indexed Views keeping aggregated data),
    #   so we don't want to bypass them here.
    #   Instead, users should use corresponding Views to perform these operations in a consistent manner.
    # - Hypothetically, has and read operations might also have specific logic in Views, but until we have a use case for that,
    #   we keep shortcut methods here for simplicity.

    def is_primitive(self, *paths: PathComponent) -> bool:
        """
        Check if a path is a primitive (non-container).

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
        return self.backend.exists(self.path.join(*paths).to_tuple())

    def is_container(self, *paths: PathComponent) -> bool:
        """
        Check if a path is a container (mapping, indexed, linked, or hashed).

        Args:
            *paths: Path components to check

        Returns:
            bool: True if path is a container, False otherwise

        Example:
            ```python
            if tree.at("users").is_container("alice"):
                print("Alice's profile is a container")
            else:
                print("Alice's profile is not a container")
            ```
        """
        return self.backend.exists(self.path.join(*paths).struct_path.to_tuple())

    def is_mapping(self, *paths: PathComponent) -> bool:
        """
        Check if a path is a mapping (dictionary-like).

        Args:
            *paths: Path components to check

        Returns:
            bool: True if path is a mapping, False otherwise

        Example:
            ```python
            if tree.at("users").is_mapping("alice"):
                print("Alice's profile is a mapping")
            else:
                print("Alice's profile is not a mapping")
            ```
        """
        print(self.path.join(*paths))
        try:
            container_type_info = self.backend.get(self.path.join(*paths).struct_path.to_tuple())
            structure, protocol = ContainerNode.extract_type_info(container_type_info)
            return ContainerNode.is_mapping_container(structure, protocol)
        except StorageKeyError:
            # Container does not exist
            return False

    def is_indexed(self, *paths: PathComponent) -> bool:
        """
        Check if a path is an indexed container (list-like).

        Args:
            *paths: Path components to check

        Returns:
            bool: True if path is an indexed container, False otherwise

        Example:
            ```python
            if tree.at("tasks").is_indexed():
                print("Tasks is an indexed container")
            else:
                print("Tasks is not an indexed container")
            ```
        """
        try:
            container_type_info = self.backend.get(self.path.join(*paths).struct_path.to_tuple())
            structure, protocol = ContainerNode.extract_type_info(container_type_info)
            return ContainerNode.is_indexed_container(structure, protocol)
        except StorageKeyError:
            # Container does not exist
            return False

    def is_linked(self, *paths: PathComponent) -> bool:
        """
        Check if a path is a linked container (set-like).

        Args:
            *paths: Path components to check

        Returns:
            bool: True if path is a linked container, False otherwise

        Example:
            ```python
            if tree.at("tags").is_linked():
                print("Tags is a linked container")
            else:
                print("Tags is not a linked container")
            ```
        """
        try:
            container_type_info = self.backend.get(self.path.join(*paths).struct_path.to_tuple())
            structure, protocol = ContainerNode.extract_type_info(container_type_info)
            return ContainerNode.is_linked_container(structure, protocol)
        except StorageKeyError:
            # Container does not exist
            return False

    def is_hashed(self, *paths: PathComponent) -> bool:
        """
        Check if a path is a hashed container (hash-like).

        Args:
            *paths: Path components to check

        Returns:
            bool: True if path is a hashed container, False otherwise

        Example:
            ```python
            if tree.at("users").is_hashed():
                print("Users is a hashed container")
            else:
                print("Users is not a hashed container")
            ```
        """
        try:
            container_type_info = self.backend.get(self.path.join(*paths).struct_path.to_tuple())
            structure, protocol = ContainerNode.extract_type_info(container_type_info)
            return ContainerNode.is_hashed_container(structure, protocol)
        except StorageKeyError:
            # Container does not exist
            return False
