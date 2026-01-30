"""Concrete Python memory refs for all types.

Each ref combines PyRefBase (source storage substrate) with its
type-specific RefBase (capability traits from everybase.refs).

Types:
    Primitives: IntRef, FloatRef, BoolRef, StrRef, BytesRef
    Collections: ListRef, DictRef, SetRef, FrozenSetRef, TupleRef
    Special: AnyRef, NoneRef, SentinelRef, EmptyRef, InvalidRef
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from everyabc import EMPTY, INVALID, Empty, Invalid, Sentinel
from everybase.refs import (
    AnyRefBase,
    BoolRefBase,
    BytesRefBase,
    DictRefBase,
    EmptyRefBase,
    FloatRefBase,
    FrozenSetRefBase,
    IntRefBase,
    InvalidRefBase,
    ListRefBase,
    NoneRefBase,
    SentinelRefBase,
    SetRefBase,
    StrRefBase,
    TupleRefBase,
)

from .base import PyRefBase


if TYPE_CHECKING:
    from everyabc import Context


__all__ = [
    "AnyRef",
    "BoolRef",
    "BytesRef",
    "DictRef",
    "EmptyRef",
    "FloatRef",
    "FrozenSetRef",
    "IntRef",
    "InvalidRef",
    "ListRef",
    "NoneRef",
    "SentinelRef",
    "SetRef",
    "StrRef",
    "TupleRef",
]


# =============================================================================
# PRIMITIVES
# =============================================================================


class IntRef(PyRefBase[int], IntRefBase):
    """Concrete integer ref for Python memory storage."""

    pass


class FloatRef(PyRefBase[float], FloatRefBase):
    """Concrete float ref for Python memory storage."""

    pass


class BoolRef(PyRefBase[bool], BoolRefBase):
    """Concrete boolean ref for Python memory storage."""

    pass


class StrRef(PyRefBase[str], StrRefBase):
    """Concrete string ref for Python memory storage."""

    pass


class BytesRef(PyRefBase[bytes], BytesRefBase):
    """Concrete bytes ref for Python memory storage."""

    pass


# =============================================================================
# COLLECTIONS
# =============================================================================


class ListRef[T](PyRefBase[list[T]], ListRefBase[T]):
    """Concrete list ref for Python memory storage."""

    pass


class DictRef[K, V](PyRefBase[dict[K, V]], DictRefBase[K, V]):
    """Concrete dict ref for Python memory storage."""

    pass


class SetRef[T](PyRefBase[set[T]], SetRefBase[T]):
    """Concrete set ref for Python memory storage."""

    pass


class FrozenSetRef[T](PyRefBase[frozenset[T]], FrozenSetRefBase[T]):
    """Concrete frozenset ref for Python memory storage."""

    pass


class TupleRef[*Ts](PyRefBase[tuple[*Ts]], TupleRefBase[*Ts]):
    """Concrete tuple ref for Python memory storage."""

    pass


# =============================================================================
# SPECIAL
# =============================================================================


class AnyRef(PyRefBase[object], AnyRefBase):
    """Concrete any/dynamic ref for Python memory storage."""

    pass


class NoneRef(PyRefBase[None], NoneRefBase):
    """Concrete none ref for Python memory storage."""

    def __init__(self) -> None:
        """Initialize with None as default source."""
        super().__init__(None)

    async def fetch(self, ctx: Context) -> None | Sentinel:
        """Get returns None."""
        return None


class SentinelRef[T](PyRefBase[T], SentinelRefBase):
    """Concrete sentinel ref for Python memory storage."""

    pass


class EmptyRef(PyRefBase[Empty], EmptyRefBase):
    """Concrete empty ref — represents absence of a value."""

    def __init__(self) -> None:
        """Initialize invalid ref."""
        super().__init__(EMPTY)

    async def fetch(self, ctx: Context) -> Sentinel:
        """Get returns EMPTY sentinel."""
        return EMPTY


class InvalidRef(PyRefBase[Invalid], InvalidRefBase):
    """Concrete invalid ref — represents invalid/undefined operations."""

    def __init__(self) -> None:
        """Initialize invalid ref."""
        super().__init__(INVALID)

    async def fetch(self, ctx: Context) -> Sentinel:
        """Get returns INVALID sentinel."""
        return INVALID
