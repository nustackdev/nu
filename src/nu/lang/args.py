"""Argument type aliases for Nu kind class signatures.

A kind that takes a python ``int`` -- or a Nu that yields one -- declares
its slot type as ``IntArg`` rather than spelling ``int | Nu | Sentinel``
each time. The aliases keep concrete kind signatures short and readable
while still admitting the full algebraic surface (a raw python value, a
Nu sub-tree producing one, or a propagating sentinel).

``Arg[T]`` is the generic form. The specialized aliases (``IntArg``,
``StrArg``, ...) cover the common scalar and collection cases.
"""

from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from .nu import Nu
    from .sentinels import Sentinel


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


type Arg[T] = T | Nu[T] | Sentinel

type IntArg = int | Nu[int] | Sentinel
type FloatArg = float | Nu[float] | Sentinel
type StrArg = str | Nu[str] | Sentinel
type BoolArg = bool | Nu[bool] | Sentinel
type BytesArg = bytes | Nu[bytes] | Sentinel
type NoneArg = None | Nu[None] | Sentinel

type ListArg[V] = list[V] | Nu[list[V]] | Sentinel
type DictArg[K, V] = dict[K, V] | Nu[dict[K, V]] | Sentinel
type SetArg[T] = set[T] | Nu[set[T]] | Sentinel
type FrozenSetArg[T] = frozenset[T] | Nu[frozenset[T]] | Sentinel
type TupleArg[*Ts] = tuple[*Ts] | Nu[tuple[*Ts]] | Sentinel
