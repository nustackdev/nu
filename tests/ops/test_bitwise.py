"""Tests for bitwise ops.

Unary: BitwiseNot
Binary: BitwiseAnd, BitwiseOr, Xor, LShift, RShift

All pure ops. TypeError -> INVALID.
"""

from __future__ import annotations

import pytest
from hypothesis import given
from hypothesis import strategies as st

from nu import Context
from nu.interactions import BitwiseAnd, BitwiseNot, BitwiseOr, LShift, RShift, Xor


ints = st.integers(min_value=-10000, max_value=10000)
pos_ints = st.integers(min_value=0, max_value=10000)
small_shifts = st.integers(min_value=0, max_value=16)


# ---------------------------------------------------------------------------
# Properties via hypothesis
# ---------------------------------------------------------------------------


@given(a=ints, b=ints)
async def test_and_commutative(a, b):
    ctx = Context()
    r1 = await BitwiseAnd(a, b).first(ctx)
    r2 = await BitwiseAnd(b, a).first(ctx)
    assert r1 == r2


@given(a=ints, b=ints)
async def test_or_commutative(a, b):
    ctx = Context()
    r1 = await BitwiseOr(a, b).first(ctx)
    r2 = await BitwiseOr(b, a).first(ctx)
    assert r1 == r2


@given(a=ints, b=ints)
async def test_xor_commutative(a, b):
    ctx = Context()
    r1 = await Xor(a, b).first(ctx)
    r2 = await Xor(b, a).first(ctx)
    assert r1 == r2


@given(a=ints)
async def test_xor_self_is_zero(a):
    ctx = Context()
    assert await Xor(a, a).first(ctx) == 0


@given(a=ints)
async def test_not_involution(a):
    """~~a == a."""
    ctx = Context()
    assert await BitwiseNot(BitwiseNot(a)).first(ctx) == a


@given(a=pos_ints, n=small_shifts)
async def test_lshift_rshift_inverse(a, n):
    """(a << n) >> n == a for non-negative a."""
    ctx = Context()
    shifted = await LShift(a, n).first(ctx)
    back = await RShift(shifted, n).first(ctx)
    assert back == a


# ---------------------------------------------------------------------------
# Explicit cases
# ---------------------------------------------------------------------------


async def test_and_basic(ctx):
    assert await BitwiseAnd(0b1100, 0b1010).first(ctx) == 0b1000


async def test_or_basic(ctx):
    assert await BitwiseOr(0b1100, 0b1010).first(ctx) == 0b1110


async def test_xor_basic(ctx):
    assert await Xor(0b1100, 0b1010).first(ctx) == 0b0110


async def test_not_basic(ctx):
    assert await BitwiseNot(0).first(ctx) == -1


async def test_lshift_basic(ctx):
    assert await LShift(1, 4).first(ctx) == 16


async def test_rshift_basic(ctx):
    assert await RShift(16, 4).first(ctx) == 1


# ---------------------------------------------------------------------------
# TypeError raises
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "op_cls",
    [BitwiseAnd, BitwiseOr, Xor, LShift, RShift],
)
async def test_binary_type_error_raises(ctx, op_cls):
    with pytest.raises(TypeError):
        await op_cls("hello", 3).first(ctx)


async def test_unary_type_error_raises(ctx):
    with pytest.raises(TypeError):
        await BitwiseNot("hello").first(ctx)
