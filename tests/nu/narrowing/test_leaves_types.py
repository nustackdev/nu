# `assert_type` needs runtime access to its type arg, so imports stay top-level.
"""Task-119 typing tests: leaf refs + primitive-value ops.

Each ``assert_type(expr, T)`` is a mypy-verified narrowing check. Runtime
is a no-op (returns the first argument), so the file also loads cleanly
under pytest. Run via ``tests/nu/narrowing/test_mypy_runner.py``.
"""

from __future__ import annotations

from typing_extensions import assert_type

import nu
from nu.forms import Bool, Bytes, Float, Int, Str
from nu.kv.refs import (
    BoolRef,
    BytesRef,
    FloatRef,
    IntRef,
    StrRef,
)
from nu.mem.refs import IntRef as MemIntRef
from nu.mem.refs import StrRef as MemStrRef


# --- Shapes -------------------------------------------------------------


class Profile(nu.Shape):
    name: StrRef
    age: IntRef
    active: BoolRef
    score: FloatRef
    blob: BytesRef


class MemProfile(nu.Shape):
    name: MemStrRef
    age: MemIntRef


# --- Leaf-ref access: annotation IS the type ----------------------------


assert_type(Profile.name, StrRef)
assert_type(Profile.age, IntRef)
assert_type(Profile.active, BoolRef)
assert_type(Profile.score, FloatRef)
assert_type(Profile.blob, BytesRef)

# mem fabric works the same way
assert_type(MemProfile.name, MemStrRef)
assert_type(MemProfile.age, MemIntRef)


# --- Int arithmetic -----------------------------------------------------


assert_type(Profile.age + 1, Int)
assert_type(Profile.age - 1, Int)
assert_type(Profile.age * 2, Int)
assert_type(Profile.age // 2, Int)
assert_type(Profile.age % 5, Int)
assert_type(Profile.age**2, Int)
assert_type(Profile.age + Profile.age, Int)
assert_type(Profile.age - Profile.age, Int)
assert_type(Profile.age * Profile.age, Int)

# chained arithmetic
assert_type(Profile.age + 1 + 2, Int)
assert_type((Profile.age + 1) * 3, Int)
assert_type(Profile.age + Profile.age + 1, Int)


# --- Float arithmetic ---------------------------------------------------


assert_type(Profile.score + 1.5, Float)
assert_type(Profile.score * 2.0, Float)
assert_type(Profile.score - Profile.score, Float)


# --- String ops ---------------------------------------------------------


assert_type(Profile.name + ", hey!", Str)
assert_type("Hi " + Profile.name, Str)
assert_type(Profile.name + Profile.name, Str)


# --- Bytes ops ----------------------------------------------------------


assert_type(Profile.blob + b"tail", Bytes)


# --- Boolean logical ----------------------------------------------------


is_adult = Profile.age >= 18
assert_type(is_adult, Bool)

is_top = Profile.score > 90.0
assert_type(is_top, Bool)

assert_type(is_adult.and_(is_top), Bool)
assert_type(is_adult.or_(is_top), Bool)
assert_type(is_adult.not_(), Bool)
assert_type(is_adult.and_(Profile.active), Bool)


# --- Comparison ---------------------------------------------------------


assert_type(Profile.age >= 18, Bool)
assert_type(Profile.age < 18, Bool)
assert_type(Profile.age <= 65, Bool)
assert_type(Profile.age > 0, Bool)
assert_type(Profile.age == Profile.age, Bool)
assert_type(Profile.age != 0, Bool)

assert_type(Profile.name == "alice", Bool)
assert_type(Profile.name != "bob", Bool)

assert_type(Profile.score > Profile.score, Bool)


# --- Cross-type comparison ---------------------------------------------


assert_type((Profile.age + 1) > Profile.age, Bool)


# --- Any escape hatch through sentinel checks --------------------------


assert_type(Profile.age.is_empty(), Bool)
assert_type(Profile.age.is_invalid(), Bool)
assert_type(Profile.age.is_sentinel(), Bool)
assert_type(Profile.age.not_empty(), Bool)
assert_type(Profile.age.not_invalid(), Bool)


# --- Nothing here should introduce Any ------------------------------


def _no_any_leaks() -> None:
    # If any of these silently degraded to Any, mypy would complain
    # about the assert_type mismatch.
    x = Profile.age + 1 + Profile.age * 2 - Profile.age // 3
    assert_type(x, Int)
    y = (Profile.age >= 18).and_((Profile.score > 90.0).not_())
    assert_type(y, Bool)
    z = Profile.name + " " + Profile.name + "!"
    assert_type(z, Str)
