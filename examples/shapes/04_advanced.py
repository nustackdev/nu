"""Task-119 typing showcase - level 4: computed keys, arithmetic, deep nesting.

Ref-typed values compose end-to-end through subscripts, arithmetic, and
string ops. The static type at each step follows the annotation and
matches the runtime Form (Phase 3 wrap unification landed).
"""

from __future__ import annotations

import nu


# --- Shapes ---


class Profile(nu.Shape):
    name: nu.v.StrRef
    score: nu.v.IntRef


class ShapeCache(nu.Shape):
    curr: nu.v.IntRef
    next: nu.v.IntRef


class Store(nu.Shape):
    profiles: nu.v.ShapesDictRef[int, Profile]
    indexes: nu.v.PrimitiveListRef[int]
    cache: ShapeCache = nu.v.ShapeRef.slot(ShapeCache)


# --- Expressions ---

# Ref-valued key: subscript a shapes-dict with an IntRef read.
curr_profile = Store.profiles[Store.cache.curr]  # -> ShapeRef  (static: Profile)
curr_profile_ref = Store.profiles[Store.cache.curr].name  # -> nu.v.StrRef

# Concat the navigated leaf with a static string.
greeting = Store.profiles[Store.cache.curr].name + ", hey!"  # -> StrForm

# Arithmetic-computed key: (curr + 1) // 2 keys the primitive index list.
mid_index = Store.indexes[(Store.cache.curr + 1) // 2]  # -> IntForm

# Deeper: pick the next-cache profile and pull its scalar leaf.
next_profile_name = Store.profiles[Store.cache.next].name  # -> nu.v.StrRef

# Cross-key arithmetic: score delta between two cached profiles.
score_delta = (
    Store.profiles[Store.cache.next].score - Store.profiles[Store.cache.curr].score
)  # -> IntForm

# Comparison chained through nested nav.
did_improve = (
    Store.profiles[Store.cache.next].score > Store.profiles[Store.cache.curr].score
)  # -> BoolForm

# Double-subscript: the profile at an id read from the primitive index list.
top_by_id_ref = Store.profiles[Store.indexes[0]]  # -> ShapeRef
top_by_id_name = Store.profiles[Store.indexes[0]].name  # -> nu.v.StrRef

# Nested primitive-list read used as a shapes-dict key, then floor-divided.
computed_key = Store.indexes[Store.cache.curr] // 2  # -> IntForm
weird_profile = Store.profiles[computed_key]  # -> ShapeRef
weird_greeting = Store.profiles[computed_key].name + " ok"  # -> StrForm

# Even further: arithmetic on the score of a computed profile.
score_x2 = Store.profiles[Store.indexes[Store.cache.curr]].score * 2
# -> IntForm

# Mixing everything: banner built from three navigations.
full_banner = (
    "curr="
    + Store.profiles[Store.cache.curr].name
    + " next="
    + Store.profiles[Store.cache.next].name
)  # -> StrForm
