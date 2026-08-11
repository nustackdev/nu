"""Task-119 typing tests: nested Shape dot-nav.

Bare Shape annotations (``field: Order``) are the ergonomic lie - static
shows the Shape (dot-nav autocompletes over its slots); runtime returns a
``ShapeRef``. Verified 1-hop, 2-hop, 3-hop, 4-hop.
"""

from __future__ import annotations

from typing_extensions import assert_type

import nu
from nu.forms import Bool, Int, Str
from nu.kv.refs import (
    IntRef,
    StrRef,
)


# --- Shapes ------------------------------------------------------------


class ZipCode(nu.Shape):
    code: IntRef
    country: StrRef


class Address(nu.Shape):
    street: StrRef
    city: StrRef
    zipcode: ZipCode = nu.kv.ShapeRef.slot(ZipCode)


class Profile(nu.Shape):
    name: StrRef
    age: IntRef
    address: Address = nu.kv.ShapeRef.slot(Address)


class User(nu.Shape):
    handle: StrRef
    profile: Profile = nu.kv.ShapeRef.slot(Profile)


# --- One-hop dot-nav ---------------------------------------------------


assert_type(User.handle, StrRef)
assert_type(User.profile, Profile)  # annotation lie: runtime is ShapeRef


# --- Two-hop dot-nav ---------------------------------------------------


assert_type(User.profile.name, StrRef)
assert_type(User.profile.age, IntRef)
assert_type(User.profile.address, Address)  # annotation lie


# --- Three-hop dot-nav -------------------------------------------------


assert_type(User.profile.address.street, StrRef)
assert_type(User.profile.address.city, StrRef)
assert_type(User.profile.address.zipcode, ZipCode)  # annotation lie


# --- Four-hop dot-nav --------------------------------------------------


assert_type(User.profile.address.zipcode.code, IntRef)
assert_type(User.profile.address.zipcode.country, StrRef)


# --- Mixed with arithmetic / concat / comparison ----------------------


assert_type(User.profile.age + 1, Int)
assert_type(User.profile.age > 30, Bool)
assert_type("Hello " + User.profile.name, Str)
assert_type(User.profile.name + "!", Str)
assert_type(User.profile.address.zipcode.code + 1, Int)
assert_type(User.profile.address.zipcode.code == 90210, Bool)


# --- Chained concat across hops ---------------------------------------


assert_type(
    User.profile.address.street + ", " + User.profile.address.city,
    Str,
)
assert_type(
    "User " + User.handle + " lives in " + User.profile.address.city,
    Str,
)


# --- Direct ShapeRef access (constructor form) -------------------------


# Using ShapeRef directly (not via annotation lie) still resolves.
direct = nu.kv.ShapeRef.slot(Profile)
assert_type(direct, Profile)  # slot returns S (annotation lie)


# --- Nested-shape existence check -------------------------------------


assert_type(User.profile.name.is_empty(), Bool)
assert_type(User.profile.address.zipcode.code.is_empty(), Bool)
