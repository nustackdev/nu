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


def test_react_sync_compile_raises():
    change = ItemRef("sub")
    r = React(change)
    with pytest.raises(NotImplementedError, match="async"):
        r.compile(0, ())


def test_react_while_sync_compile_raises():
    change = ItemRef("sub")
    cond = ItemRef("cond")
    body = ItemRef("body")
    r = ReactWhile(change, cond, body)
    with pytest.raises(NotImplementedError, match="async"):
        r.compile(0, ())


def test_react_forever_sync_compile_raises():
    change = ItemRef("sub")
    body = ItemRef("body")
    r = ReactForever(change, body)
    with pytest.raises(NotImplementedError, match="async"):
        r.compile(0, ())


# ---------------------------------------------------------------------------
# Execution deferred
# ---------------------------------------------------------------------------


@pytest.mark.skip(reason="substrate impl deferred — needs asyncio subscription backing store")
async def test_react_fires_on_first_change():
    pass


@pytest.mark.skip(reason="substrate impl deferred — needs asyncio subscription backing store")
async def test_react_while_stops_when_condition_false():
    pass
