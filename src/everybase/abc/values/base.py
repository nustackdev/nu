"""ValueBase — Python memory storage substrate for values.

Provides:
- source: Public property — the source (Term child or literal)
- _literal: Stores non-Term sources (_NO_LITERAL when Term-backed)
- execute(): Evaluates source and returns value
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from everybase.core import Arg, Sentinel, Term, Value


_NO_LITERAL = object()  # sentinel: "this Value is Term-backed, no literal"

if TYPE_CHECKING:
    from everybase.core import Context


__all__ = [
    "ValueBase",
]


class ValueBase[T](Value[T | Sentinel]):
    """Value substrate base for Python runtime memory.

    Provides:
    - source: Public property — the source (Term child or literal)
    - _literal: Stores non-Term sources (_NO_LITERAL when Term-backed)
    - execute(): Evaluates source and returns value

    Usage:
        class IntValue(ValueBase[int], IntType):
            pass

    For Term sources, the Term is stored as children[0]. with_children()
    automatically updates it — no manual sync needed.
    For literal sources, the value is stored in _literal.
    """

    _literal: object  # T or _NO_LITERAL

    def __init__(self, source: Arg[T]) -> None:
        """Initialize with source.

        Args:
            source: Either a Term (computation) or literal value
        """
        if isinstance(source, Term):
            super().__init__(source)
            self._literal = _NO_LITERAL
        else:
            super().__init__()
            self._literal = source

    @property
    def source(self) -> Arg[T]:
        """The source of this value — either a Term child or a literal."""
        if self._literal is not _NO_LITERAL:
            return self._literal  # type: ignore[return-value]
        return self.children[0] if self.children else _NO_LITERAL  # type: ignore[return-value]

    async def execute(self, ctx: Context) -> T | Sentinel:
        """Get the value by evaluating the source.

        - Term source: execute children[0]
        - Literal source: return directly

        Args:
            ctx: Execution context

        Returns:
            The value, or Sentinel if computation returns one
        """
        if self._literal is not _NO_LITERAL:
            return self._literal  # type: ignore[return-value]
        return await self.children[0].execute(ctx)
