# ruff: noqa: TC001
"""Task-119 typing tests: NEGATIVE - things that SHOULD fail typecheck.

Every violation is on a ``# type: ignore[error-code]`` line. Mypy runs
with ``warn_unused_ignores = True`` (see ``mypy.ini``), so if a fix ever
lands that removes the error, the ignore becomes unused and mypy fails -
forcing the reviewer to promote the case to a positive assertion.

All violations live inside ``_type_checks_only()`` so import-time runtime
doesn't try to actually evaluate them (some raise ``AttributeError`` etc.);
mypy still descends into the function body and verifies each ignore.
"""

from __future__ import annotations

import nu
from nu.forms import Int, Str
from nu.kv.refs import IntRef, ShapesDictRef, StrRef


# --- Shapes (used across the negative cases) ---------------------------


class Profile(nu.Shape):
    name: StrRef
    age: IntRef


class Address(nu.Shape):
    city: StrRef


class Other(nu.Shape):
    x: IntRef


class Store(nu.Shape):
    profiles: ShapesDictRef[int, Profile]


class WithMembers(nu.Shape):
    members: ShapesDictRef[int, Profile]


def _type_checks_only() -> None:
    """Body is type-checked by mypy but never called at runtime.

    Each block documents WHAT should error and WHY. Removing the ignore
    should cause mypy to flag the actual error; if the ignore ever goes
    unused, mypy's ``warn_unused_ignores`` fails this file.
    """

    # 1. StrRef is not str; assigning to a raw-str variable is a mismatch.
    _wrong_leaf: str = Profile.name  # type: ignore[assignment]

    # 2. Store.profiles is ShapesDictRef[int, Profile]; subscript returns
    #    Profile, not Other.
    _wrong_subscript: Other = Store.profiles[42]  # type: ignore[assignment]

    # 3. Int from arithmetic is not Str.
    _wrong_arithmetic: Str = Profile.age + 1  # type: ignore[assignment]

    # 4. Str from concat is not Int.
    _wrong_concat: Int = Profile.name + "!"  # type: ignore[assignment]

    # 5. Bool from a comparison is not Int.
    _wrong_cmp: Int = Profile.age > 18  # type: ignore[assignment]

    # 6. Str.__add__ takes str-like; adding an int is a type error.
    _bad_add = Profile.name + 5  # type: ignore[operator]

    # 7. Profile is not Address; assignment fails.
    _wrong_shape_ann: Address = Profile.name  # type: ignore[assignment]

    # 8. Profile has no slot ``nonexistent``; attribute-error at type-check.
    _bad_attr = WithMembers.members[1].nonexistent  # type: ignore[attr-defined]

    # 9. Bool.and_ takes BoolArg (bool | Nu[bool] | Sentinel);
    #    a float literal is none of those.
    _bad_and = (Profile.age > 18).and_(1.5)  # type: ignore[arg-type]

    # 10. Reference the locals so ruff doesn't strip the assignments.
    _ = (
        _wrong_leaf,
        _wrong_subscript,
        _wrong_arithmetic,
        _wrong_concat,
        _wrong_cmp,
        _bad_add,
        _wrong_shape_ann,
        _bad_attr,
        _bad_and,
    )


# --- Positive redundancy: sanity anchor -------------------------------


# A clean assignment to keep at least one runtime-safe line, so pytest
# collection has something to import. Not needed for the negative
# semantics; just makes the module non-empty at runtime.
_ok: IntRef = Profile.age
