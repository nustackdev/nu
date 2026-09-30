"""Tests for the composition operators on the Nu base: ``>>`` / ``|`` / ``&``.

These are sugar for the Strategy flows. Every atom inherits them from ``Nu``, so
the operators are exercised on plain mem ``.set()`` bodies. Coverage pins the
type each operator builds, that chains nest left-to-right, and that a built tree
runs the same as the explicit constructor.
"""

from __future__ import annotations

from _support.policy_atoms import RecordAction

import nu
import nustd.mem
from nu.core.flows import Parallel, Race, Sequential
from nu.domains.shape.interactions import SetCmd
from nu.lang import Context, Literal
from nu.lang.helpers import arun, run


class S(nu.Shape):
    """The mem slots the bodies below write."""

    a = nustd.mem.ObjectRef.slot()
    b = nustd.mem.ObjectRef.slot()
    c = nustd.mem.ObjectRef.slot()


def _set(name: str, value: object) -> SetCmd:
    return getattr(S, name).set(Literal(value))


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
    assert isinstance(right, SetCmd)


# --- built tree runs the same as the explicit constructor -----------------


def test_rshift_runs_like_sequential() -> None:
    data: dict = {}
    run(_set("a", 1) >> _set("b", 2), Context().bind(dict, data, S))
    assert data == {"a": 1, "b": 2}


def test_or_runs_like_parallel() -> None:
    log: list = []
    run(RecordAction(log, "a") | RecordAction(log, "b"), max_parallel=2)
    assert sorted(tag for tag, _, _ in log) == ["a", "b"]


async def test_and_runs_like_race() -> None:
    # Race is async-only; the operator builds it, arun drives it.
    log: list = []
    await arun(RecordAction(log, "a") & RecordAction(log, "b"), max_parallel=2)
    assert {tag for tag, _, _ in log} <= {"a", "b"}
    assert log
