"""Python memory ref base with source storage.

PyRefBase provides source storage and fetch() implementation for Python memory refs.
This is the substrate base for refs that hold values in Python runtime memory.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from everyabc import Ref, Sentinel, Term


if TYPE_CHECKING:
    from everyabc import Context


__all__ = [
    "PyRefBase",
]


class PyRefBase[T](Ref[T]):
    """Python memory substrate base.

    Provides:
    - _source: Storage for literal value or Term computation
    - fetch(): Evaluates source and returns value
    - resolve(): Returns simple identity

    Usage:
        class IntRef(PyRefBase[int], IntRefBase):
            pass

    The fetch() implementation evaluates the source:
    - If source is a Term, executes it
    - Otherwise returns the literal value
    """

    __slots__ = ("_source",)

    _source: Term[T] | T

    def __init__(self, source: Term[T] | T) -> None:
        """Initialize ref with source.

        Args:
            source: Either a Term (computation) or literal value
        """
        if isinstance(source, Term):
            super().__init__(source)
        else:
            super().__init__()
        self._source = source

    @property
    def source(self) -> Term[T] | T:
        """Get the underlying source."""
        return self._source

    @property
    def is_pure(self) -> bool:
        """Check if this ref is pure (no side effects)."""
        if isinstance(self._source, Term):
            return self._source.is_pure
        return True

    def fetch(self, ctx: Context) -> T | Sentinel:
        """Fetch the value by evaluating the source.

        For Python memory refs:
        - Term source: execute the term
        - Literal source: return directly

        Args:
            ctx: Execution context

        Returns:
            The value, or Sentinel if computation returns one
        """
        if isinstance(self._source, Term):
            return self._source.execute(ctx)
        return self._source

    def resolve(self, ctx: Context) -> tuple[str, type]:
        """Resolve to identity.

        Python memory refs have simple identity - just class and source type.

        Args:
            ctx: Execution context

        Returns:
            Tuple of (class_name, source_type)
        """
        return (self.__class__.__name__, type(self._source))

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self._source!r})"
