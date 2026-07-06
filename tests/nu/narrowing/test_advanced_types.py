"""Task-119 typing tests: chained / nested / computed-key patterns.

Combines subscript, dot-nav, arithmetic, concat, and comparison across
multiple hops. Ref-typed keys and arithmetic-computed keys are the
important cases.
"""

from __future__ import annotations

from typing import assert_type

import nu
from nu.forms import AnyForm, BoolForm, IntForm, StrForm
from nu.virtuals.refs import (
    IntRef,
    StrRef,
)


# --- Shapes ------------------------------------------------------------


class Profile(nu.Shape):
    name:  StrRef
    score: IntRef
    age:   IntRef


class ShapeCache(nu.Shape):
    curr: IntRef
    next: IntRef


class Store(nu.Shape):
    profiles: nu.v.ShapesDictRef[int, Profile]
    ranks:    nu.v.ShapesListRef[Profile]
    indexes:  nu.v.PrimitiveListRef[int]
    cache:    ShapeCache = nu.v.ShapeRef.slot(ShapeCache)


# --- Ref-typed keys ---------------------------------------------------


assert_type(Store.profiles[Store.cache.curr],           Profile)
assert_type(Store.profiles[Store.cache.next],           Profile)
assert_type(Store.profiles[Store.cache.curr].name,      StrRef)
assert_type(Store.profiles[Store.cache.curr].score,     IntRef)
assert_type(Store.profiles[Store.cache.curr].age,       IntRef)


# --- Arithmetic-computed keys -----------------------------------------


assert_type(Store.profiles[Store.cache.curr + 1],       Profile)
assert_type(Store.profiles[(Store.cache.curr + 1) // 2],Profile)
assert_type(Store.profiles[Store.cache.curr * 2],       Profile)
assert_type(Store.profiles[Store.cache.next - 1],       Profile)


# --- Deep concat across multiple navigations --------------------------


assert_type(
    "curr="
    + Store.profiles[Store.cache.curr].name
    + " next="
    + Store.profiles[Store.cache.next].name,
    StrForm,
)


# --- Cross-key arithmetic + comparison --------------------------------


assert_type(
    Store.profiles[Store.cache.next].score
    - Store.profiles[Store.cache.curr].score,
    IntForm,
)
assert_type(
    Store.profiles[Store.cache.next].score
    > Store.profiles[Store.cache.curr].score,
    BoolForm,
)
assert_type(
    Store.profiles[Store.cache.next].age
    + Store.profiles[Store.cache.curr].age,
    IntForm,
)


# --- Chained subscripts through parametric refs -----------------------


# Store.indexes[0] is currently AnyForm (Phase 3 gap). Using it as a key
# into shape-decomposed profiles still returns Profile via the
# ShapesDictRef binding.
assert_type(Store.profiles[Store.indexes[0]],           Profile)
assert_type(Store.profiles[Store.indexes[0]].name,      StrRef)
assert_type(Store.profiles[Store.indexes[0]].score * 2, IntForm)


# FIXME(phase-3): primitive-blob subscript degrades to AnyForm; downstream
# arithmetic stays AnyForm. Explicitly-encoded so Phase 3 flips them.
assert_type(Store.indexes[0],           AnyForm)  # FIXME(phase-3): -> IntForm
assert_type(Store.indexes[Store.cache.curr], AnyForm)  # FIXME(phase-3): -> IntForm
assert_type(Store.indexes[Store.cache.curr] // 2, AnyForm)  # FIXME(phase-3): -> IntForm


# --- Multi-level dot-nav after subscript ------------------------------


class Team(nu.Shape):
    captain: Profile = nu.v.ShapeRef.slot(Profile)


class League(nu.Shape):
    teams:   nu.v.ShapesListRef[Team]
    winners: nu.v.ShapesDictRef[str, Team]


assert_type(League.teams[0],                       Team)
assert_type(League.teams[0].captain,               Profile)
assert_type(League.teams[0].captain.name,          StrRef)
assert_type(League.teams[0].captain.score,         IntRef)
assert_type(League.teams[0].captain.score + 10,    IntForm)

assert_type(League.winners["gold"],                 Team)
assert_type(League.winners["gold"].captain,         Profile)
assert_type(League.winners["gold"].captain.name,    StrRef)
assert_type(
    League.winners["gold"].captain.name
    + " (from gold team)",
    StrForm,
)


# --- Comparison chains across shape collections -----------------------


assert_type(
    League.teams[0].captain.score
    > League.teams[1].captain.score,
    BoolForm,
)
assert_type(
    (League.teams[0].captain.score > 50)
    .and_(League.teams[1].captain.score < 80),
    BoolForm,
)
