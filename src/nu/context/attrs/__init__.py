"""The attrs axis of the Context fabric: name-keyed store for short-lived data.

``ctx.attrs`` is a flat, name-keyed dict for loop counters, accumulators,
markers, and other short-lived primitives. ``AttrRef`` names a slot; the write
ops (``SetCmd`` / ``Delete``) and existence query
(``AttrExists``) are the interactions.
"""

from __future__ import annotations

from .interactions import AttrExists, Delete, Let, SetCmd
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
    "AttrExists",
    "AttrRef",
    "BoolAttrRef",
    "BytesAttrRef",
    "Delete",
    "DictAttrRef",
    "FloatAttrRef",
    "FrozenSetAttrRef",
    "IntAttrRef",
    "Let",
    "ListAttrRef",
    "NoneAttrRef",
    "SetAttrRef",
    "SetCmd",
    "StrAttrRef",
    "TupleAttrRef",
]
