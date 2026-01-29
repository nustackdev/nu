"""Var -- mutable in-memory variable."""

from __future__ import annotations

from typing import TYPE_CHECKING

from everyabc import EMPTY, Ref


if TYPE_CHECKING:
    from everyabc import Context, Sentinel


__all__ = [
    "Var",
]


class Var[T](Ref[T]):
    """Mutable in-memory variable extending Ref[T].

    The default communication primitive between flows.
    Readable as a Term (via fetch/execute), writable via set().

    Example::

        i = Var(0)
        i.set(42)
        i.get()           # → 42
        i.execute(ctx)    # → 42  (Term interface)
        i.fetch(ctx)      # → 42  (Ref interface)
    """

    def __init__(self, value: T | Sentinel = EMPTY) -> None:
        """Initialize with optional value (defaults to EMPTY)."""
        super().__init__()
        self._value: T | Sentinel = value

    def resolve(self, ctx: Context) -> object:
        """Return identity of this variable."""
        return id(self)

    def fetch(self, ctx: Context) -> T | Sentinel:
        """Return current value."""
        return self._value

    def set(self, value: T) -> None:
        """Set value directly. No context needed for in-memory."""
        self._value = value

    def get(self) -> T | Sentinel:
        """Get value directly. No context needed for in-memory."""
        return self._value

    def __repr__(self) -> str:
        """Var(value)."""
        return f"Var({self._value!r})"
