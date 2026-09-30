"""The attrs axis of the Context fabric: name-keyed store for short-lived data.

``ctx.attrs`` is a flat, name-keyed dict for loop counters, accumulators,
markers, and other short-lived values. ``Let`` declares a name for a body's
duration; the typed refs (``IntRef``, ``StrRef``, ..., ``ObjectRef``) read it,
``ref.set(v)`` reassigns it (the ``Set`` command) and ``ref.exists()`` asks
whether it is declared (the ``Exists`` query).
"""

from __future__ import annotations

from .interactions import Exists, Let, Set
from .refs import (
    AttrRef,
    BoolRef,
    BytesRef,
    FloatRef,
    FrozenSetRef,
    IntRef,
    ObjectRef,
    StrRef,
    TupleRef,
)


__all__ = [
    "AttrRef",
    "BoolRef",
    "BytesRef",
    "Exists",
    "FloatRef",
    "FrozenSetRef",
    "IntRef",
    "Let",
    "ObjectRef",
    "Set",
    "StrRef",
    "TupleRef",
]
