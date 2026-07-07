"""The attrs axis of the Context fabric: name-keyed store for short-lived data.

``ctx.attrs`` is a flat, name-keyed dict for loop counters, accumulators,
markers, and other short-lived primitives. ``AttrRef`` names a slot; the write
ops (``SetCommand`` / ``DeleteCommand``) and existence query
(``AttrExistsQuery``) are the interactions.
"""

from __future__ import annotations

from .interactions import AttrExistsQuery, DeleteCommand, SetCommand
from .refs import (
    AnyAttrRef,
    AttrRef,
    BoolAttrRef,
    BytesAttrRef,
    DictAttrRef,
    FloatAttrRef,
    FrozenSetAttrRef,
    IntAttrRef,
    ListAttrRef,
    NoneAttrRef,
    SetAttrRef,
    StrAttrRef,
    TupleAttrRef,
)


__all__ = [
    "AnyAttrRef",
    "AttrExistsQuery",
    "AttrRef",
    "BoolAttrRef",
    "BytesAttrRef",
    "DeleteCommand",
    "DictAttrRef",
    "FloatAttrRef",
    "FrozenSetAttrRef",
    "IntAttrRef",
    "ListAttrRef",
    "NoneAttrRef",
    "SetAttrRef",
    "SetCommand",
    "StrAttrRef",
    "TupleAttrRef",
]
