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
from nu.forms import IntForm, StrForm
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


# --- Subscript narrows to the elem type (Phase 3) ---------------------


# Static overloads on ListForm.__getitem__ + runtime dispatch via
# _payload["type_info"] flip these from AnyForm to the elem's Form.
assert_type(Blob.tags[0],       StrForm)
assert_type(Blob.scores[0],     IntForm)
assert_type(Blob.meta["k"],     IntForm)
assert_type(Blob.tags[-1],      StrForm)


# --- Downstream ops preserve the narrowed type ------------------------


# Once subscript narrows correctly, arithmetic + concat flow with the
# right Form all the way through.
assert_type(Blob.scores[0] + 1,          IntForm)
assert_type(Blob.scores[0] // 2,         IntForm)
assert_type(Blob.tags[0] + "!",          StrForm)
assert_type(Blob.meta["k"] * 3,          IntForm)
assert_type((Blob.scores[0] + 1) * 2,    IntForm)


# --- Store commands (whole-blob writes) --------------------------------


# store() on a primitive-blob ref takes the whole container. Just verify
# the ref itself is well-typed here; command return types are Phase 3+.
assert_type(Blob.tags,   PrimitiveListRef[str])
assert_type(Blob.scores, PrimitiveListRef[int])
