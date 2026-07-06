"""Task-119 typing showcase - level 3: parametric refs.

``Primitive*Ref[T]`` stores raw python primitives as one atomic blob - the
elem is a python leaf type, subscript yields a value-Form. ``ShapesDict``
/ ``ShapesList`` DECOMPOSE the container into per-key/per-index refs -
subscript yields a substrate ``ShapeRef`` you can dot-nav into.
"""

from __future__ import annotations

import nu


# --- Shapes ---


class Profile(nu.Shape):
    name: nu.v.StrRef
    age:  nu.v.IntRef


class Team(nu.Shape):
    # Primitive-blob collections: raw python types inside (blob storage).
    tags: nu.v.PrimitiveListRef[str]
    meta: nu.v.PrimitiveDictRef[str, int]

    # Decomposed shape collections: each element IS a shape ref.
    members: nu.v.ShapesDictRef[int, Profile]
    ranks:   nu.v.ShapesListRef[Profile]


# --- Expressions ---

# Primitive collection subscript yields a value-Form (leaf, no per-elem ref).
first_tag  = Team.tags[0]                        # -> StrForm
meta_users = Team.meta["users"]                  # -> IntForm
meta_count = Team.meta["users"] + 1              # -> IntForm

# Decomposed shape collection subscript yields a substrate ShapeRef.
alice           = Team.members[42]                # -> nu.v.ShapeRef  (static: Profile)
alice_name      = Team.members[42].name           # -> nu.v.StrRef
alice_age_plus1 = Team.members[42].age + 1        # -> IntForm

# Indexed shape list.
first_member  = Team.ranks[0]                     # -> nu.v.ShapeRef
first_age     = Team.ranks[0].age                 # -> nu.v.IntRef
first_greet   = Team.ranks[0].name + ", welcome"  # -> StrForm

# Whole-container access (returns the outer ref itself).
all_tags    = Team.tags                           # -> nu.v.PrimitiveListRef
all_members = Team.members                        # -> nu.v.ShapesDictRef
