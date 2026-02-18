"""Context — type-keyed handle container for execution.

Context is the runtime environment passed to Executable.execute().
It holds resolved handles (connections, transactions, etc.) keyed by type,
optionally discriminated by a scope for multi-store scenarios.

Design:
    - Immutable: with_handle() returns new Context
    - Type-keyed: handles looked up by type, optionally scoped
    - Lazy factories: handles can be created on-demand
    - No Handle base class: any object can be a handle

Scope is any hashable — Shape, Table, tenant ID, etc.
Context doesn't know what a scope *is*, only that it discriminates handles.
Fallback: scoped lookup falls back to unscoped.
"""

from __future__ import annotations

from collections.abc import Hashable
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import Any


__all__ = [
    "Context",
]


type ContextKey = type | tuple[type, Hashable]


class Context:
    """Container of resolved handles. Passed to Executable.execute().

    Immutable — with_handle() returns a new Context with the
    additional/overridden handle.

    Keys can be:
        - type: singleton handle (e.g., NotionClient)
        - (type, scope): scoped handle (e.g., (StorageProtocol, UserShape))

    Scope is any hashable. Context is scope-agnostic — it doesn't
    know about Shape, Table, or any specific taxonomy. Higher layers
    decide what to use as scope.

    Usage:
        # Singleton
        ctx = Context().with_handle(NotionClient, client)
        client = ctx.get(NotionClient)

        # Scoped
        ctx = ctx.with_handle(KVStore, user_store, scope=UserShape)
        store = ctx.get(KVStore, scope=UserShape)

        # Lazy factory
        ctx = ctx.with_factory(Transaction, lambda: store.begin())
        txn = ctx.get(Transaction)  # created on first access
    """

    def __init__(self) -> None:
        """Initialize empty context."""
        self._handles: dict[ContextKey, Any] = {}
        self._factories: dict[ContextKey, Callable[[], Any]] = {}
        self._opened: set[ContextKey] = set()  # track lazily opened handles

    def _copy(self) -> Context:
        """Create a shallow copy."""
        ctx = Context.__new__(Context)
        ctx._handles = dict(self._handles)
        ctx._factories = dict(self._factories)
        ctx._opened = set(self._opened)
        return ctx

    @staticmethod
    def _make_key(handle_type: type, scope: Hashable | None) -> ContextKey:
        """Create lookup key from type and optional scope."""
        return (handle_type, scope) if scope is not None else handle_type

    def get[T](self, handle_type: type[T], scope: Hashable | None = None) -> T:
        """Look up a handle by type, optionally scoped.

        Resolution order:
          1. Exact match (type, scope)
          2. Factory for (type, scope)
          3. Fallback to unscoped type
          4. Factory for unscoped type

        Args:
            handle_type: The type to look up.
            scope: Optional scope discriminator (any hashable).

        Returns:
            The handle instance.

        Raises:
            LookupError: If no handle or factory for this key.
        """
        key = self._make_key(handle_type, scope)

        # Check existing handles
        if key in self._handles:
            return self._handles[key]

        # Try factory (lazy creation)
        if key in self._factories:
            handle = self._factories[key]()
            self._handles[key] = handle
            self._opened.add(key)  # mark as lazily opened
            return handle

        # Fallback: try unscoped lookup when scoped fails
        if scope is not None:
            unscoped_key = handle_type
            if unscoped_key in self._handles:
                return self._handles[unscoped_key]
            if unscoped_key in self._factories:
                handle = self._factories[unscoped_key]()
                self._handles[unscoped_key] = handle
                self._opened.add(unscoped_key)
                return handle

        # Build error message
        if scope is not None:
            scope_name = scope.__name__ if hasattr(scope, "__name__") else str(scope)
            msg = f"No handle for {handle_type.__name__} with scope {scope_name}"
        else:
            msg = f"No handle for {handle_type.__name__}"
        raise LookupError(msg)

    def has(self, handle_type: type, scope: Hashable | None = None) -> bool:
        """Check if a handle or factory is available."""
        key = self._make_key(handle_type, scope)
        return key in self._handles or key in self._factories

    def was_opened(self, handle_type: type, scope: Hashable | None = None) -> bool:
        """Check if a lazy handle was actually opened."""
        key = self._make_key(handle_type, scope)
        return key in self._opened

    def with_handle[T](
        self,
        handle_type: type[T],
        handle: T,
        scope: Hashable | None = None,
    ) -> Context:
        """Create new Context with an additional/overridden handle.

        Args:
            handle_type: Type key for the handle
            handle: The handle instance
            scope: Optional scope discriminator

        Returns:
            New Context with the handle added
        """
        key = self._make_key(handle_type, scope)
        ctx = self._copy()
        ctx._handles[key] = handle
        # Remove any factory for this key (handle takes precedence)
        ctx._factories.pop(key, None)
        return ctx

    def with_factory[T](
        self,
        handle_type: type[T],
        factory: Callable[[], T],
        scope: Hashable | None = None,
    ) -> Context:
        """Create new Context with a lazy handle factory.

        The factory is called on first access to get().
        The result is cached for subsequent calls.

        Args:
            handle_type: Type key for the handle
            factory: Callable that creates the handle
            scope: Optional scope discriminator

        Returns:
            New Context with the factory added
        """
        key = self._make_key(handle_type, scope)
        ctx = self._copy()
        ctx._factories[key] = factory
        return ctx

    def __contains__(self, handle_type: type) -> bool:
        """Check if handle type exists (singleton only)."""
        return self.has(handle_type)

    def __getitem__[T](self, handle_type: type[T]) -> T:
        """Subscript access to singleton handles."""
        return self.get(handle_type)

    def __repr__(self) -> str:
        """String representation."""
        parts = []
        for key in self._handles:
            if isinstance(key, tuple):
                scope_name = key[1].__name__ if hasattr(key[1], "__name__") else str(key[1])
                parts.append(f"{key[0].__name__}@{scope_name}")
            else:
                parts.append(key.__name__)
        for key in self._factories:
            if key not in self._handles:
                if isinstance(key, tuple):
                    scope_name = key[1].__name__ if hasattr(key[1], "__name__") else str(key[1])
                    parts.append(f"{key[0].__name__}@{scope_name}(lazy)")
                else:
                    parts.append(f"{key.__name__}(lazy)")
        return f"Context({', '.join(parts)})"
