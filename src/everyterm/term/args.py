"""Standardized argument types for Term inputs.

This module provides the Arg type family for uniform method signatures.
Any method accepting user input should use Arg types to accept both
literal values and Term expressions.

Pattern: T | Term[T] | Term[T | Sentinel]
- T: literal value
- Term[T]: typed term producing T
- Term[T | Sentinel]: typed term that may produce sentinel (Empty/Invalid)

Usage:
    from everyshape.term import IntArg, StrArg

    class MyRef:
        def set(self, value: IntArg) -> IntType:
            return IntType(SetCmd(self, literal(value)))

    # Now works with both:
    ref.set(42)              # Literal
    ref.set(other_ref.get()) # Expression

Custom types:
    from everyshape.term import Term, Sentinel

    type MyArg = MyType | Term[MyType] | Term[MyType | Sentinel]
"""

from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from everyterm.typing import Sentinel

    from .term import Term


__all__ = [
    "Arg",
    "BoolArg",
    "BytesArg",
    "DictArg",
    "FloatArg",
    "FrozenSetArg",
    "IntArg",
    "ListArg",
    "NoneArg",
    "SetArg",
    "StrArg",
    "TupleArg",
]


# =============================================================================
# GENERIC ARG TYPE
# =============================================================================

type Arg[T] = T | Term[T] | Term[T | Sentinel]


# =============================================================================
# PRIMITIVE ARG TYPES
# =============================================================================

type IntArg = int | Term[int] | Term[int | Sentinel]
type FloatArg = float | Term[float] | Term[float | Sentinel]
type StrArg = str | Term[str] | Term[str | Sentinel]
type BoolArg = bool | Term[bool] | Term[bool | Sentinel]
type BytesArg = bytes | Term[bytes] | Term[bytes | Sentinel]
type NoneArg = None | Term[None] | Term[None | Sentinel]


# =============================================================================
# COLLECTION ARG TYPES
# =============================================================================

type ListArg[V] = list[V] | Term[list[V]] | Term[list[V] | Sentinel]
type DictArg[K, V] = dict[K, V] | Term[dict[K, V]] | Term[dict[K, V] | Sentinel]
type SetArg[T] = set[T] | Term[set[T]] | Term[set[T] | Sentinel]
type FrozenSetArg[T] = frozenset[T] | Term[frozenset[T]] | Term[frozenset[T] | Sentinel]
type TupleArg[*Ts] = tuple[*Ts] | Term[tuple[*Ts]] | Term[tuple[*Ts] | Sentinel]
