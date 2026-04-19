"""Tests for logical ops.

Unary: NotOp, BoolOp
Binary: AndOp, OrOp (short-circuit evaluation)

AndOp and OrOp override execute() for short-circuit semantics.
Key property: the right operand is NOT evaluated when short-circuit fires.
"""

from __future__ import annotations

import nu

from hypothesis import given
from hypothesis import strategies as st
from tests.conftest import FailingNu

from nu import EMPTY, INVALID, Context, Literal
from nu.ops import AndOp, BoolOp, NotOp, OrOp
from nu.terms.sentinel import is_invalid, is_sentinel


ints = st.integers(min_value=-1000, max_value=1000)


# ---------------------------------------------------------------------------
# NotOp
# ---------------------------------------------------------------------------


@given(a=ints)
async def test_not_involution(a):
    """Double negation restores truthiness."""
    ctx = Context()
    result = await nu.first(NotOp(NotOp(a)), ctx)
    assert result == (not not a)


async def test_not_true(ctx):
    assert await nu.first(NotOp(True), ctx) is False


async def test_not_false(ctx):
    assert await nu.first(NotOp(False), ctx) is True


async def test_not_zero(ctx):
    assert await nu.first(NotOp(0), ctx) is True


async def test_not_nonempty_string(ctx):
    assert await nu.first(NotOp("hello"), ctx) is False


# ---------------------------------------------------------------------------
# BoolOp
# ---------------------------------------------------------------------------


async def test_bool_truthy(ctx):
    assert await nu.first(BoolOp(1), ctx) is True


async def test_bool_falsy(ctx):
    assert await nu.first(BoolOp(0), ctx) is False


async def test_bool_empty_string(ctx):
    assert await nu.first(BoolOp(""), ctx) is False


async def test_bool_nonempty_list(ctx):
    assert await nu.first(BoolOp(Literal([1, 2])), ctx) is True


# ---------------------------------------------------------------------------
# AndOp - short-circuit
# ---------------------------------------------------------------------------


async def test_and_both_truthy(ctx):
    result = await nu.first(AndOp(3, 5), ctx)
    assert result == 5


async def test_and_left_falsy(ctx):
    result = await nu.first(AndOp(0, 5), ctx)
    assert result == 0


async def test_and_right_falsy(ctx):
    result = await nu.first(AndOp(3, 0), ctx)
    assert result == 0


async def test_and_short_circuit_skips_right(ctx):
    """Left is falsy -> right is never evaluated."""
    result = await nu.first(AndOp(Literal(0), FailingNu()), ctx)
    assert result == 0


async def test_and_sentinel_left(ctx):
    """EMPTY left -> INVALID, right not evaluated."""
    result = await nu.first(AndOp(Literal(EMPTY), FailingNu()), ctx)
    assert is_sentinel(result)


async def test_and_sentinel_right(ctx):
    """Clean left, INVALID right -> INVALID."""
    result = await nu.first(AndOp(Literal(3), Literal(INVALID)), ctx)
    assert is_invalid(result)


# ---------------------------------------------------------------------------
# OrOp - short-circuit
# ---------------------------------------------------------------------------


async def test_or_both_truthy(ctx):
    result = await nu.first(OrOp(3, 5), ctx)
    assert result == 3


async def test_or_left_falsy(ctx):
    result = await nu.first(OrOp(0, 5), ctx)
    assert result == 5


async def test_or_both_falsy(ctx):
    result = await nu.first(OrOp(0, ""), ctx)
    assert result == ""


async def test_or_short_circuit_skips_right(ctx):
    """Left is truthy -> right is never evaluated."""
    result = await nu.first(OrOp(Literal(3), FailingNu()), ctx)
    assert result == 3


async def test_or_sentinel_left(ctx):
    """EMPTY left -> INVALID, right not evaluated."""
    result = await nu.first(OrOp(Literal(EMPTY), FailingNu()), ctx)
    assert is_sentinel(result)


async def test_or_sentinel_right(ctx):
    """Falsy left, INVALID right -> INVALID."""
    result = await nu.first(OrOp(Literal(0), Literal(INVALID)), ctx)
    assert is_invalid(result)
