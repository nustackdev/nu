"""Literal RValue implementations.

This module provides literal value wrappers for Python primitives and collections.
These wrap fixed, known values that are available at definition time.

Literal Values (this module):
- IntLiteral, FloatLiteral, BoolLiteral, StrLiteral, BytesLiteral, NoneLiteral
- ListLiteral, DictLiteral, TupleLiteral, SetLiteral, FrozenSetLiteral

Computed Values (primitive_values.py, collection_values.py):
- IntValue, FloatValue, BoolValue, StrValue, etc.
- Wrap Operations/RValues that compute results

Usage:
    >>> from everyshape.shape.values.literals import IntLiteral
    >>> lit = IntLiteral(42)  # Fixed value
    >>> lit.execute(ctx)  # Returns 42
"""

from __future__ import annotations

from ..term import LiteralValue


__all__ = [  # noqa: RUF022
    # Primitive literals
    "IntLiteral",
    "FloatLiteral",
    "BoolLiteral",
    "StrLiteral",
    "BytesLiteral",
    "NoneLiteral",
    # Collection literals
    "ListLiteral",
    "DictLiteral",
    "TupleLiteral",
    "SetLiteral",
    "FrozenSetLiteral",
]


# =============================================================================
# PRIMITIVE LITERALS
# =============================================================================


class IntLiteral(LiteralValue[int]):
    """Literal integer value."""

    pass


class FloatLiteral(LiteralValue[float]):
    """Literal float value."""

    pass


class BoolLiteral(LiteralValue[bool]):
    """Literal boolean value."""

    pass


class StrLiteral(LiteralValue[str]):
    """Literal string value."""

    pass


class BytesLiteral(LiteralValue[bytes]):
    """Literal bytes value."""

    pass


class NoneLiteral(LiteralValue[None]):
    """Literal None value."""

    def __init__(self) -> None:
        """Initialize None literal."""
        super().__init__(None)


# =============================================================================
# COLLECTION LITERALS
# =============================================================================


class ListLiteral[T](LiteralValue[list[T]]):
    """Literal list value."""

    pass


class DictLiteral[K, V](LiteralValue[dict[K, V]]):
    """Literal dict value."""

    pass


class TupleLiteral[*Ts](LiteralValue[tuple[*Ts]]):
    """Literal tuple value."""

    pass


class SetLiteral[T](LiteralValue[set[T]]):
    """Literal set value."""

    pass


class FrozenSetLiteral[T](LiteralValue[frozenset[T]]):
    """Literal frozenset value."""

    pass
