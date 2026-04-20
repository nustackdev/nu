"""Tests for Literal - the irreducible atom.

Literal is the leaf that bottoms out recursion. It stores a Python
literal and yields it once on open. No children, always pure.
"""

from __future__ import annotations

from nu import EMPTY, INVALID, Literal


# ---------------------------------------------------------------------------
# Open / first
# ---------------------------------------------------------------------------


async def test_first_returns_int(ctx):
    assert await Literal(42).first(ctx) == 42


async def test_first_returns_str(ctx):
    assert await Literal("hello").first(ctx) == "hello"


async def test_first_returns_none(ctx):
    assert await Literal(None).first(ctx) is None


async def test_first_returns_list(ctx):
    assert await Literal([1, 2, 3]).first(ctx) == [1, 2, 3]


async def test_first_returns_dict(ctx):
    assert await Literal({"a": 1}).first(ctx) == {"a": 1}


async def test_first_holds_sentinel(ctx):
    """Literal stores sentinels as literals - it does not propagate them."""
    result = await Literal(EMPTY).first(ctx)
    assert result is EMPTY


async def test_first_holds_invalid(ctx):
    result = await Literal(INVALID).first(ctx)
    assert result is INVALID


# ---------------------------------------------------------------------------
# Structure
# ---------------------------------------------------------------------------


def test_is_leaf():
    assert Literal(42)._is_leaf is True
    assert Literal(42)._child_count == 0
    assert Literal(42).children == ()


# ---------------------------------------------------------------------------
# Repr
# ---------------------------------------------------------------------------


def test_repr():
    assert repr(Literal(42)) == "Literal(42)"
    assert repr(Literal("hi")) == "Literal('hi')"
