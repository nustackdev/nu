# `assert_type` needs runtime access to its type arg, so imports stay top-level.
"""Task-119 typing tests: leaf refs + primitive-value ops.

Each ``assert_type(expr, T)`` is a mypy-verified narrowing check. Runtime
is a no-op (returns the first argument), so the file also loads cleanly
under pytest. Run via ``tests/nu/narrowing/test_mypy_runner.py``.
"""

from __future__ import annotations

from typing import assert_type

import nu
from nu.forms import BoolForm, BytesForm, FloatForm, IntForm, StrForm
from nu.mem.refs import IntRef as MemIntRef
from nu.mem.refs import StrRef as MemStrRef
from nu.virtuals.refs import (
    BoolRef,
    BytesRef,
    FloatRef,
    IntRef,
    StrRef,
)


# --- Shapes -------------------------------------------------------------


class Profile(nu.Shape):
    name:   StrRef
    age:    IntRef
    active: BoolRef
    score:  FloatRef
    blob:   BytesRef


class MemProfile(nu.Shape):
    name: MemStrRef
    age:  MemIntRef


# --- Leaf-ref access: annotation IS the type ----------------------------


assert_type(Profile.name,   StrRef)
assert_type(Profile.age,    IntRef)
assert_type(Profile.active, BoolRef)
assert_type(Profile.score,  FloatRef)
assert_type(Profile.blob,   BytesRef)

# mem fabric works the same way
assert_type(MemProfile.name, MemStrRef)
assert_type(MemProfile.age,  MemIntRef)


# --- Int arithmetic -----------------------------------------------------


assert_type(Profile.age + 1,             IntForm)
assert_type(Profile.age - 1,             IntForm)
assert_type(Profile.age * 2,             IntForm)
assert_type(Profile.age // 2,            IntForm)
assert_type(Profile.age % 5,             IntForm)
assert_type(Profile.age ** 2,            IntForm)
assert_type(Profile.age + Profile.age,   IntForm)
assert_type(Profile.age - Profile.age,   IntForm)
assert_type(Profile.age * Profile.age,   IntForm)

# chained arithmetic
assert_type(Profile.age + 1 + 2,         IntForm)
assert_type((Profile.age + 1) * 3,       IntForm)
assert_type(Profile.age + Profile.age + 1, IntForm)


# --- Float arithmetic ---------------------------------------------------


assert_type(Profile.score + 1.5,           FloatForm)
assert_type(Profile.score * 2.0,           FloatForm)
assert_type(Profile.score - Profile.score, FloatForm)


# --- String ops ---------------------------------------------------------


assert_type(Profile.name + ", hey!",         StrForm)
assert_type("Hi " + Profile.name,            StrForm)
assert_type(Profile.name + Profile.name,     StrForm)


# --- Bytes ops ----------------------------------------------------------


assert_type(Profile.blob + b"tail",          BytesForm)


# --- Boolean logical ----------------------------------------------------


is_adult = Profile.age >= 18
assert_type(is_adult, BoolForm)

is_top   = Profile.score > 90.0
assert_type(is_top, BoolForm)

assert_type(is_adult.and_(is_top),          BoolForm)
assert_type(is_adult.or_(is_top),           BoolForm)
assert_type(is_adult.not_(),                BoolForm)
assert_type(is_adult.and_(Profile.active),  BoolForm)


# --- Comparison ---------------------------------------------------------


assert_type(Profile.age >= 18,               BoolForm)
assert_type(Profile.age < 18,                BoolForm)
assert_type(Profile.age <= 65,               BoolForm)
assert_type(Profile.age > 0,                 BoolForm)
assert_type(Profile.age == Profile.age,      BoolForm)
assert_type(Profile.age != 0,                BoolForm)

assert_type(Profile.name == "alice",         BoolForm)
assert_type(Profile.name != "bob",           BoolForm)

assert_type(Profile.score > Profile.score,   BoolForm)


# --- Cross-type comparison ---------------------------------------------


assert_type((Profile.age + 1) > Profile.age, BoolForm)


# --- Any escape hatch through sentinel checks --------------------------


assert_type(Profile.age.is_empty(),        BoolForm)
assert_type(Profile.age.is_invalid(),      BoolForm)
assert_type(Profile.age.is_sentinel(),     BoolForm)
assert_type(Profile.age.not_empty(),       BoolForm)
assert_type(Profile.age.not_invalid(),     BoolForm)


# --- Nothing here should introduce AnyForm ------------------------------


def _no_any_leaks() -> None:
    # If any of these silently degraded to AnyForm, mypy would complain
    # about the assert_type mismatch.
    x = Profile.age + 1 + Profile.age * 2 - Profile.age // 3
    assert_type(x, IntForm)
    y = (Profile.age >= 18).and_((Profile.score > 90.0).not_())
    assert_type(y, BoolForm)
    z = Profile.name + " " + Profile.name + "!"
    assert_type(z, StrForm)

