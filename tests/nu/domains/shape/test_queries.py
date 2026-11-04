"""Tests for shape fabric read queries.

Covers class hierarchy, construction, and compile-time thunk behavior using a
minimal mock runtime. Full integration (real substrate + program) is deferred.
"""

from __future__ import annotations

import pytest

import nu
from nu.domains.shape.interactions import (
    AdvanceCursor,
    Exists,
    Extract,
    Load,
)
from nu.domains.shape.item import ItemRef
from nu.lang import NULL, ScalarQuery, is_null


# ---------------------------------------------------------------------------
# Class hierarchy
# ---------------------------------------------------------------------------


def test_load_query_is_scalar_query():
    assert issubclass(Load, ScalarQuery)


def test_exists_query_is_scalar_query():
    assert issubclass(Exists, ScalarQuery)


def test_extract_query_is_scalar_query():
    assert issubclass(Extract, ScalarQuery)


def test_advance_cursor_query_is_scalar_query():
    assert issubclass(AdvanceCursor, ScalarQuery)


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------


def test_load_query_constructs_with_ref():
    ref = ItemRef("slot")
    q = Load(ref)
    assert nu.tree.children(q)


def test_exists_query_constructs_with_ref():
    ref = ItemRef("slot")
    q = Exists(ref)
    assert nu.tree.children(q)


def test_extract_query_constructs_with_ref():
    ref = ItemRef("slot")
    q = Extract(ref)
    assert nu.tree.children(q)


def test_advance_cursor_query_constructs_with_two_children():
    source = ItemRef("src")
    cursor = ItemRef("cur")
    q = AdvanceCursor(source, cursor)
    assert len(nu.tree.children(q)) == 2


# ---------------------------------------------------------------------------
# Thunk logic — minimal mock runtime
# ---------------------------------------------------------------------------


def _make_thunk(value):
    """Return a callable that returns ``value`` regardless of runtime arg."""

    def thunk(rt):
        return value

    return thunk


def test_exists_thunk_true_for_real_value():
    q = Exists(ItemRef("x"))
    thunk = q._compile(0, (_make_thunk(42),))
    assert thunk(None) is True


def test_exists_thunk_false_for_empty():
    q = Exists(ItemRef("x"))
    thunk = q._compile(0, (_make_thunk(NULL),))
    assert thunk(None) is False


def test_load_thunk_passes_through_value():
    q = Load(ItemRef("x"))
    thunk = q._compile(0, (_make_thunk("result"),))
    assert thunk(None) == "result"


@pytest.mark.skip(reason="substrate impl deferred — Extract needs view.extract()")
def test_extract_thunk_calls_extract():
    pass


# ---------------------------------------------------------------------------
# Extract sentinel identity (#9 — v1 parity)
# ---------------------------------------------------------------------------


def test_extract_thunk_returns_empty_for_empty_view():
    from nu.lang.sentinels import NULL

    q = Extract(ItemRef("x"))
    thunk = q._compile(0, (_make_thunk(NULL),))
    result = thunk(None)
    assert is_null(result)


@pytest.mark.skip(reason="substrate impl deferred — AdvanceCursor needs view.next_key_after()")
def test_advance_cursor_thunk_reads_next_key():
    pass


class _HookRef(ItemRef):
    """A ref that answers existence itself, the way a lazy view does."""

    def _exists(self, rt, nid):
        rt.seen.append(nid)
        return 1

    async def _aexists(self, rt, nid):
        rt.seen.append(nid)
        return 0


def _hook_rt():
    from types import SimpleNamespace

    return SimpleNamespace(program=SimpleNamespace(children={0: (7,)}), seen=[])


def test_exists_dispatches_to_the_ref_hook_over_the_read():
    rt = _hook_rt()
    thunk = Exists(_HookRef("x"))._compile(0, (_make_thunk(NULL),))
    assert thunk(rt) is True
    assert rt.seen == [7]


def test_exists_async_dispatches_to_the_async_hook():
    import asyncio

    rt = _hook_rt()
    athunk = Exists(_HookRef("x"))._acompile(0, (_make_thunk(42),))
    assert asyncio.run(athunk(rt)) is False
    assert rt.seen == [7]
