"""Shared types for the new Nu term system.

Effect / Mode / Realization / ExecState enums, T_co, Arg[T] family.

Sentinels live in `sentinels.py`. Composition primitives (Nu protocol)
live in `protocol.py`. Effect machinery lives in `effects.py`.
"""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, TypeVar


if TYPE_CHECKING:
    from .protocol import Nu
    from .sentinels import Sentinel


__all__ = [
    "Arg",
    "BoolArg",
    "BytesArg",
    "DictArg",
    "Effect",
    "ExecState",
    "FloatArg",
    "FrozenSetArg",
    "IntArg",
    "ListArg",
    "Mode",
    "NoneArg",
    "Realization",
    "SetArg",
    "StrArg",
    "T_co",
    "TupleArg",
]


T_co = TypeVar("T_co", covariant=True)


class Effect(Enum):
    """The three directional effects on a (Ref, effect) tuple.

    See projects/nu/model/04-laws/00-effects-algebra.md.
    """

    RESOLVE = "resolve"
    READ = "read"
    WRITE = "write"


class Mode(Enum):
    """Element of a kind's `support` set.

    Replaces the legacy `(own_mode, func_mode)` pair. A kind declares
    `support: frozenset[Mode]` drawn from `{ {SYNC}, {ASYNC}, {SYNC, ASYNC} }`.
    """

    SYNC = "sync"
    ASYNC = "async"


class Realization(Enum):
    """Native realization of a producer kind."""

    SCALAR = "scalar"
    STREAM = "stream"


class ExecState(Enum):
    """Per-node dispatch state - whether the node runs inside an event loop."""

    LOOP = "loop"
    NO_LOOP = "no_loop"


type Arg[T] = T | Nu | Sentinel

type IntArg = int | Nu | Sentinel
type FloatArg = float | Nu | Sentinel
type StrArg = str | Nu | Sentinel
type BoolArg = bool | Nu | Sentinel
type BytesArg = bytes | Nu | Sentinel
type NoneArg = None | Nu | Sentinel

type ListArg[V] = list[V] | Nu | Sentinel
type DictArg[K, V] = dict[K, V] | Nu | Sentinel
type SetArg[T] = set[T] | Nu | Sentinel
type FrozenSetArg[T] = frozenset[T] | Nu | Sentinel
type TupleArg[*Ts] = tuple[*Ts] | Nu | Sentinel
