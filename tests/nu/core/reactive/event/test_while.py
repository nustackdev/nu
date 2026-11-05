"""Tests for ReactWhile: run the body on each change while a condition holds."""

from __future__ import annotations

import pytest

import nu
from nu.core.flows import Race
from nu.core.reactive.event import ReactEvery, ReactWhile
from nu.domains.shape import Shape
from nu.domains.shape.item import ItemRef
from nu.lang import Control
from nu.lang.helpers import compile, validate
from nustd.kv import IntRef


def test_react_while_is_control():
    assert issubclass(ReactWhile, Control)


def test_react_while_constructs():
    change = ItemRef("sub")
    cond = ItemRef("cond")
    body = ItemRef("body")
    r = ReactWhile(change, cond, body)
    assert len(nu.tree.children(r)) == 3


def test_react_while_constructs_with_changed_key():
    change = ItemRef("sub")
    cond = ItemRef("cond")
    body = ItemRef("body")
    key = ItemRef("k")
    r = ReactWhile(change, cond, body, changed_key=key)
    assert len(nu.tree.children(r)) == 4


# ---------------------------------------------------------------------------
# Law validation: a Control driving a mutating body validates, and composes
# as a work branch inside a Strategy (Race). Structural; no substrate needed.
# ---------------------------------------------------------------------------


class _Sensor(Shape):
    n = IntRef.slot()


def _validate(term: object) -> None:
    validate(compile(term))  # raises ValidationError on any failure


def test_react_while_validates_with_mutating_body():
    _validate(ReactWhile(_Sensor.n.on_change(), _Sensor.n < 10, _Sensor.n.set(_Sensor.n + 1)))


def test_react_while_composes_in_race():
    """The reason for the refactor: a reactive branch is now WORK, so a Strategy holds it."""
    producer = _Sensor.n.set(0)
    consumer_a = ReactWhile(_Sensor.n.on_change(), _Sensor.n < 10, _Sensor.n.set(_Sensor.n + 1))
    consumer_b = ReactEvery(_Sensor.n.on_change(), _Sensor.n.set(_Sensor.n + 1))
    _validate(Race(producer, consumer_a, consumer_b))


def test_react_while_sync_thunk_raises():
    change = ItemRef("sub")
    cond = ItemRef("cond")
    body = ItemRef("body")
    r = ReactWhile(change, cond, body)
    thunk = r._compile(0, ())
    with pytest.raises(RuntimeError, match="async"):
        thunk(None)


@pytest.mark.skip(reason="substrate impl deferred: needs asyncio subscription backing store")
async def test_react_while_stops_when_condition_false():
    pass
