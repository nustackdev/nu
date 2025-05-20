"""
State implementation for the state management system.

This module defines the State class, which is the primary interface for accessing
and manipulating the state tree. It provides methods for navigation, accessing nodes,
checking types, and creating views.
"""

from __future__ import annotations

from typing import Optional, TypeVar

from loomi.interfaces.state.observer import SyncSubscriptionProtocol

from .._core.container import ContainerNode
from .._core.path import StatePath
from .._state.backend import ObservableKVBackend, ObservableKVTransaction
from .._types import CommonContainerProtocols, ContainerProtocol, PathComponent, StateCallbackFn
from .._utils import TransactionContext
from .._views.dict_view import DictView
from .._views.flat_view import FlatView
from .._views.list_view import ListView
from .._views.set_view import SetView

ViewT = TypeVar("ViewT")

__all__ = ["State"]


class State:
    """
    Primary interface for accessing the state tree.

    State provides methods for navigating the tree, querying and manipulating nodes,
    and creating appropriate views for container nodes. It follows a filesystem-like
    mental model, where containers are like directories and primitives are like files.

    Example:
        ```python
        state = state_service.state

        # Navigation
        users = state.at("users")
        alice = users.at("alice")

        # Checking paths
        if alice.exists():
            print(f"User type: {alice.type()}")

        # Getting and setting values
        name = alice.at("name").get()
        alice.at("email").set("alice@example.com")

        # Using views
        profile = alice.at("profile").dict_view()
        profile.set("location", "San Francisco")

        skills = profile.list_view("skills")
        skills.append("Python")
        ```
    """

    def __init__(
        self,
        backend: ObservableKVBackend,
        path: Optional[StatePath] = None,
        *,
        tx: Optional[ObservableKVTransaction] = None,
    ) -> None:
        """
        Initialize a State instance.

        Args:
            backend: The backend storage interface
            path: The current path location (default: root)
            tx: Optional transaction for atomic operations
        """
        self._backend = backend
        self._path = path if path is not None else StatePath()
        self._tx = tx

    @property
    def path(self) -> StatePath:
        """
        Get the current path location.

        Returns:
            StatePath: Current path
        """
        return self._path

    def at(self, *paths: PathComponent, tx: ObservableKVTransaction | None = None) -> State:
        """
        Navigate to a path (relative to current path).

        This creates a new State instance pointing to the specified path.

        Args:
            *paths: Path components to navigate to

        Returns:
            State: New State for the specified path

        Example:
            ```python
            user = state.at("users", "alice")
            email = state.at("users", "alice", "email")
            ```
        """
        new_path = self._path.join(*paths)
        return State(self._backend, new_path, tx=tx or self._tx)

    @property
    def parent(self) -> State:
        """
        Navigate to parent path.

        Returns:
            State: State for the parent path, or self if already at root

        Example:
            ```python
            user = state.at("users", "alice")
            users = user.parent
            ```
        """
        parent_path = self._path.parent()
        if parent_path is None:
            # Already at root
            return self
        return State(self._backend, parent_path, tx=self._tx)

    @property
    def root(self) -> State:
        """
        Navigate to root path.

        Returns:
            State: State for the root path

        Example:
            ```python
            root = state.at("deeply", "nested", "path").root
            ```
        """
        return State(self._backend, StatePath(), tx=self._tx)

    def dict_view(self, *, tx: Optional[ObservableKVTransaction] = None) -> DictView:
        """
        Access container as dictionary view.

        If path doesn't exist, creates a new mapping container.
        If path exists but is not a container with MAPPING protocol,
        raises an error.

        Args:
            tx: Optional transaction (defaults to current transaction)

        Returns:
            DictView: Dictionary view for the container

        Raises:
            IncompatibleViewError: If container doesn't support MAPPING protocol

        Example:
            ```python
            users = state.at("users").dict_view()
            users.set("alice", {"email": "alice@example.com"})
            ```
        """
        container = ContainerNode(
            self._backend,
            self._path,
            CommonContainerProtocols.DICT,
            tx=tx or self._tx,
        )

        return DictView(container, tx=tx or self._tx)

    def list_view(self, *, tx: Optional[ObservableKVTransaction] = None) -> ListView:
        """
        Access container as list view.

        If path doesn't exist, creates a new sequence container.
        If path exists but is not a container with SEQUENCE protocol,
        raises an error.

        Args:
            tx: Optional transaction (defaults to current transaction)

        Returns:
            ListView: List view for the container

        Raises:
            IncompatibleViewError: If container doesn't support SEQUENCE protocol

        Example:
            ```python
            tasks = state.at("tasks").list_view()
            tasks.append("Buy groceries")
            ```
        """
        container = ContainerNode(
            self._backend,
            self._path,
            CommonContainerProtocols.LIST,
            tx=tx or self._tx,
        )

        return ListView(container, tx=tx or self._tx)

    def set_view(self, *, tx: Optional[ObservableKVTransaction] = None) -> SetView:
        """
        Access container as set view.

        If path doesn't exist, creates a new set container.
        If path exists but is not a container with SET protocol,
        raises an error.

        Args:
            tx: Optional transaction (defaults to current transaction)

        Returns:
            SetView: Set view for the container

        Raises:
            IncompatibleViewError: If container doesn't support SET protocol

        Example:
            ```python
            tags = state.at("tags").set_view()
            tags.add("important")
            ```
        """
        container = ContainerNode(
            self._backend,
            self._path,
            CommonContainerProtocols.SET,
            tx=tx or self._tx,
        )

        return SetView(container, tx=tx or self._tx)

    def flat_view(self, *, tx: Optional[ObservableKVTransaction] = None) -> FlatView:
        """
        Access container as flat view.

        If path doesn't exist, creates a new flat mapping container.
        If path exists but is not a container with MAPPING and FLAT protocols,
        raises an error.

        Args:
            tx: Optional transaction (defaults to current transaction)

        Returns:
            FlatView: Flat view for the container

        Raises:
            IncompatibleViewError: If container doesn't support required protocols

        Example:
            ```python
            config = state.at("config").flat_view()
            config.set("theme", "dark")
            ```
        """
        container = ContainerNode(
            self._backend,
            self._path,
            CommonContainerProtocols.FLAT_DICT,
            tx=tx or self._tx,
        )

        return FlatView(container, tx=tx or self._tx)

    def view(
        self, view_class: type[ViewT], *, tx: Optional[ObservableKVTransaction] = None
    ) -> ViewT:
        """
        Access container via custom view class.

        If path doesn't exist, creates a new container with protocols
        required by the view class.
        If path exists but doesn't support required protocols, raises an error.

        Args:
            view_class: View class to use
            tx: Optional transaction (defaults to current transaction)

        Returns:
            ViewT: Instance of the specified view class

        Raises:
            IncompatibleViewError: If container doesn't support required protocols

        Example:
            ```python
            custom_view = state.at("custom").view(CustomView)
            ```
        """
        tx or self._tx

        # Get required protocols from view class
        required_protocols = getattr(
            view_class, "required_protocols", lambda: ContainerProtocol.CONTAINER
        )()

        container = ContainerNode(
            self._backend,
            self._path,
            required_protocols,
            tx=tx or self._tx,
        )

        return view_class(container, tx=tx or self._tx)

    def begin_transaction(self) -> ObservableKVTransaction:
        """
        Start a new transaction.

        Returns:
            ObservableKVTransaction: New transaction

        Example:
            ```python
            tx = state.begin_transaction()
            try:
                # Perform operations with tx
                state.at("users").dict_view(tx=tx).set("alice", {"name": "Alice"})
                tx.commit()
            except Exception:
                tx.rollback()
                raise
            ```
        """
        return self._backend.begin_transaction()

    def transaction(self) -> TransactionContext:
        """
        Get a transaction context manager.

        Returns:
            TransactionContext: Transaction context manager

        Example:
            ```python
            with state.transaction() as tx:
                # Perform operations with tx
                state.at("users").dict_view(tx=tx).set("alice", {"name": "Alice"})
                # Auto-commits on success, auto-rollbacks on exception
            ```
        """
        return TransactionContext(self._backend)

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
            def on_change(path):
                print(f"Path {path} changed")

            sub = state.at("users").subscribe(on_change)
            # Later, unsubscribe
            sub.unsubscribe()
            ```
        """
        return self._backend.subscribe(self._path.to_tuple(), callback, depth)
