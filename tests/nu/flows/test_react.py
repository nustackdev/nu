"""Tests for reactive control flows: React, ReactWhile, ReactForever.

Construction and class-hierarchy checks run without a substrate. Execution
(subscription binding, async queue drain) is deferred to substrate integration.
"""

from __future__ import annotations

import pytest

from nu.domains.shape.refs.item import ItemRef
from nu.flows.react import React, ReactForever, ReactWhile
from nu.lang import Control, StreamQuery


# ---------------------------------------------------------------------------
# Class hierarchy
# ---------------------------------------------------------------------------


def test_react_is_stream_query():
    assert issubclass(React, StreamQuery)


def test_react_while_is_stream_query():
    assert issubclass(ReactWhile, StreamQuery)


def test_react_forever_is_control():
    assert issubclass(ReactForever, Control)


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------


def test_react_constructs_with_change_only():
    change = ItemRef("sub")
    r = React(change)
    assert r.children  # at least one child


def test_react_constructs_with_body():
    change = ItemRef("sub")
    body = ItemRef("body")
    r = React(change, body)
    assert len(r.children) >= 2


def test_react_while_constructs():
    change = ItemRef("sub")
    cond = ItemRef("cond")
    body = ItemRef("body")
    r = ReactWhile(change, cond, body)
    assert len(r.children) == 3


def test_react_while_constructs_with_changed_key():
    change = ItemRef("sub")
    cond = ItemRef("cond")
    body = ItemRef("body")
    key = ItemRef("k")
    r = ReactWhile(change, cond, body, changed_key=key)
    assert len(r.children) == 4


def test_react_forever_constructs():
    change = ItemRef("sub")
    body = ItemRef("body")
    r = ReactForever(change, body)
    assert len(r.children) == 2


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
    thunk = r.compile(0, ())
    with pytest.raises(RuntimeError, match="async"):
        thunk(None)


def test_react_while_sync_thunk_raises():
    change = ItemRef("sub")
    cond = ItemRef("cond")
    body = ItemRef("body")
    r = ReactWhile(change, cond, body)
    thunk = r.compile(0, ())
    with pytest.raises(RuntimeError, match="async"):
        thunk(None)


def test_react_forever_sync_thunk_raises():
    change = ItemRef("sub")
    body = ItemRef("body")
    r = ReactForever(change, body)
    thunk = r.compile(0, ())
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
