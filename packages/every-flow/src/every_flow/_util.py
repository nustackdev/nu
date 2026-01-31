"""Utilities for flow construction."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from everyabc import Executable, Term


if TYPE_CHECKING:
    from everyabc import Context


__all__ = [
    "Const",
]


class Const[T](Term[T]):
    """Literal value wrapped as a Term. Leaf node.

    Allows flows to treat all computation parameters uniformly
    as children in the tree, whether they are Terms or literals.

    Example::

        Const(42).execute(ctx)  # → 42
        Const("hello").execute(ctx)  # → "hello"
    """

    def __init__(self, value: T) -> None:
        """Initialize with a literal value."""
        super().__init__()
        self._value = value

    @property
    def is_self_pure(self) -> bool:
        """Constants are always pure."""
        return True

    async def execute(self, ctx: Context) -> T:
        """Return the literal value."""
        return self._value

    def __repr__(self) -> str:
        """Const(value)."""
        return f"Const({self._value!r})"


def _ensure_term(value: Any) -> Executable:
    """Convert a value to a Term if it isn't one already.

    If value is already an Executable (Term, Flow, Span), return as-is.
    Otherwise wrap in Const.
    """
    if isinstance(value, Executable):
        return value
    return Const(value)
