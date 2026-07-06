"""Task-119 typing showcase - level 2: nested shape navigation.

A nested shape is annotated with the Shape class directly (``profile:
Profile``) - not ``ShapeRef[Profile]`` - so ``.``-nav autocomplete follows
Profile's own slots. The explicit ``= nu.v.ShapeRef.slot(Profile)`` names
the fabric (bare Shape annotations can't infer it).

At runtime the value is a ``ShapeRef``, and each field access returns the
matching leaf ref of Profile.
"""

from __future__ import annotations

import nu


# --- Shapes ---


class Address(nu.Shape):
    street:  nu.v.StrRef
    city:    nu.v.StrRef
    zipcode: nu.v.IntRef


class Profile(nu.Shape):
    name:    nu.v.StrRef
    age:     nu.v.IntRef
    address: Address = nu.v.ShapeRef.slot(Address)


class User(nu.Shape):
    handle:  nu.v.StrRef
    profile: Profile = nu.v.ShapeRef.slot(Profile)


# --- Expressions ---

# One hop into a nested Shape - static shows Profile's surface via the
# ``profile: Profile`` annotation lie; runtime returns a nu.v.ShapeRef.
profile_ref = User.profile               # -> nu.v.ShapeRef  (static: Profile)

# Two hops - dot-nav follows Profile's slots.
handle    = User.handle                  # -> nu.v.StrRef
name      = User.profile.name            # -> nu.v.StrRef
age       = User.profile.age             # -> nu.v.IntRef

# Three hops - Profile.address is Address, .city is Address's own StrRef.
city      = User.profile.address.city    # -> nu.v.StrRef
street    = User.profile.address.street  # -> nu.v.StrRef
zipcode   = User.profile.address.zipcode # -> nu.v.IntRef

# Mixed with arithmetic / string ops.
banner    = "Hi " + User.profile.name    # -> StrForm
next_zip  = User.profile.address.zipcode + 1  # -> IntForm
is_old    = User.profile.age > 30              # -> BoolForm

# Chain everything.
addr_line = User.profile.address.street + ", " + User.profile.address.city
# -> StrForm
