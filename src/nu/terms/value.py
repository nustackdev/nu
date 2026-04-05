"""Value - irreducible atom.

Nu                          - the primitive
└── RValue                  - evaluable expression
    └── Value               - literal data (leaf Nu)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .nu import RValue
from .type_vars import T_co


if TYPE_CHECKING:
    from ..context import Context


__all__ = [
    "Value",
]


class Value(RValue[T_co]):
    """Irreducible atom. Holds a literal value.

    Value is a leaf Nu with no children. It stores a Python object
    directly and returns it on execute().

    Usage:
        v = Value(42)
        result = await v.execute(ctx)  # → 42
    """

    _value: object  # T

    def __init__(self, value: T_co) -> None:  # type: ignore[misc]
        """Initialize with a literal value (not a Nu)."""
        super().__init__()  # no children
        self._value = value

    async def execute(self, ctx: Context) -> T_co:
        """Return the literal value."""
        return self._value  # type: ignore[return-value]

    @property
    def is_self_pure(self) -> bool:
        """Values never have side effects."""
        return True

    def __repr__(self) -> str:
        return f"Value({self._value!r})"
