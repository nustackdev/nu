"""Tests for ReactOnce: wait for one change, run the body once."""

from __future__ import annotations

import pytest

import nu
from nu.core.reactive.event import ReactOnce
from nu.domains.shape import Shape
from nu.domains.shape.item import ItemRef
from nu.lang import Control
from nu.lang.helpers import compile, validate
from nustd.kv import IntRef


def test_react_is_control():
    assert issubclass(ReactOnce, Control)


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------


def test_react_constructs_with_change_only():
    change = ItemRef("sub")
    r = ReactOnce(change)
    assert nu.tree.children(r)  # at least one child


def test_react_constructs_with_body():
    change = ItemRef("sub")
    body = ItemRef("body")
    r = ReactOnce(change, body)
    assert len(nu.tree.children(r)) >= 2


def test_react_changed_key_requires_body():
    change = ItemRef("sub")
    key = ItemRef("k")
    with pytest.raises(ValueError, match="changed_key requires a body"):
        ReactOnce(change, changed_key=key)


# ---------------------------------------------------------------------------
# Law validation: a Control driving a mutating body validates.
# Structural; no substrate needed.
# ---------------------------------------------------------------------------


class _Sensor(Shape):
    n = IntRef.slot()


def _validate(term: object) -> None:
    validate(compile(term))  # raises ValidationError on any failure


def test_react_validates_with_mutating_body():
    _validate(ReactOnce(_Sensor.n.on_change(), _Sensor.n.set(_Sensor.n + 1)))


# ---------------------------------------------------------------------------
# Sync compile raises (async-only)
# ---------------------------------------------------------------------------


def test_react_sync_thunk_raises():
    """Sync compile returns a thunk that raises at execution -- matches Race/AnyN.

    Compile itself must succeed so emit_thunks can walk the whole tree; the raise
    only fires if the sync path is actually driven (arun uses acompile).
    """
    change = ItemRef("sub")
    r = ReactOnce(change)
    thunk = r._compile(0, ())
    with pytest.raises(RuntimeError, match="async"):
        thunk(None)


# ---------------------------------------------------------------------------
# Execution deferred
# ---------------------------------------------------------------------------


@pytest.mark.skip(reason="substrate impl deferred: needs asyncio subscription backing store")
async def test_react_fires_on_first_change():
    pass
