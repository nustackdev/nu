"""Task-119 typing showcase - level 1: leaf refs.

Hover over each assigned variable in your editor to see the narrowed static
type. Under the annotation-driven surface, ``Profile.name`` is statically
typed as ``nu.v.StrRef`` (correct: at runtime it IS a ``StrRef`` instance),
and every arithmetic / string / logical op returns the matching ``*Form``.
"""

from __future__ import annotations

import nu


# --- Shapes ---


class Profile(nu.Shape):
    """A user profile with primitive-typed leaf refs."""

    name:   nu.v.StrRef
    age:    nu.v.IntRef
    active: nu.v.BoolRef
    score:  nu.v.FloatRef


# --- Expressions ---

# Leaf ref access - the annotation IS the type.
name_ref   = Profile.name              # -> nu.v.StrRef
age_ref    = Profile.age               # -> nu.v.IntRef
active_ref = Profile.active            # -> nu.v.BoolRef
score_ref  = Profile.score             # -> nu.v.FloatRef

# Arithmetic on IntRef (mixes in IntForm).
next_age   = Profile.age + 1           # -> IntForm
double_age = Profile.age * 2           # -> IntForm
age_diff   = Profile.age - Profile.age # -> IntForm  (silly, but well-typed)
half_age   = Profile.age // 2          # -> IntForm

# Float arithmetic.
scaled = Profile.score * 1.5           # -> FloatForm

# Comparison -> BoolForm.
is_adult   = Profile.age >= 18         # -> BoolForm
is_top     = Profile.score > 90.0      # -> BoolForm

# String concat on StrRef (mixes in StrForm).
greeting   = Profile.name + ", hey!"   # -> StrForm
banner     = "Hi " + Profile.name      # -> StrForm  (via __radd__)

# Logical combination of BoolForms (`&` / `|` on Nu are flow operators;
# for logical AND/OR/NOT use the named methods).
is_top_adult = is_adult.and_(is_top)   # -> BoolForm
either       = is_adult.or_(is_top)    # -> BoolForm
negated      = is_adult.not_()         # -> BoolForm
