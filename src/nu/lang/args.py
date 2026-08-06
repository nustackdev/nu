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

from typing import TYPE_CHECKING, TypeAlias, TypeVar

from typing_extensions import TypeAliasType, TypeVarTuple


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


_T = TypeVar("_T")
_K = TypeVar("_K")
_V = TypeVar("_V")
_Ts = TypeVarTuple("_Ts")


Arg = TypeAliasType("Arg", "_T | Nu[_T] | Any | Sentinel", type_params=(_T,))

IntArg: TypeAlias = "int | Nu[int] | Any | Sentinel"
FloatArg: TypeAlias = "float | Nu[float] | Any | Sentinel"
StrArg: TypeAlias = "str | Nu[str] | Any | Sentinel"
BoolArg: TypeAlias = "bool | Nu[bool] | Any | Sentinel"
BytesArg: TypeAlias = "bytes | Nu[bytes] | Any | Sentinel"
NoneArg: TypeAlias = "None | Nu[None] | Any | Sentinel"

ListArg = TypeAliasType("ListArg", "list[_V] | Nu[list[_V]] | Any | Sentinel", type_params=(_V,))
DictArg = TypeAliasType(
    "DictArg", "dict[_K, _V] | Nu[dict[_K, _V]] | Any | Sentinel", type_params=(_K, _V)
)
SetArg = TypeAliasType("SetArg", "set[_T] | Nu[set[_T]] | Any | Sentinel", type_params=(_T,))
FrozenSetArg = TypeAliasType(
    "FrozenSetArg", "frozenset[_T] | Nu[frozenset[_T]] | Any | Sentinel", type_params=(_T,)
)
TupleArg = TypeAliasType(
    "TupleArg", "tuple[*_Ts] | Nu[tuple[*_Ts]] | Any | Sentinel", type_params=(_Ts,)
)
