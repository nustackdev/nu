"""Tests for bitwise ops.

Unary: BitwiseNotOp
Binary: BitwiseAndOp, BitwiseOrOp, XorOp, LShiftOp, RShiftOp

All pure ops. TypeError -> INVALID.
"""

from __future__ import annotations

import nu

import pytest
from hypothesis import given
from hypothesis import strategies as st

from nu import Context
from nu.ops import BitwiseAndOp, BitwiseNotOp, BitwiseOrOp, LShiftOp, RShiftOp, XorOp


ints = st.integers(min_value=-10000, max_value=10000)
pos_ints = st.integers(min_value=0, max_value=10000)
small_shifts = st.integers(min_value=0, max_value=16)


# ---------------------------------------------------------------------------
# Properties via hypothesis
# ---------------------------------------------------------------------------


@given(a=ints, b=ints)
async def test_and_commutative(a, b):
    ctx = Context()
    r1 = await nu.first(BitwiseAndOp(a, b), ctx)
    r2 = await nu.first(BitwiseAndOp(b, a), ctx)
    assert r1 == r2


@given(a=ints, b=ints)
async def test_or_commutative(a, b):
    ctx = Context()
    r1 = await nu.first(BitwiseOrOp(a, b), ctx)
    r2 = await nu.first(BitwiseOrOp(b, a), ctx)
    assert r1 == r2


@given(a=ints, b=ints)
async def test_xor_commutative(a, b):
    ctx = Context()
    r1 = await nu.first(XorOp(a, b), ctx)
    r2 = await nu.first(XorOp(b, a), ctx)
    assert r1 == r2


@given(a=ints)
async def test_xor_self_is_zero(a):
    ctx = Context()
    assert await nu.first(XorOp(a, a), ctx) == 0


@given(a=ints)
async def test_not_involution(a):
    """~~a == a."""
    ctx = Context()
    assert await nu.first(BitwiseNotOp(BitwiseNotOp(a)), ctx) == a


@given(a=pos_ints, n=small_shifts)
async def test_lshift_rshift_inverse(a, n):
    """(a << n) >> n == a for non-negative a."""
    ctx = Context()
    shifted = await nu.first(LShiftOp(a, n), ctx)
    back = await nu.first(RShiftOp(shifted, n), ctx)
    assert back == a


# ---------------------------------------------------------------------------
# Explicit cases
# ---------------------------------------------------------------------------


async def test_and_basic(ctx):
    assert await nu.first(BitwiseAndOp(0b1100, 0b1010), ctx) == 0b1000


async def test_or_basic(ctx):
    assert await nu.first(BitwiseOrOp(0b1100, 0b1010), ctx) == 0b1110


async def test_xor_basic(ctx):
    assert await nu.first(XorOp(0b1100, 0b1010), ctx) == 0b0110


async def test_not_basic(ctx):
    assert await nu.first(BitwiseNotOp(0), ctx) == -1


async def test_lshift_basic(ctx):
    assert await nu.first(LShiftOp(1, 4), ctx) == 16


async def test_rshift_basic(ctx):
    assert await nu.first(RShiftOp(16, 4), ctx) == 1


# ---------------------------------------------------------------------------
# TypeError raises
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "op_cls",
    [BitwiseAndOp, BitwiseOrOp, XorOp, LShiftOp, RShiftOp],
)
async def test_binary_type_error_raises(ctx, op_cls):
    with pytest.raises(TypeError):
        await nu.first(op_cls("hello", 3), ctx)


async def test_unary_type_error_raises(ctx):
    with pytest.raises(TypeError):
        await nu.first(BitwiseNotOp("hello"), ctx)
