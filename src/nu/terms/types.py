"""Shared types for the Nu term system.

Merges what used to live in:
  - mode.py       (Mode, sup)
  - sentinel.py   (Sentinel, Empty, Invalid, EMPTY, INVALID, is_*, propagate_special)
  - effect.py     (Direction, TrackedEffect)  - analysis functions live in utils.py
  - arg.py        (IntArg, FloatArg, ..., Arg[T])
  - type_vars.py  (T_co)
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, Flag, auto
from typing import TYPE_CHECKING, TypeGuard, TypeVar


if TYPE_CHECKING:
    from .nu import Nu


__all__ = [
    "EMPTY",
    "INVALID",
    "Arg",
    "BoolArg",
    "BytesArg",
    "DictArg",
    "Direction",
    "Empty",
    "FloatArg",
    "FrozenSetArg",
    "IntArg",
    "Invalid",
    "ListArg",
    "Mode",
    "NoneArg",
    "Sentinel",
    "SetArg",
    "StrArg",
    "T_co",
    "TrackedEffect",
    "TupleArg",
    "is_empty",
    "is_invalid",
    "is_sentinel",
    "propagate_special",
    "sup",
]


# =============================================================================
# TYPE VARS
# =============================================================================

T_co = TypeVar("T_co", covariant=True)


# =============================================================================
# MODE
# =============================================================================


class Mode(str, Enum):
    """Execution mode. SYNC = plain generator; ASYNC = event loop; BOTH = either."""

    SYNC = "sync"
    ASYNC = "async"
    BOTH = "both"


def sup(*modes: Mode) -> Mode:
    """Supremum over modes. ASYNC dominates; SYNC + BOTH = SYNC; all BOTH = BOTH."""
    if not modes:
        return Mode.BOTH
    has_async = any(m is Mode.ASYNC for m in modes)
    has_sync = any(m is Mode.SYNC for m in modes)
    if has_async:
        return Mode.ASYNC
    if has_sync:
        return Mode.SYNC
    return Mode.BOTH


# =============================================================================
# SENTINELS
# =============================================================================


class Sentinel:
    """Base class for special sentinel values."""


class Empty(Sentinel):
    """Value doesn't exist. Distinct from None."""

    def __repr__(self) -> str:
        return "<Empty>"

    def __bool__(self) -> bool:
        return False

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Empty)

    def __hash__(self) -> int:
        return hash(type(self).__name__)


class Invalid(Sentinel):
    """Operation not applicable. Cannot produce a meaningful result."""

    def __repr__(self) -> str:
        return "<Invalid>"

    def __bool__(self) -> bool:
        return False

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Invalid)

    def __hash__(self) -> int:
        return hash(type(self).__name__)


EMPTY: Empty = Empty()
INVALID: Invalid = Invalid()


def is_empty(value: object) -> TypeGuard[Empty]:
    return isinstance(value, Empty)


def is_invalid(value: object) -> TypeGuard[Invalid]:
    return isinstance(value, Invalid)


def is_sentinel(value: object) -> TypeGuard[Sentinel]:
    return isinstance(value, Sentinel)


def propagate_special(*values: object) -> Invalid | Empty | None:
    """Propagate EMPTY / INVALID through computation.

    Returns INVALID if any value is a sentinel, else None (all normal).
    """
    for v in values:
        if isinstance(v, (Invalid, Empty)):
            return INVALID
    return None


# =============================================================================
# EFFECT TAXONOMY (types only; analysis lives in utils.py)
# =============================================================================


class Direction(Flag):
    """Tracked direction of fabric interaction."""

    READ = auto()
    WRITE = auto()


@dataclass(frozen=True)
class TrackedEffect:
    """A single tracked effect: which fabric, which direction."""

    fabric: type
    direction: Direction

    def __repr__(self) -> str:
        return f"TrackedEffect({self.fabric.__name__}, {self.direction.name})"


# =============================================================================
# ARG TYPES
# =============================================================================

type Arg[T] = T | Nu[T] | Nu[T | Sentinel]

type IntArg = int | Nu[int] | Nu[int | Sentinel]
type FloatArg = float | Nu[float] | Nu[float | Sentinel]
type StrArg = str | Nu[str] | Nu[str | Sentinel]
type BoolArg = bool | Nu[bool] | Nu[bool | Sentinel]
type BytesArg = bytes | Nu[bytes] | Nu[bytes | Sentinel]
type NoneArg = None | Nu[None] | Nu[None | Sentinel]

type ListArg[V] = list[V] | Nu[list[V]] | Nu[list[V] | Sentinel]
type DictArg[K, V] = dict[K, V] | Nu[dict[K, V]] | Nu[dict[K, V] | Sentinel]
type SetArg[T] = set[T] | Nu[set[T]] | Nu[set[T] | Sentinel]
type FrozenSetArg[T] = frozenset[T] | Nu[frozenset[T]] | Nu[frozenset[T] | Sentinel]
type TupleArg[*Ts] = tuple[*Ts] | Nu[tuple[*Ts]] | Nu[tuple[*Ts] | Sentinel]
