"""Tests for Value - the irreducible atom.

Value is the leaf that bottoms out recursion. It stores a Python
literal and returns it on execute. No children, always pure.
"""

from __future__ import annotations

from nu import EMPTY, INVALID, Value


# ---------------------------------------------------------------------------
# Execute
# ---------------------------------------------------------------------------


async def test_execute_returns_int(ctx):
    assert await Value(42).execute(ctx) == 42


async def test_execute_returns_str(ctx):
    assert await Value("hello").execute(ctx) == "hello"


async def test_execute_returns_none(ctx):
    assert await Value(None).execute(ctx) is None


async def test_execute_returns_list(ctx):
    assert await Value([1, 2, 3]).execute(ctx) == [1, 2, 3]


async def test_execute_returns_dict(ctx):
    assert await Value({"a": 1}).execute(ctx) == {"a": 1}


async def test_execute_holds_sentinel(ctx):
    """Value stores sentinels as literals - it does not propagate them."""
    result = await Value(EMPTY).execute(ctx)
    assert result is EMPTY


async def test_execute_holds_invalid(ctx):
    result = await Value(INVALID).execute(ctx)
    assert result is INVALID


# ---------------------------------------------------------------------------
# Structure
# ---------------------------------------------------------------------------


def test_is_leaf():
    assert Value(42).is_leaf is True
    assert Value(42).child_count == 0
    assert Value(42).children == ()


# ---------------------------------------------------------------------------
# Purity
# ---------------------------------------------------------------------------


def test_is_self_pure():
    assert Value(42).is_self_pure is True


def test_is_subtree_pure():
    assert Value(42).is_subtree_pure is True


# ---------------------------------------------------------------------------
# Repr
# ---------------------------------------------------------------------------


def test_repr():
    assert repr(Value(42)) == "Value(42)"
    assert repr(Value("hi")) == "Value('hi')"
