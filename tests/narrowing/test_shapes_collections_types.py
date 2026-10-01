"""Task-119 typing tests: decomposed shape collections.

``DictRef[K, T]`` / ``ListRef[T]`` subscript returns ``T`` (the
Shape) statically for dot-nav autocomplete; runtime returns a ``ShapeRef``.
Chained subscript + attribute access flows through cleanly.
"""

from __future__ import annotations

from typing_extensions import assert_type

import nu
import nustd
from nu.forms import Bool, Int, Str
from nustd.kv.refs import (
    DictRef,
    IntRef,
    Kh57Ref,
    ListRef,
    StrRef,
)


# --- Shapes ------------------------------------------------------------


class Profile(nu.Shape):
    name: StrRef
    age: IntRef
    score: IntRef


class Team(nu.Shape):
    members: nustd.kv.DictRef[int, Profile]
    ranks: nustd.kv.ListRef[Profile]


class Org(nu.Shape):
    teams: nustd.kv.DictRef[str, Team]


# --- Whole-container access -------------------------------------------


assert_type(Team.members, DictRef[int, Profile])
assert_type(Team.ranks, ListRef[Profile])
assert_type(Team.ranks.exists(), Bool)
assert_type(Team.ranks.missing(), Bool)
assert_type(Org.teams, DictRef[str, Team])


# --- Subscript -> Shape (annotation lie) ------------------------------


assert_type(Team.members[42], Profile)
assert_type(Team.members[0], Profile)
assert_type(Team.ranks[0], Profile)
assert_type(Team.ranks[7], Profile)


# --- Subscript then field access --------------------------------------


assert_type(Team.members[42].name, StrRef)
assert_type(Team.members[42].age, IntRef)
assert_type(Team.members[42].score, IntRef)

assert_type(Team.ranks[0].name, StrRef)
assert_type(Team.ranks[0].age, IntRef)
assert_type(Team.ranks[0].score, IntRef)


# --- Ref-typed keys ---------------------------------------------------


class Cache(nu.Shape):
    curr: IntRef
    key: StrRef


class Root(nu.Shape):
    cache: Cache = nustd.kv.ShapeRef.slot(Cache)
    members: nustd.kv.DictRef[int, Profile]


# Subscript with an IntRef (Nu-typed key) still returns Profile.
assert_type(Root.members[Root.cache.curr], Profile)
assert_type(Root.members[Root.cache.curr].name, StrRef)
assert_type(Root.members[Root.cache.curr].age + 1, Int)


# --- Nested collections (dict of dict of shape) -----------------------


assert_type(Org.teams["alpha"], Team)
assert_type(Org.teams["alpha"].members[1], Profile)
assert_type(Org.teams["alpha"].members[1].name, StrRef)
assert_type(Org.teams["alpha"].members[1].age + 1, Int)
assert_type(Org.teams["alpha"].ranks[0].score * 2, Int)


# --- Cross-subscript arithmetic ---------------------------------------


assert_type(Team.members[1].score + Team.members[2].score, Int)
assert_type(Team.members[1].score - Team.members[2].score, Int)
assert_type(
    Team.members[1].score > Team.members[2].score,
    Bool,
)


# --- Subscript then concat --------------------------------------------


assert_type(Team.members[42].name + ", welcome!", Str)
assert_type("Hi " + Team.members[42].name, Str)
assert_type(
    Team.ranks[0].name + " vs " + Team.ranks[1].name,
    Str,
)


# --- Double subscript (both are shape collections) --------------------


class Match(nu.Shape):
    home: Profile = nustd.kv.ShapeRef.slot(Profile)
    away: Profile = nustd.kv.ShapeRef.slot(Profile)


class Season(nu.Shape):
    matches: nustd.kv.ListRef[Match]


assert_type(Season.matches[0], Match)
assert_type(Season.matches[0].home, Profile)
assert_type(Season.matches[0].home.name, StrRef)
assert_type(Season.matches[0].away.age, IntRef)
assert_type(
    Season.matches[0].home.score - Season.matches[0].away.score,
    Int,
)


# --- Kh57Ref / Kh57Ref ------------------------------------------


class TickSeries(nu.Shape):
    counters: nustd.kv.Kh57Ref[int]
    points: nustd.kv.Kh57Ref[Profile]


# Whole-container types
assert_type(TickSeries.counters, Kh57Ref[int])
assert_type(TickSeries.points, Kh57Ref[Profile])

# Kh57Ref subscript -> Shape; then field access
assert_type(TickSeries.points[100], Profile)
assert_type(TickSeries.points[100].name, StrRef)
assert_type(TickSeries.points[100].age, IntRef)
assert_type(TickSeries.points[100].age + 1, Int)
