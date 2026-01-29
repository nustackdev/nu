"""Arg type aliases — accept both literals and Term expressions.

Pattern: ``T | Term[T] | Term[T | Sentinel]``

Usage::

    class MyRef:
        def set(self, value: IntArg) -> ...:
            ...

    ref.set(42)               # literal
    ref.set(other_ref.get())  # expression
"""

from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from .sentinel import Sentinel
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


# Generic
type Arg[T] = T | Term[T] | Term[T | Sentinel]

# Primitives
type IntArg = int | Term[int] | Term[int | Sentinel]
type FloatArg = float | Term[float] | Term[float | Sentinel]
type StrArg = str | Term[str] | Term[str | Sentinel]
type BoolArg = bool | Term[bool] | Term[bool | Sentinel]
type BytesArg = bytes | Term[bytes] | Term[bytes | Sentinel]
type NoneArg = None | Term[None] | Term[None | Sentinel]

# Collections
type ListArg[V] = list[V] | Term[list[V]] | Term[list[V] | Sentinel]
type DictArg[K, V] = dict[K, V] | Term[dict[K, V]] | Term[dict[K, V] | Sentinel]
type SetArg[T] = set[T] | Term[set[T]] | Term[set[T] | Sentinel]
type FrozenSetArg[T] = frozenset[T] | Term[frozenset[T]] | Term[frozenset[T] | Sentinel]
type TupleArg[*Ts] = tuple[*Ts] | Term[tuple[*Ts]] | Term[tuple[*Ts] | Sentinel]
