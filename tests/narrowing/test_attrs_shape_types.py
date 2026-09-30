# `assert_type` needs runtime access to its type arg, so imports stay top-level.
"""Typing tests: attrs refs as Shape slots.

A slot on an attrs Shape is typed as the attrs ref it names, in both
spellings, so its form surface and ``set`` / ``exists`` narrow as on a plain
attrs ref. Run via ``tests/narrowing/test_mypy_runner.py``.
"""

from __future__ import annotations

from typing_extensions import assert_type

import nu
from nu.context.attrs import Exists, Set
from nu.forms import Bool, Int, Str


class Attrs(nu.Shape):
    plane = nu.StrRef.slot()
    count = nu.IntRef.slot()
    ui: nu.BoolRef
    anything: nu.ObjectRef


assert_type(Attrs.plane, nu.StrRef)
assert_type(Attrs.count, nu.IntRef)
assert_type(Attrs.ui, nu.BoolRef)
assert_type(Attrs.anything, nu.ObjectRef)

assert_type(Attrs.plane.upper(), Str)
assert_type(Attrs.count + 1, Int)
assert_type(Attrs.plane == "p", Bool)

assert_type(Attrs.plane.set("p"), Set)
assert_type(Attrs.ui.exists(), Exists)
assert_type(nu.Let(Attrs.plane, "p", Attrs.plane.upper()), nu.Let)
