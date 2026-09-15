"""Tests for the host-namespace escape-hatch atoms (Globals, Locals).

Reach the host namespace directly; checked at the attribute level and
driven to confirm they bypass the Context into raw Python.
"""

from __future__ import annotations

from nu.core.dynamic import Globals as Globals
from nu.core.dynamic import Locals as Locals
from nu.lang import Attr
from nu.lang.helpers import compile, eval


def _eval(term: object) -> object:
    value, _ = eval(compile(term))
    return value


def test_globals_and_locals_are_scalar_queries():
    # Pure attribute check: structural, no live-namespace fabric needed here.
    assert compile(Globals()).attr((), Attr.COMPOSITION_EFFECTS) == frozenset()
    assert compile(Locals()).attr((), Attr.COMPOSITION_EFFECTS) == frozenset()


def test_globals_returns_the_host_namespace_dict():
    assert isinstance(_eval(Globals()), dict)


def test_locals_returns_a_dict():
    assert isinstance(_eval(Locals()), dict)
