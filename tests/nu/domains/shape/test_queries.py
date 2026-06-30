"""Tests for shape fabric read queries.

Covers class hierarchy, construction, and compile-time thunk behavior using a
minimal mock runtime. Full integration (real substrate + program) is deferred.
"""

from __future__ import annotations

import pytest

from nu.domains.shape.interactions import (
    AdvanceCursorQuery,
    ExistsQuery,
    ExtractQuery,
    LoadQuery,
    MissingQuery,
)
from nu.domains.shape.refs.item import ItemRef
from nu.lang import ScalarQuery
from nu.lang.sentinels import EMPTY, INVALID


# ---------------------------------------------------------------------------
# Class hierarchy
# ---------------------------------------------------------------------------


def test_load_query_is_scalar_query():
    assert issubclass(LoadQuery, ScalarQuery)


def test_exists_query_is_scalar_query():
    assert issubclass(ExistsQuery, ScalarQuery)


def test_missing_query_is_scalar_query():
    assert issubclass(MissingQuery, ScalarQuery)


def test_extract_query_is_scalar_query():
    assert issubclass(ExtractQuery, ScalarQuery)


def test_advance_cursor_query_is_scalar_query():
    assert issubclass(AdvanceCursorQuery, ScalarQuery)


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------


def test_load_query_constructs_with_ref():
    ref = ItemRef("slot")
    q = LoadQuery(ref)
    assert q.children


def test_exists_query_constructs_with_ref():
    ref = ItemRef("slot")
    q = ExistsQuery(ref)
    assert q.children


def test_missing_query_constructs_with_ref():
    ref = ItemRef("slot")
    q = MissingQuery(ref)
    assert q.children


def test_extract_query_constructs_with_ref():
    ref = ItemRef("slot")
    q = ExtractQuery(ref)
    assert q.children


def test_advance_cursor_query_constructs_with_two_children():
    source = ItemRef("src")
    cursor = ItemRef("cur")
    q = AdvanceCursorQuery(source, cursor)
    assert len(q.children) == 2


# ---------------------------------------------------------------------------
# Thunk logic — minimal mock runtime
# ---------------------------------------------------------------------------


def _make_thunk(value):
    """Return a callable that returns ``value`` regardless of runtime arg."""

    def thunk(rt):
        return value

    return thunk


def test_exists_thunk_true_for_real_value():
    q = ExistsQuery(ItemRef("x"))
    thunk = q.compile(0, (_make_thunk(42),))
    assert thunk(None) is True


def test_exists_thunk_false_for_empty():
    q = ExistsQuery(ItemRef("x"))
    thunk = q.compile(0, (_make_thunk(EMPTY),))
    assert thunk(None) is False


def test_exists_thunk_false_for_invalid():
    q = ExistsQuery(ItemRef("x"))
    thunk = q.compile(0, (_make_thunk(INVALID),))
    assert thunk(None) is False


def test_missing_thunk_true_for_empty():
    q = MissingQuery(ItemRef("x"))
    thunk = q.compile(0, (_make_thunk(EMPTY),))
    assert thunk(None) is True


def test_missing_thunk_false_for_real_value():
    q = MissingQuery(ItemRef("x"))
    thunk = q.compile(0, (_make_thunk("hello"),))
    assert thunk(None) is False


def test_load_thunk_passes_through_value():
    q = LoadQuery(ItemRef("x"))
    thunk = q.compile(0, (_make_thunk("result"),))
    assert thunk(None) == "result"


@pytest.mark.skip(reason="substrate impl deferred — ExtractQuery needs view.extract()")
def test_extract_thunk_calls_extract():
    pass


# ---------------------------------------------------------------------------
# ExtractQuery sentinel identity (#9 — v1 parity)
# ---------------------------------------------------------------------------


def test_extract_thunk_returns_empty_for_empty_view():
    from nu.lang.sentinels import EMPTY

    q = ExtractQuery(ItemRef("x"))
    thunk = q.compile(0, (_make_thunk(EMPTY),))
    result = thunk(None)
    # v1 parity: preserve the sentinel identity — EMPTY stays EMPTY, not INVALID
    assert result is EMPTY


def test_extract_thunk_returns_invalid_for_invalid_view():
    from nu.lang.sentinels import INVALID

    q = ExtractQuery(ItemRef("x"))
    thunk = q.compile(0, (_make_thunk(INVALID),))
    result = thunk(None)
    assert result is INVALID


@pytest.mark.skip(reason="substrate impl deferred — AdvanceCursorQuery needs view.next_key_after()")
def test_advance_cursor_thunk_reads_next_key():
    pass
