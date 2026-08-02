"""Argument type aliases for Nu kind class signatures.

A kind that takes a python ``int`` (or a Nu that yields one) declares
its slot type as ``IntArg`` rather than spelling ``int | Nu | Sentinel``
each time. The aliases keep concrete kind signatures short and readable
while still admitting the full algebraic surface (a raw python value, a
Nu sub-tree producing one, or a propagating sentinel).

Each specialized alias also admits ``Any`` explicitly: the honest
terminal is consumable everywhere. This is redundant with the ``TypedNu
[Any]`` variance trick (``Nu[Any]`` already substitutes for ``Nu[int]``
etc.), but stating it in the alias makes the surface readable in code -
you can see at a glance that ``IntArg`` welcomes a dynamic value.

``Arg[T]`` is the generic form. The specialized aliases (``IntArg``,
``StrArg``, ...) cover the common scalar and collection cases.

Import note: ``Any`` lives in ``nu.forms`` which imports from
``nu.lang``, so a runtime import here would cycle. PEP 695 ``type`` aliases
evaluate their RHS lazily (``TypeAliasType.__value__`` is only touched by
mypy or explicit introspection), so a ``TYPE_CHECKING``-only import is
sufficient: mypy sees the name, runtime never does.
"""

from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from nu.forms.primitives.any_ import Any

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


type Arg[T] = T | Nu[T] | Any | Sentinel

type IntArg = int | Nu[int] | Any | Sentinel
type FloatArg = float | Nu[float] | Any | Sentinel
type StrArg = str | Nu[str] | Any | Sentinel
type BoolArg = bool | Nu[bool] | Any | Sentinel
type BytesArg = bytes | Nu[bytes] | Any | Sentinel
type NoneArg = None | Nu[None] | Any | Sentinel

type ListArg[V] = list[V] | Nu[list[V]] | Any | Sentinel
type DictArg[K, V] = dict[K, V] | Nu[dict[K, V]] | Any | Sentinel
type SetArg[T] = set[T] | Nu[set[T]] | Any | Sentinel
type FrozenSetArg[T] = frozenset[T] | Nu[frozenset[T]] | Any | Sentinel
type TupleArg[*Ts] = tuple[*Ts] | Nu[tuple[*Ts]] | Any | Sentinel
