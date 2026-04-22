"""Tests for logical ops.

Unary: Not, Bool
Binary: And, Or (short-circuit evaluation)

And and Or override execute() for short-circuit semantics.
Key property: the right operand is NOT evaluated when short-circuit fires.
"""

from __future__ import annotations

from hypothesis import given
from hypothesis import strategies as st
from tests.conftest import FailingNu

from nu import EMPTY, INVALID, Context, Literal
from nu.interactions import And, Bool, Not, Or
from nu.terms import is_invalid, is_sentinel


ints = st.integers(min_value=-1000, max_value=1000)


# ---------------------------------------------------------------------------
# Not
# ---------------------------------------------------------------------------


@given(a=ints)
async def test_not_involution(a):
    """Double negation restores truthiness."""
    ctx = Context()
    result = await Not(Not(a)).afirst(ctx)
    assert result == (not not a)


async def test_not_true(ctx):
    assert await Not(True).afirst(ctx) is False


async def test_not_false(ctx):
    assert await Not(False).afirst(ctx) is True


async def test_not_zero(ctx):
    assert await Not(0).afirst(ctx) is True


async def test_not_nonempty_string(ctx):
    assert await Not("hello").afirst(ctx) is False


# ---------------------------------------------------------------------------
# Bool
# ---------------------------------------------------------------------------


async def test_bool_truthy(ctx):
    assert await Bool(1).afirst(ctx) is True


async def test_bool_falsy(ctx):
    assert await Bool(0).afirst(ctx) is False


async def test_bool_empty_string(ctx):
    assert await Bool("").afirst(ctx) is False


async def test_bool_nonempty_list(ctx):
    assert await Bool(Literal([1, 2])).afirst(ctx) is True


# ---------------------------------------------------------------------------
# And - short-circuit
# ---------------------------------------------------------------------------


async def test_and_both_truthy(ctx):
    result = await And(3, 5).afirst(ctx)
    assert result == 5


async def test_and_left_falsy(ctx):
    result = await And(0, 5).afirst(ctx)
    assert result == 0


async def test_and_right_falsy(ctx):
    result = await And(3, 0).afirst(ctx)
    assert result == 0


async def test_and_short_circuit_skips_right(ctx):
    """Left is falsy -> right is never evaluated."""
    result = await And(Literal(0), FailingNu()).afirst(ctx)
    assert result == 0


async def test_and_sentinel_left(ctx):
    """EMPTY left -> INVALID, right not evaluated."""
    result = await And(Literal(EMPTY), FailingNu()).afirst(ctx)
    assert is_sentinel(result)


async def test_and_sentinel_right(ctx):
    """Clean left, INVALID right -> INVALID."""
    result = await And(Literal(3), Literal(INVALID)).afirst(ctx)
    assert is_invalid(result)


# ---------------------------------------------------------------------------
# Or - short-circuit
# ---------------------------------------------------------------------------


async def test_or_both_truthy(ctx):
    result = await Or(3, 5).afirst(ctx)
    assert result == 3


async def test_or_left_falsy(ctx):
    result = await Or(0, 5).afirst(ctx)
    assert result == 5


async def test_or_both_falsy(ctx):
    result = await Or(0, "").afirst(ctx)
    assert result == ""


async def test_or_short_circuit_skips_right(ctx):
    """Left is truthy -> right is never evaluated."""
    result = await Or(Literal(3), FailingNu()).afirst(ctx)
    assert result == 3


async def test_or_sentinel_left(ctx):
    """EMPTY left -> INVALID, right not evaluated."""
    result = await Or(Literal(EMPTY), FailingNu()).afirst(ctx)
    assert is_sentinel(result)


async def test_or_sentinel_right(ctx):
    """Falsy left, INVALID right -> INVALID."""
    result = await Or(Literal(0), Literal(INVALID)).afirst(ctx)
    assert is_invalid(result)
