"""Tests for the composition operators on the Nu base: ``>>`` / ``|`` / ``&``.

These are sugar for the Strategy flows. Every atom inherits them from ``Nu``, so
the operators are exercised on plain ``.set()`` bodies. Coverage pins the
type each operator builds, that chains nest left-to-right, and that a built tree
runs the same as the explicit constructor.
"""

from __future__ import annotations

from _support.attrs import declared

import nu
from nu.context import ObjectRef
from nu.context.attrs import Set
from nu.core.flows import Parallel, Race, Sequential
from nu.lang import Literal
from nu.lang.helpers import arun, run


def _set(name: str, value: object) -> Set:
    return ObjectRef(name).set(Literal(value))


# --- each operator builds its Strategy ------------------------------------


def test_rshift_builds_sequential() -> None:
    tree = _set("a", 1) >> _set("b", 2)
    assert isinstance(tree, Sequential)
    assert len(nu.tree.children(tree)) == 2


def test_or_builds_parallel() -> None:
    tree = _set("a", 1) | _set("b", 2)
    assert isinstance(tree, Parallel)
    assert len(nu.tree.children(tree)) == 2


def test_and_builds_race() -> None:
    tree = _set("a", 1) & _set("b", 2)
    assert isinstance(tree, Race)
    assert len(nu.tree.children(tree)) == 2


# --- chaining nests left-to-right -----------------------------------------


def test_rshift_chain_nests_left() -> None:
    # a >> b >> c == Sequential(Sequential(a, b), c)
    tree = _set("a", 1) >> _set("b", 2) >> _set("c", 3)
    assert isinstance(tree, Sequential)
    left, right = nu.tree.children(tree)
    assert isinstance(left, Sequential)
    assert isinstance(right, Set)


# --- built tree runs the same as the explicit constructor -----------------


def test_rshift_runs_like_sequential() -> None:
    _, ctx = run(_set("a", 1) >> _set("b", 2), declared("a", "b"))
    assert ctx.attrs["a"] == 1
    assert ctx.attrs["b"] == 2


def test_or_runs_like_parallel() -> None:
    _, ctx = run(_set("a", 1) | _set("b", 2), declared("a", "b"), max_parallel=2)
    assert ctx.attrs["a"] == 1
    assert ctx.attrs["b"] == 2


async def test_and_runs_like_race() -> None:
    # Race is async-only; the operator builds it, arun drives it.
    _, ctx = await arun(_set("a", 1) & _set("b", 2), declared("a", "b"), max_parallel=2)
    assert ctx.attrs.get("a") == 1 or ctx.attrs.get("b") == 2
