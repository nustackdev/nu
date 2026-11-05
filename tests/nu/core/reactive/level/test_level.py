"""Tests every level flow shares: construction, laws, the async-only sync path."""

from __future__ import annotations

import pytest

import nu
from nu.context import Attr as AttrRef
from nu.core.reactive import (
    Reconcile,
    ReconcileEach,
    ReconcileLatest,
    ReconcileLatestEach,
    ReconcileWhile,
    WaitUntil,
)
from nu.domains.shape import Shape
from nu.lang import Attr, Control
from nu.lang.helpers import compile, validate
from nustd.kv import IntRef


# ---------------------------------------------------------------------------
# Construction and laws
# ---------------------------------------------------------------------------


class _Sensor(Shape):
    n = IntRef.slot()


LEVEL = [Reconcile, ReconcileEach, ReconcileLatest, ReconcileLatestEach, ReconcileWhile, WaitUntil]


def _one_of_each() -> dict[type, object]:
    """One instance per level flow, over a real shape so the tree validates."""
    change, write = _Sensor.n.on_change(), _Sensor.n.set(_Sensor.n + 1)
    return {
        Reconcile: Reconcile(change, write),
        ReconcileEach: ReconcileEach(nu.Iter([1]), change, write),
        ReconcileLatest: ReconcileLatest(_Sensor.n, change, write),
        ReconcileLatestEach: ReconcileLatestEach(nu.Iter([1]), change, write),
        ReconcileWhile: ReconcileWhile(change, _Sensor.n < 3, write),
        WaitUntil: WaitUntil(change, _Sensor.n > 3),
    }


@pytest.mark.parametrize("flow", LEVEL)
def test_level_flows_are_controls(flow: type) -> None:
    assert issubclass(flow, Control)


@pytest.mark.parametrize("flow", LEVEL)
def test_level_flows_validate(flow: type) -> None:
    validate(compile(_one_of_each()[flow]))


@pytest.mark.parametrize(
    ("flow", "slots"),
    [
        (Reconcile, {0, 2, 3}),
        (ReconcileEach, {0, 1, 3, 4, 5}),
        (ReconcileLatest, {0, 1, 3, 4, 5}),
        (ReconcileLatestEach, {0, 1, 3, 4, 5}),
        (ReconcileWhile, {0, 1, 3, 4}),
        (WaitUntil, {0, 1, 2, 3}),
    ],
)
def test_level_flows_are_async_only_and_declare_their_params(flow: type, slots: set) -> None:
    program = compile(_one_of_each()[flow])
    assert program.attr(program.root, Attr.REQUIRES_ASYNC)
    assert program.attr(program.root, Attr.PARAM_SLOTS) == frozenset(slots)


def test_sync_thunks_raise() -> None:
    for term in (
        Reconcile(AttrRef("feed"), nu.Noop()),
        WaitUntil(AttrRef("feed"), nu.Literal(True)),
        ReconcileWhile(AttrRef("feed"), nu.Literal(True), nu.Noop()),
        ReconcileEach(nu.Iter([1]), AttrRef("feed"), nu.Noop()),
        ReconcileLatest(nu.Literal(1), AttrRef("feed"), nu.Noop()),
        ReconcileLatestEach(nu.Iter([1]), AttrRef("feed"), nu.Noop()),
    ):
        with pytest.raises(RuntimeError, match="async"):
            term._compile(0, ())(None)


def test_a_body_cannot_ask_for_the_changed_key() -> None:
    with pytest.raises(TypeError, match="0 values"):
        Reconcile(AttrRef("feed"), lambda key: nu.print(key))
    with pytest.raises(TypeError, match="0 values"):
        WaitUntil(AttrRef("feed"), lambda key: key)


def test_a_lambda_taking_nothing_builds_the_body() -> None:
    term = WaitUntil(AttrRef("feed"), lambda: nu.Literal(True))
    assert nu.tree.equal(term, WaitUntil(AttrRef("feed"), nu.Literal(True)))
