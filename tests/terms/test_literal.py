"""Tests for Literal - the irreducible atom.

Literal is the leaf that bottoms out recursion. It stores a Python
literal and returns it on execute. No children, always pure.
"""

from __future__ import annotations

from nu import EMPTY, INVALID, Literal


# ---------------------------------------------------------------------------
# Execute
# ---------------------------------------------------------------------------


async def test_execute_returns_int(ctx):
    assert await Literal(42).execute(ctx) == 42


async def test_execute_returns_str(ctx):
    assert await Literal("hello").execute(ctx) == "hello"


async def test_execute_returns_none(ctx):
    assert await Literal(None).execute(ctx) is None


async def test_execute_returns_list(ctx):
    assert await Literal([1, 2, 3]).execute(ctx) == [1, 2, 3]


async def test_execute_returns_dict(ctx):
    assert await Literal({"a": 1}).execute(ctx) == {"a": 1}


async def test_execute_holds_sentinel(ctx):
    """Literal stores sentinels as literals - it does not propagate them."""
    result = await Literal(EMPTY).execute(ctx)
    assert result is EMPTY


async def test_execute_holds_invalid(ctx):
    result = await Literal(INVALID).execute(ctx)
    assert result is INVALID


# ---------------------------------------------------------------------------
# Structure
# ---------------------------------------------------------------------------


def test_is_leaf():
    assert Literal(42).is_leaf is True
    assert Literal(42).child_count == 0
    assert Literal(42).children == ()


# ---------------------------------------------------------------------------
# Repr
# ---------------------------------------------------------------------------


def test_repr():
    assert repr(Literal(42)) == "Literal(42)"
    assert repr(Literal("hi")) == "Literal('hi')"
