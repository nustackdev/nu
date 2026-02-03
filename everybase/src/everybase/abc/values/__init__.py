"""Concrete value types for Python memory storage.

ValueBase provides source storage and fetch() for values held in Python runtime
memory. Concrete types combine ValueBase (substrate) with type interfaces (types/).

Types:
    Primitives: IntValue, FloatValue, BoolValue, StrValue, BytesValue
    Collections: ListValue, DictValue, SetValue, FrozenSetValue, TupleValue
    Special: AnyValue, NoneValue, SentinelValue, EmptyValue, InvalidValue
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from everybase.core import EMPTY, INVALID, Arg, Empty, Invalid, Sentinel, Term, Value

from ..types import (
    AnyType,
    BoolType,
    BytesType,
    DictType,
    EmptyType,
    FloatType,
    FrozenSetType,
    IntType,
    InvalidType,
    ListType,
    NoneType,
    SentinelType,
    SetType,
    StrType,
    TupleType,
)


if TYPE_CHECKING:
    from everybase.core import Context


__all__ = [
    "AnyValue",
    "BoolValue",
    "BytesValue",
    "DictValue",
    "EmptyValue",
    "FloatValue",
    "FrozenSetValue",
    "IntValue",
    "InvalidValue",
    "ListValue",
    "NoneValue",
    "SentinelValue",
    "SetValue",
    "StrValue",
    "TupleValue",
    "ValueBase",
]


# =============================================================================
# BASE
# =============================================================================


class ValueBase[T](Value[T | Sentinel]):
    """Value substrate base for Python runtime memory.

    Provides:
    - _source: Storage for literal value or Term computation
    - fetch(): Evaluates source and returns value
    - resolve(): Returns simple identity

    Usage:
        class IntValue(ValueBase[int], IntType):
            pass

    The fetch() implementation evaluates the source:
    - If source is a Term, executes it
    - Otherwise returns the literal value
    """

    def __init__(self, source: Arg[T]) -> None:
        """Initialize with source.

        Args:
            source: Either a Term (computation) or literal value
        """
        if isinstance(source, Term):
            super().__init__(source)
        else:
            super().__init__()

        self._source = source

    async def execute(self, ctx: Context) -> T | Sentinel:
        """Get the value by evaluating the source.

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


# =============================================================================
# PRIMITIVES
# =============================================================================


class IntValue(ValueBase[int], IntType):
    """Concrete integer value for Python memory storage."""

    pass


class FloatValue(ValueBase[float], FloatType):
    """Concrete float value for Python memory storage."""

    pass


class BoolValue(ValueBase[bool], BoolType):
    """Concrete boolean value for Python memory storage."""

    pass


class StrValue(ValueBase[str], StrType):
    """Concrete string value for Python memory storage."""

    pass


class BytesValue(ValueBase[bytes], BytesType):
    """Concrete bytes value for Python memory storage."""

    pass


# =============================================================================
# COLLECTIONS
# =============================================================================


class ListValue[T](ValueBase[list[T]], ListType[T]):
    """Concrete list value for Python memory storage."""

    pass


class DictValue[K, V](ValueBase[dict[K, V]], DictType[K, V]):
    """Concrete dict value for Python memory storage."""

    pass


class SetValue[T](ValueBase[set[T]], SetType[T]):
    """Concrete set value for Python memory storage."""

    pass


class FrozenSetValue[T](ValueBase[frozenset[T]], FrozenSetType[T]):
    """Concrete frozenset value for Python memory storage."""

    pass


class TupleValue[*Ts](ValueBase[tuple[*Ts]], TupleType[*Ts]):
    """Concrete tuple value for Python memory storage."""

    pass


# =============================================================================
# SPECIAL
# =============================================================================


class AnyValue(ValueBase[object], AnyType):
    """Concrete any/dynamic value for Python memory storage."""

    pass


class NoneValue(ValueBase[None], NoneType):
    """Concrete none value for Python memory storage."""

    def __init__(self, source: Arg[None] = None) -> None:
        """Initialize with None as default source."""
        super().__init__(source)

    async def fetch(self, ctx: Context) -> None | Sentinel:
        """Get returns None."""
        return None


class SentinelValue[T](ValueBase[T], SentinelType):
    """Concrete sentinel value for Python memory storage."""

    pass


class EmptyValue(ValueBase[Empty], EmptyType):
    """Concrete empty value — represents absence of a value."""

    def __init__(self) -> None:
        """Initialize empty value."""
        super().__init__(EMPTY)

    async def fetch(self, ctx: Context) -> Sentinel:
        """Get returns EMPTY sentinel."""
        return EMPTY


class InvalidValue(ValueBase[Invalid], InvalidType):
    """Concrete invalid value — represents invalid/undefined operations."""

    def __init__(self) -> None:
        """Initialize invalid value."""
        super().__init__(INVALID)

    async def fetch(self, ctx: Context) -> Sentinel:
        """Get returns INVALID sentinel."""
        return INVALID
