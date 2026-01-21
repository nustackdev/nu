"""Python memory ref base with source storage.

PyRefBase provides source storage and get() implementation for Python memory refs.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from every import Sentinel, Term


if TYPE_CHECKING:
    from every import Context


__all__ = [
    "PyRefBase",
]


class PyRefBase[T]:
    """Mixin providing source storage for Python memory refs.

    Provides:
    - _source: Storage for literal value or Term computation
    - get(): Evaluates source and returns value

    Usage:
        class IntRef(PyRefBase[int], IntRefBase):
            pass

    The get() implementation evaluates the source:
    - If source is a Term, executes it
    - Otherwise returns the literal value
    """

    _source: Term | T

    def __init__(self, source: Term | T) -> None:
        """Initialize ref with source.

        Args:
            source: Either a Term (computation) or literal value
        """
        super().__init__(parent_ref=None, owner_shape=None)
        self._source = source

    @property
    def source(self) -> Term | T:
        """Get the underlying source."""
        return self._source

    @property
    def is_pure(self) -> bool:
        """Check if this ref is pure (no side effects)."""
        if isinstance(self._source, Term):
            return self._source.is_pure
        return True

    def get(self, ctx: Context) -> T | Sentinel:
        """Get the value by evaluating the source.

        For Python memory refs:
        - Term source: execute the term
        - Literal source: return directly
        """
        if isinstance(self._source, Term):
            return self._source.execute(ctx)
        return self._source

    def resolve(self, ctx: Context) -> object:
        """Resolve to concrete path."""
        return ((self.__class__.__name__, type(self._source)),)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self._source!r})"
