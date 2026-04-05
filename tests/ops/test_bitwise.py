"""Tests for bitwise ops.

Unary: BitwiseNotOp
Binary: BitwiseAndOp, BitwiseOrOp, XorOp, LShiftOp, RShiftOp

All Calculations (pure). TypeError -> INVALID.
"""

from __future__ import annotations

import pytest
from hypothesis import given
from hypothesis import strategies as st

from nu import Context
from nu.ops.bitwise import BitwiseAndOp, BitwiseNotOp, BitwiseOrOp, LShiftOp, RShiftOp, XorOp


ints = st.integers(min_value=-10000, max_value=10000)
pos_ints = st.integers(min_value=0, max_value=10000)
small_shifts = st.integers(min_value=0, max_value=16)


# ---------------------------------------------------------------------------
# Properties via hypothesis
# ---------------------------------------------------------------------------


@given(a=ints, b=ints)
async def test_and_commutative(a, b):
    ctx = Context()
    r1 = await BitwiseAndOp(a, b).execute(ctx)
    r2 = await BitwiseAndOp(b, a).execute(ctx)
    assert r1 == r2


@given(a=ints, b=ints)
async def test_or_commutative(a, b):
    ctx = Context()
    r1 = await BitwiseOrOp(a, b).execute(ctx)
    r2 = await BitwiseOrOp(b, a).execute(ctx)
    assert r1 == r2


@given(a=ints, b=ints)
async def test_xor_commutative(a, b):
    ctx = Context()
    r1 = await XorOp(a, b).execute(ctx)
    r2 = await XorOp(b, a).execute(ctx)
    assert r1 == r2


@given(a=ints)
async def test_xor_self_is_zero(a):
    ctx = Context()
    assert await XorOp(a, a).execute(ctx) == 0


@given(a=ints)
async def test_not_involution(a):
    """~~a == a."""
    ctx = Context()
    assert await BitwiseNotOp(BitwiseNotOp(a)).execute(ctx) == a


@given(a=pos_ints, n=small_shifts)
async def test_lshift_rshift_inverse(a, n):
    """(a << n) >> n == a for non-negative a."""
    ctx = Context()
    shifted = await LShiftOp(a, n).execute(ctx)
    back = await RShiftOp(shifted, n).execute(ctx)
    assert back == a


# ---------------------------------------------------------------------------
# Explicit cases
# ---------------------------------------------------------------------------


async def test_and_basic(ctx):
    assert await BitwiseAndOp(0b1100, 0b1010).execute(ctx) == 0b1000


async def test_or_basic(ctx):
    assert await BitwiseOrOp(0b1100, 0b1010).execute(ctx) == 0b1110


async def test_xor_basic(ctx):
    assert await XorOp(0b1100, 0b1010).execute(ctx) == 0b0110


async def test_not_basic(ctx):
    assert await BitwiseNotOp(0).execute(ctx) == -1


async def test_lshift_basic(ctx):
    assert await LShiftOp(1, 4).execute(ctx) == 16


async def test_rshift_basic(ctx):
    assert await RShiftOp(16, 4).execute(ctx) == 1


# ---------------------------------------------------------------------------
# TypeError raises
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "op_cls",
    [BitwiseAndOp, BitwiseOrOp, XorOp, LShiftOp, RShiftOp],
)
async def test_binary_type_error_raises(ctx, op_cls):
    with pytest.raises(TypeError):
        await op_cls("hello", 3).execute(ctx)


async def test_unary_type_error_raises(ctx):
    with pytest.raises(TypeError):
        await BitwiseNotOp("hello").execute(ctx)
