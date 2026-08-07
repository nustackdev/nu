"""Task-119 typing tests: chained / nested / computed-key patterns.

Combines subscript, dot-nav, arithmetic, concat, and comparison across
multiple hops. Ref-typed keys and arithmetic-computed keys are the
important cases.
"""

from __future__ import annotations

from typing_extensions import assert_type

import nu
from nu.forms import Bool, Int, Str
from nu.virtuals.refs import (
    IntRef,
    StrRef,
)


# --- Shapes ------------------------------------------------------------


class Profile(nu.Shape):
    name: StrRef
    score: IntRef
    age: IntRef


class ShapeCache(nu.Shape):
    curr: IntRef
    next: IntRef


class Store(nu.Shape):
    profiles: nu.kv.ShapesDictRef[int, Profile]
    ranks: nu.kv.ShapesListRef[Profile]
    indexes: nu.kv.PrimitiveListRef[int]
    cache: ShapeCache = nu.kv.ShapeRef.slot(ShapeCache)


# --- Ref-typed keys ---------------------------------------------------


assert_type(Store.profiles[Store.cache.curr], Profile)
assert_type(Store.profiles[Store.cache.next], Profile)
assert_type(Store.profiles[Store.cache.curr].name, StrRef)
assert_type(Store.profiles[Store.cache.curr].score, IntRef)
assert_type(Store.profiles[Store.cache.curr].age, IntRef)


# --- Arithmetic-computed keys -----------------------------------------


assert_type(Store.profiles[Store.cache.curr + 1], Profile)
assert_type(Store.profiles[(Store.cache.curr + 1) // 2], Profile)
assert_type(Store.profiles[Store.cache.curr * 2], Profile)
assert_type(Store.profiles[Store.cache.next - 1], Profile)


# --- Deep concat across multiple navigations --------------------------


assert_type(
    "curr="
    + Store.profiles[Store.cache.curr].name
    + " next="
    + Store.profiles[Store.cache.next].name,
    Str,
)


# --- Cross-key arithmetic + comparison --------------------------------


assert_type(
    Store.profiles[Store.cache.next].score - Store.profiles[Store.cache.curr].score,
    Int,
)
assert_type(
    Store.profiles[Store.cache.next].score > Store.profiles[Store.cache.curr].score,
    Bool,
)
assert_type(
    Store.profiles[Store.cache.next].age + Store.profiles[Store.cache.curr].age,
    Int,
)


# --- Chained subscripts through parametric refs -----------------------


# Store.indexes[0] is currently Any (Phase 3 gap). Using it as a key
# into shape-decomposed profiles still returns Profile via the
# ShapesDictRef binding.
assert_type(Store.profiles[Store.indexes[0]], Profile)
assert_type(Store.profiles[Store.indexes[0]].name, StrRef)
assert_type(Store.profiles[Store.indexes[0]].score * 2, Int)


# Primitive-blob subscript narrows to the elem's Form; downstream
# arithmetic composes narrowly (Phase 3).
assert_type(Store.indexes[0], Int)
assert_type(Store.indexes[Store.cache.curr], Int)
assert_type(Store.indexes[Store.cache.curr] // 2, Int)


# --- Multi-level dot-nav after subscript ------------------------------


class Team(nu.Shape):
    captain: Profile = nu.kv.ShapeRef.slot(Profile)


class League(nu.Shape):
    teams: nu.kv.ShapesListRef[Team]
    winners: nu.kv.ShapesDictRef[str, Team]


assert_type(League.teams[0], Team)
assert_type(League.teams[0].captain, Profile)
assert_type(League.teams[0].captain.name, StrRef)
assert_type(League.teams[0].captain.score, IntRef)
assert_type(League.teams[0].captain.score + 10, Int)

assert_type(League.winners["gold"], Team)
assert_type(League.winners["gold"].captain, Profile)
assert_type(League.winners["gold"].captain.name, StrRef)
assert_type(
    League.winners["gold"].captain.name + " (from gold team)",
    Str,
)


# --- Comparison chains across shape collections -----------------------


assert_type(
    League.teams[0].captain.score > League.teams[1].captain.score,
    Bool,
)
assert_type(
    (League.teams[0].captain.score > 50).and_(League.teams[1].captain.score < 80),
    Bool,
)
