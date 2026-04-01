"""Arg type aliases - accept both literals and Nu expressions.

Pattern: ``T | Nu[T] | Nu[T | Sentinel]``

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
    from .nu import Nu
    from .sentinel import Sentinel


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
type Arg[T] = T | Nu[T] | Nu[T | Sentinel]

# Primitives
type IntArg = int | Nu[int] | Nu[int | Sentinel]
type FloatArg = float | Nu[float] | Nu[float | Sentinel]
type StrArg = str | Nu[str] | Nu[str | Sentinel]
type BoolArg = bool | Nu[bool] | Nu[bool | Sentinel]
type BytesArg = bytes | Nu[bytes] | Nu[bytes | Sentinel]
type NoneArg = None | Nu[None] | Nu[None | Sentinel]

# Collections
type ListArg[V] = list[V] | Nu[list[V]] | Nu[list[V] | Sentinel]
type DictArg[K, V] = dict[K, V] | Nu[dict[K, V]] | Nu[dict[K, V] | Sentinel]
type SetArg[T] = set[T] | Nu[set[T]] | Nu[set[T] | Sentinel]
type FrozenSetArg[T] = frozenset[T] | Nu[frozenset[T]] | Nu[frozenset[T] | Sentinel]
type TupleArg[*Ts] = tuple[*Ts] | Nu[tuple[*Ts]] | Nu[tuple[*Ts] | Sentinel]
