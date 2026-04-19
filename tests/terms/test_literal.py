"""Tests for Literal - the irreducible atom.

Literal is the leaf that bottoms out recursion. It stores a Python
literal and yields it once on open. No children, always pure.
"""

from __future__ import annotations

import nu
from nu import EMPTY, INVALID, Literal


# ---------------------------------------------------------------------------
# Open / first
# ---------------------------------------------------------------------------


async def test_first_returns_int(ctx):
    assert await nu.first(Literal(42), ctx) == 42


async def test_first_returns_str(ctx):
    assert await nu.first(Literal("hello"), ctx) == "hello"


async def test_first_returns_none(ctx):
    assert await nu.first(Literal(None), ctx) is None


async def test_first_returns_list(ctx):
    assert await nu.first(Literal([1, 2, 3]), ctx) == [1, 2, 3]


async def test_first_returns_dict(ctx):
    assert await nu.first(Literal({"a": 1}), ctx) == {"a": 1}


async def test_first_holds_sentinel(ctx):
    """Literal stores sentinels as literals - it does not propagate them."""
    result = await nu.first(Literal(EMPTY), ctx)
    assert result is EMPTY


async def test_first_holds_invalid(ctx):
    result = await nu.first(Literal(INVALID), ctx)
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
