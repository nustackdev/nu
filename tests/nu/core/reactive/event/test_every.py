"""Tests for ReactEvery: run the body on every change, in order."""

from __future__ import annotations

import pytest

import nu
from nu.core.reactive.event import ReactEvery
from nu.domains.shape import Shape
from nu.domains.shape.item import ItemRef
from nu.lang import Control
from nu.lang.helpers import compile, validate
from nustd.kv import IntRef


def test_react_every_is_control():
    assert issubclass(ReactEvery, Control)


def test_react_every_constructs():
    change = ItemRef("sub")
    body = ItemRef("body")
    r = ReactEvery(change, body)
    assert len(nu.tree.children(r)) == 2


# ---------------------------------------------------------------------------
# Law validation: a Control driving a mutating body validates.
# Structural; no substrate needed.
# ---------------------------------------------------------------------------


class _Sensor(Shape):
    n = IntRef.slot()


def _validate(term: object) -> None:
    validate(compile(term))  # raises ValidationError on any failure


def test_react_every_validates_with_mutating_body():
    _validate(ReactEvery(_Sensor.n.on_change(), _Sensor.n.set(_Sensor.n + 1)))


def test_react_every_sync_thunk_raises():
    change = ItemRef("sub")
    body = ItemRef("body")
    r = ReactEvery(change, body)
    thunk = r._compile(0, ())
    with pytest.raises(RuntimeError, match="async"):
        thunk(None)
