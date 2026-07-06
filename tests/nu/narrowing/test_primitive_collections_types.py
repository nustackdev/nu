"""Task-119 typing tests: primitive-blob collections.

``Primitive*Ref[T]`` stores the whole container as one atomic blob. At the
outer level the ref itself is fully typed. Subscript into it currently
degrades to ``AnyForm`` because ``ListForm.__getitem__`` / ``DictForm``
etc. don't propagate the elem type - that is the Phase 3 wrap-unification
target. Tests below encode BOTH the current state (AnyForm) and the intent
(fixmes) so Phase 3 can flip them.
"""

from __future__ import annotations

from typing import assert_type

import nu
from nu.forms import AnyForm
from nu.virtuals.refs import (
    PrimitiveDictRef,
    PrimitiveFrozenSetRef,
    PrimitiveListRef,
    PrimitiveSetRef,
    PrimitiveTupleRef,
)


# --- Shapes ------------------------------------------------------------


class Blob(nu.Shape):
    tags:      PrimitiveListRef[str]
    scores:    PrimitiveListRef[int]
    meta:      PrimitiveDictRef[str, int]
    labels:    PrimitiveSetRef[str]
    frozen:    PrimitiveFrozenSetRef[int]
    raw_tuple: PrimitiveTupleRef


# --- Whole-container access (outer ref carries its generic params) ----


assert_type(Blob.tags,      PrimitiveListRef[str])
assert_type(Blob.scores,    PrimitiveListRef[int])
assert_type(Blob.meta,      PrimitiveDictRef[str, int])
assert_type(Blob.labels,    PrimitiveSetRef[str])
assert_type(Blob.frozen,    PrimitiveFrozenSetRef[int])
assert_type(Blob.raw_tuple, PrimitiveTupleRef)


# --- Subscript currently yields AnyForm (Phase 3 will narrow) ---------


# FIXME(phase-3): flip AnyForm -> StrForm once ListForm.__getitem__
# propagates the elem type param T.
assert_type(Blob.tags[0],       AnyForm)
assert_type(Blob.scores[0],     AnyForm)  # FIXME(phase-3): -> IntForm
assert_type(Blob.meta["k"],     AnyForm)  # FIXME(phase-3): -> IntForm
assert_type(Blob.tags[-1],      AnyForm)


# --- Downstream ops on AnyForm stay AnyForm (absorbing) ---------------


# The absorbing nature of AnyForm means arithmetic + concat keep flowing
# without exploding, they just don't narrow. Phase 3 fixes the source.
assert_type(Blob.scores[0] + 1,          AnyForm)  # FIXME(phase-3): -> IntForm
assert_type(Blob.scores[0] // 2,         AnyForm)  # FIXME(phase-3): -> IntForm
assert_type(Blob.tags[0] + "!",          AnyForm)  # FIXME(phase-3): -> StrForm
assert_type(Blob.meta["k"] * 3,          AnyForm)  # FIXME(phase-3): -> IntForm
assert_type((Blob.scores[0] + 1) * 2,    AnyForm)  # FIXME(phase-3): -> IntForm


# --- Store commands (whole-blob writes) --------------------------------


# store() on a primitive-blob ref takes the whole container. Just verify
# the ref itself is well-typed here; command return types are Phase 3+.
assert_type(Blob.tags,   PrimitiveListRef[str])
assert_type(Blob.scores, PrimitiveListRef[int])
