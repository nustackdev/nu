"""Tests for Literal - the irreducible atom.

Literal is the leaf that bottoms out recursion. It stores a Python
literal and yields it once on open. No children, always pure.
"""

from __future__ import annotations

from nu import EMPTY, INVALID, Literal, runtime


# ---------------------------------------------------------------------------
# Open / first
# ---------------------------------------------------------------------------


async def test_first_returns_int(ctx):
    assert await runtime.afirst(Literal(42), ctx) == 42


async def test_first_returns_str(ctx):
    assert await runtime.afirst(Literal("hello"), ctx) == "hello"


async def test_first_returns_none(ctx):
    assert await runtime.afirst(Literal(None), ctx) is None


async def test_first_returns_list(ctx):
    assert await runtime.afirst(Literal([1, 2, 3]), ctx) == [1, 2, 3]


async def test_first_returns_dict(ctx):
    assert await runtime.afirst(Literal({"a": 1}), ctx) == {"a": 1}


async def test_first_holds_sentinel(ctx):
    """Literal stores sentinels as literals - it does not propagate them."""
    result = await runtime.afirst(Literal(EMPTY), ctx)
    assert result is EMPTY


async def test_first_holds_invalid(ctx):
    result = await runtime.afirst(Literal(INVALID), ctx)
    assert result is INVALID


# ---------------------------------------------------------------------------
# Structure
# ---------------------------------------------------------------------------


def test_is_leaf():
    assert Literal(42)._children == ()
    assert len(Literal(42)._children) == 0


# ---------------------------------------------------------------------------
# Repr
# ---------------------------------------------------------------------------


def test_repr():
    assert repr(Literal(42)) == "Literal(42)"
    assert repr(Literal("hi")) == "Literal('hi')"
