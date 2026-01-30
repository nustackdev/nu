"""Python memory ref base with source storage.

PyRefBase provides source storage and fetch() implementation for Python memory refs.
This is the substrate base for refs that hold values in Python runtime memory.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from everyabc import Arg, Ref, Sentinel, Term


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

    def __init__(self, source: Arg[T]) -> None:
        """Initialize ref with source.

        Args:
            source: Either a Term (computation) or literal value
        """
        if isinstance(source, Term):
            super().__init__(source)
        else:
            super().__init__()

        self._source = source

    async def fetch(self, ctx: Context) -> T | Sentinel:
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
            return await self._source.execute(ctx)
        return self._source

    async def resolve(self, ctx: Context) -> int:
        """Resolve to identity.

        Python memory refs have simple identity - id(var).

        Args:
            ctx: Execution context

        Returns:
            int
        """
        return id(self._source)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self._source!r})"
