"""Literal - irreducible atom.

Nu                          - the primitive
└── RValue                  - evaluable expression
    └── Literal             - literal data (leaf Nu)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .interaction import Interaction
from .type_vars import T_co


if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from ..context import Context


__all__ = [
    "Literal",
]


class Literal(Interaction[T_co]):
    """Irreducible atom. Holds a literal value.

    Literal is a leaf Nu with no children. It stores a Python object
    directly and yields it on open().

    Usage:
        v = Literal(42)
        # open yields 42 once
    """

    _value: object  # T

    def __init__(self, value: T_co) -> None:  # type: ignore[misc]
        """Initialize with a literal value (not a Nu)."""
        super().__init__()  # no children
        self._value = value

    async def open(self, ctx: Context) -> AsyncGenerator[T_co, None]:
        """Yield the literal value once."""
        yield self._value  # type: ignore[misc]

    @property
    def is_self_pure(self) -> bool:
        """Literals never have side effects."""
        return True

    def __repr__(self) -> str:
        return f"Literal({self._value!r})"
