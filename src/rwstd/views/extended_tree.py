"""This module implement Tree class - the primary interface for accessing the tree storage.

This module defines the Tree class, which is the primary interface for accessing
and manipulating the tree storage. It provides methods for navigation, accessing nodes,
checking types, and creating views with clean separation between context manager
and direct access patterns.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Self

from redwood.tree import Tree as BaseTree
from redwood.tree import create_view_context_manager

from .dict_view import DictView
from .list_view import ListView
from .queue_view import QueueView


if TYPE_CHECKING:
    from contextlib import AbstractContextManager

    from redwood.storage import (
        StorageContextType,
    )


__all__ = [
    "Tree",
]


class Tree(BaseTree):
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

    # =========================================================================
    # CONVENIENCE METHODS FOR BUILT-IN VIEWS
    # =========================================================================

    def with_dict_view(self, *, snapshot: bool = False) -> AbstractContextManager[DictView[Self]]:
        """Access container as dictionary view with automatic transaction or snapshot management.

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
            tree=self,
        )

    def with_list_view(self, *, snapshot: bool = False) -> AbstractContextManager[ListView[Self]]:
        """Access container as list view with automatic transaction or snapshot management.

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
            tree=self,
        )

    def with_queue_view(self, *, snapshot: bool = False) -> AbstractContextManager[QueueView[Self]]:
        """Access container as queue view with automatic transaction or snapshot management.

        Returns a context manager that yields a QueueView with transaction or snapshot context.
        If path doesn't exist, creates a new queue container.

        Args:
            snapshot: If True, creates a read-only snapshot view instead of a transaction view

        Returns:
            Context manager yielding QueueView with transaction or snapshot

        Example:
            ```python
            # Automatic transaction - recommended for mutations
            with tree.at("work_queue").with_queue_view() as work_queue:
                work_queue.enqueue("Task 1")
                work_queue.enqueue("Task 2")
                next_task = work_queue.dequeue()
            # Transaction automatically committed on success

            # Read-only snapshot - recommended for consistent reads
            with tree.at("work_queue").with_queue_view(snapshot=True) as work_queue:
                is_empty = work_queue.is_empty()
                queue_size = work_queue.size()
                # Read-only operations only
            # Snapshot automatically cleaned up
            ```
        """
        return create_view_context_manager(
            QueueView,
            snapshot=snapshot,
            backend=self.backend,
            path=self.path,
            ctx=self.ctx,
            tree=self,
        )

    def dict_view(self, *, ctx: StorageContextType | None = None) -> DictView[Self]:
        """Access container as dictionary view with manual context management.

        Returns a DictView object directly. No automatic context handling.
        If path doesn't exist, creates a new mapping container when accessed.

        Args:
            ctx: Optional context (defaults to current context)

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
                users = tree.at("users").dict_view(ctx=ctx)
                users.set("alice", {"email": "alice@example.com"})
                ctx.commit()
            except Exception:
                ctx.rollback()
                raise

            # Use existing transaction from context
            with tree.with_dict_view() as root_dict:
                # This inherits the transaction from the context
                users = tree.at("users").dict_view()
                users.set("bob", {"email": "bob@example.com"})
            ```
        """
        return DictView(backend=self.backend, path=self.path, ctx=ctx or self.ctx, tree=self)

    def list_view(self, *, ctx: StorageContextType | None = None) -> ListView[Self]:
        """Access container as list view with manual context management.

        Returns a ListView object directly. No automatic context handling.
        If path doesn't exist, creates a new sequence container when accessed.

        Args:
            ctx: Optional context (defaults to current context)

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
                ctx.commit()
            except Exception:
                ctx.rollback()
                raise

            # Accessing nested containers
            tasks = tree.at("tasks").list_view()
            if tasks.length() > 0:
                first_task_dict = tasks.dict_view(0)  # Access first item as dict
                first_task_dict.set("completed", True)
            ```
        """
        return ListView(backend=self.backend, path=self.path, ctx=ctx or self.ctx, tree=self)

    def queue_view(self, *, ctx: StorageContextType | None = None) -> QueueView[Self]:
        """Access container as queue view with manual context management.

        Returns a QueueView object directly. No automatic context handling.
        If path doesn't exist, creates a new queue container when accessed.

        Args:
            ctx: Optional context (defaults to current context)

        Returns:
            QueueView: Queue view for the container

        Example:
            ```python
            # Direct usage - good for reads
            work_queue = tree.at("work_queue").queue_view()
            is_empty = work_queue.is_empty()
            queue_size = work_queue.size()

            # Manual transaction management
            tx = tree.begin_transaction()
            try:
                work_queue = tree.at("work_queue").queue_view(ctx=tx)
                work_queue.enqueue("New task")
                ctx.commit()
            except Exception:
                ctx.rollback()
                raise
            ```
        """
        return QueueView(backend=self.backend, path=self.path, ctx=ctx or self.ctx, tree=self)
