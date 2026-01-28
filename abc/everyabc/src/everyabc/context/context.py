"""Context — type-keyed handle container for execution.

Context is the runtime environment passed to Term.execute().
It holds resolved handles (connections, transactions, etc.) keyed by type.

Design:
    - Immutable: with_handle() returns new Context
    - Type-keyed: handles looked up by their type
    - No Handle base class: any object can be a handle
"""

from __future__ import annotations


__all__ = [
    "Context",
]


class Context:
    """Container of resolved handles. Passed to Term.execute().

    Immutable — with_handle() returns a new Context with the
    additional/overridden handle.

    Usage in Terms::

        kv = ctx[KVHandle]
        kv = ctx.get(KVHandle)   # same thing

    Example::

        ctx = Context()
        ctx = ctx.with_handle(KVTransaction, txn)
        txn = ctx.get(KVTransaction)
    """

    __slots__ = ("_handles",)

    def __init__(self, handles: dict[type, object] | None = None) -> None:
        """Initialize context with optional handles.

        Args:
            handles: Initial type->handle mapping
        """
        self._handles: dict[type, object] = dict(handles) if handles else {}

    def get[T](self, handle_type: type[T]) -> T:
        """Look up a handle by type.

        Args:
            handle_type: The type to look up.

        Returns:
            The handle instance.

        Raises:
            LookupError: If no handle of this type is available.
        """
        handle = self._handles.get(handle_type)
        if handle is None:
            msg = f"No handle for {handle_type.__name__}"
            raise LookupError(msg)
        return handle  # type: ignore[return-value]

    def has(self, handle_type: type) -> bool:
        """Check if a handle type is available."""
        return handle_type in self._handles

    def with_handle[T](self, handle_type: type[T], handle: T) -> Context:
        """Create new Context with an additional/overridden handle.

        Innermost wins: the new handle shadows any existing one
        of the same type.

        Args:
            handle_type: Type key for the handle
            handle: The handle instance

        Returns:
            New Context with the handle added
        """
        new_handles = dict(self._handles)
        new_handles[handle_type] = handle
        ctx = Context.__new__(Context)
        ctx._handles = new_handles
        return ctx

    def __contains__(self, handle_type: type) -> bool:
        """Check if handle type exists."""
        return handle_type in self._handles

    def __getitem__[T](self, handle_type: type[T]) -> T:
        """Subscript access to handles."""
        return self.get(handle_type)

    def __repr__(self) -> str:
        """String representation."""
        types = ", ".join(t.__name__ for t in self._handles)
        return f"Context({types})"
