"""Tests for shape fabric read queries.

Covers class hierarchy, construction, and compile-time thunk behavior using a
minimal mock runtime. Full integration (real substrate + program) is deferred.
"""

from __future__ import annotations

import pytest

from nu.domains.shape.interactions import (
    AdvanceCursor,
    Exists,
    Extract,
    Load,
    Missing,
)
from nu.domains.shape.refs.item import ItemRef
from nu.lang import ScalarQuery
from nu.lang.sentinels import EMPTY, INVALID


# ---------------------------------------------------------------------------
# Class hierarchy
# ---------------------------------------------------------------------------


def test_load_query_is_scalar_query():
    assert issubclass(Load, ScalarQuery)


def test_exists_query_is_scalar_query():
    assert issubclass(Exists, ScalarQuery)


def test_missing_query_is_scalar_query():
    assert issubclass(Missing, ScalarQuery)


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
    assert q._children


def test_exists_query_constructs_with_ref():
    ref = ItemRef("slot")
    q = Exists(ref)
    assert q._children


def test_missing_query_constructs_with_ref():
    ref = ItemRef("slot")
    q = Missing(ref)
    assert q._children


def test_extract_query_constructs_with_ref():
    ref = ItemRef("slot")
    q = Extract(ref)
    assert q._children


def test_advance_cursor_query_constructs_with_two_children():
    source = ItemRef("src")
    cursor = ItemRef("cur")
    q = AdvanceCursor(source, cursor)
    assert len(q._children) == 2


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
    thunk = q._compile(0, (_make_thunk(EMPTY),))
    assert thunk(None) is False


def test_exists_thunk_false_for_invalid():
    q = Exists(ItemRef("x"))
    thunk = q._compile(0, (_make_thunk(INVALID),))
    assert thunk(None) is False


def test_missing_thunk_true_for_empty():
    q = Missing(ItemRef("x"))
    thunk = q._compile(0, (_make_thunk(EMPTY),))
    assert thunk(None) is True


def test_missing_thunk_false_for_real_value():
    q = Missing(ItemRef("x"))
    thunk = q._compile(0, (_make_thunk("hello"),))
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
    from nu.lang.sentinels import EMPTY

    q = Extract(ItemRef("x"))
    thunk = q._compile(0, (_make_thunk(EMPTY),))
    result = thunk(None)
    # v1 parity: preserve the sentinel identity — EMPTY stays EMPTY, not INVALID
    assert result is EMPTY


def test_extract_thunk_returns_invalid_for_invalid_view():
    from nu.lang.sentinels import INVALID

    q = Extract(ItemRef("x"))
    thunk = q._compile(0, (_make_thunk(INVALID),))
    result = thunk(None)
    assert result is INVALID


@pytest.mark.skip(reason="substrate impl deferred — AdvanceCursor needs view.next_key_after()")
def test_advance_cursor_thunk_reads_next_key():
    pass
