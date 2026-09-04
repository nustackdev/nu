"""Cardinality attribute: how a node yields a result.

A node yields one value, a stream, nothing, or whatever its body yields. The
declared ``cardinality`` fixes that per sort; the synthesized
``child_cardinality`` resolves it, forwarding a Span's body cardinality through
the transparent wrapper so a parent slot-fits the Span by what its body yields.
"""

from __future__ import annotations

import sys as _sys


if _sys.version_info >= (3, 11):
    from enum import StrEnum
else:
    from enum import Enum as _Enum

    class StrEnum(str, _Enum):
        """Backport of enum.StrEnum for Python 3.10."""

        def __new__(cls, value: str) -> StrEnum:
            member = str.__new__(cls, value)
            member._value_ = value
            return member

        def __str__(self) -> str:
            return str.__str__(self)


from typing import TYPE_CHECKING

from nu.engine import Attribute, Synthesized

from .names import Attr


if TYPE_CHECKING:
    from nu.engine import Path, Program

__all__ = ["ATTRIBUTES", "Cardinality"]


class Cardinality(StrEnum):
    """How a node yields: one value, a stream, nothing, or its body's shape."""

    SCALAR = "scalar"
    STREAM = "stream"
    VOID = "void"
    TRANSPARENT = "transparent"


def _own_cardinality(program: Program, path: Path) -> Cardinality:
    """A node's cardinality as its sort declares it, before Span resolution.

    Dyn is special: its declared cardinality is SCALAR, but if the term carries
    a promise with a cardinality field, that promise pins the value the parent
    slot-fits against. Runtime dispatch then checks the inner tree against the
    same promise.
    """
    from .sort import Sort

    sort = program.attr(path, Attr.SORT)
    if sort == Sort.DYNAMIC:
        nid = program.id_of[path]
        promise = program.terms[nid]._payload.get("dyn_promise") or {}
        pinned = promise.get("cardinality")
        if pinned is not None:
            return pinned
        return Cardinality.SCALAR
    return program.attr(path, Attr.CARDINALITY)


def _resolve_cardinality(own: Cardinality, children: list[Cardinality]) -> Cardinality:
    """Resolve cardinality: a Span (declared TRANSPARENT) takes its body's; else fixed."""
    if own is not Cardinality.TRANSPARENT:
        return own
    return children[0] if children else Cardinality.VOID


ATTRIBUTES: tuple[Attribute, ...] = (
    Synthesized(
        name=Attr.CHILD_CARDINALITY,
        base=_own_cardinality,
        combine=_resolve_cardinality,
        reads=(Attr.CARDINALITY,),
    ),
)
