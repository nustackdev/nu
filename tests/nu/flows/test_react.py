"""Tests for reactive control flows: React, ReactWhile, ReactForever.

All three are ``Control`` flows: they drive a mutating body on change events and
yield nothing. Construction, class-hierarchy, and law-validation checks run
without a substrate (validation is structural). Execution (subscription
binding, async queue drain) is deferred to substrate integration.
"""

from __future__ import annotations

import pytest

from nu.domains.shape import Shape
from nu.domains.shape.refs.item import ItemRef
from nu.flows import Race
from nu.flows.react import React, ReactForever, ReactWhile
from nu.lang import LAWS, Control, compile, validate
from nu.virtuals import IntRef


# ---------------------------------------------------------------------------
# Class hierarchy — all three are Controls (Flows), not Queries
# ---------------------------------------------------------------------------


def test_react_is_control():
    assert issubclass(React, Control)


def test_react_while_is_control():
    assert issubclass(ReactWhile, Control)


def test_react_forever_is_control():
    assert issubclass(ReactForever, Control)


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------


def test_react_constructs_with_change_only():
    change = ItemRef("sub")
    r = React(change)
    assert r._children  # at least one child


def test_react_constructs_with_body():
    change = ItemRef("sub")
    body = ItemRef("body")
    r = React(change, body)
    assert len(r._children) >= 2


def test_react_changed_key_requires_body():
    change = ItemRef("sub")
    key = ItemRef("k")
    with pytest.raises(ValueError, match="changed_key requires a body"):
        React(change, changed_key=key)


def test_react_while_constructs():
    change = ItemRef("sub")
    cond = ItemRef("cond")
    body = ItemRef("body")
    r = ReactWhile(change, cond, body)
    assert len(r._children) == 3


def test_react_while_constructs_with_changed_key():
    change = ItemRef("sub")
    cond = ItemRef("cond")
    body = ItemRef("body")
    key = ItemRef("k")
    r = ReactWhile(change, cond, body, changed_key=key)
    assert len(r._children) == 4


def test_react_forever_constructs():
    change = ItemRef("sub")
    body = ItemRef("body")
    r = ReactForever(change, body)
    assert len(r._children) == 2


# ---------------------------------------------------------------------------
# Law validation — a Control driving a mutating body validates, and composes
# as a work branch inside a Strategy (Race). Structural; no substrate needed.
# ---------------------------------------------------------------------------


class _Sensor(Shape):
    n = IntRef.slot()


def _validate(term: object) -> None:
    validate(compile(term), *LAWS)  # raises ValidationError on any failure


def test_react_validates_with_mutating_body():
    _validate(React(_Sensor.n.on_change(), _Sensor.n.set(_Sensor.n + 1)))


def test_react_while_validates_with_mutating_body():
    _validate(ReactWhile(_Sensor.n.on_change(), _Sensor.n < 10, _Sensor.n.set(_Sensor.n + 1)))


def test_react_forever_validates_with_mutating_body():
    _validate(ReactForever(_Sensor.n.on_change(), _Sensor.n.set(_Sensor.n + 1)))


def test_react_while_composes_in_race():
    """The reason for the refactor: a reactive branch is now WORK, so a Strategy holds it."""
    producer = _Sensor.n.set(0)
    consumer_a = ReactWhile(_Sensor.n.on_change(), _Sensor.n < 10, _Sensor.n.set(_Sensor.n + 1))
    consumer_b = ReactForever(_Sensor.n.on_change(), _Sensor.n.set(_Sensor.n + 1))
    _validate(Race(producer, consumer_a, consumer_b))


# ---------------------------------------------------------------------------
# Sync compile raises (async-only)
# ---------------------------------------------------------------------------


def test_react_sync_thunk_raises():
    """Sync compile returns a thunk that raises at execution -- matches Race/AnyN.

    Compile itself must succeed so emit_thunks can walk the whole tree; the raise
    only fires if the sync path is actually driven (arun uses acompile).
    """
    change = ItemRef("sub")
    r = React(change)
    thunk = r._compile(0, ())
    with pytest.raises(RuntimeError, match="async"):
        thunk(None)


def test_react_while_sync_thunk_raises():
    change = ItemRef("sub")
    cond = ItemRef("cond")
    body = ItemRef("body")
    r = ReactWhile(change, cond, body)
    thunk = r._compile(0, ())
    with pytest.raises(RuntimeError, match="async"):
        thunk(None)


def test_react_forever_sync_thunk_raises():
    change = ItemRef("sub")
    body = ItemRef("body")
    r = ReactForever(change, body)
    thunk = r._compile(0, ())
    with pytest.raises(RuntimeError, match="async"):
        thunk(None)


# ---------------------------------------------------------------------------
# Execution deferred
# ---------------------------------------------------------------------------


@pytest.mark.skip(reason="substrate impl deferred — needs asyncio subscription backing store")
async def test_react_fires_on_first_change():
    pass


@pytest.mark.skip(reason="substrate impl deferred — needs asyncio subscription backing store")
async def test_react_while_stops_when_condition_false():
    pass
