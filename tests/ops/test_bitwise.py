"""Tests for bitwise ops.

Unary: BitwiseNot
Binary: BitwiseAnd, BitwiseOr, Xor, LShift, RShift

All pure ops. TypeError -> INVALID.
"""

from __future__ import annotations

import pytest
from hypothesis import given
from hypothesis import strategies as st

from nu import Context, runtime
from nu import BitwiseAnd, BitwiseNot, BitwiseOr, LShift, RShift, Xor


ints = st.integers(min_value=-10000, max_value=10000)
pos_ints = st.integers(min_value=0, max_value=10000)
small_shifts = st.integers(min_value=0, max_value=16)


# ---------------------------------------------------------------------------
# Properties via hypothesis
# ---------------------------------------------------------------------------


@given(a=ints, b=ints)
async def test_and_commutative(a, b):
    ctx = Context()
    r1 = await runtime.afirst(BitwiseAnd(a, b), ctx)
    r2 = await runtime.afirst(BitwiseAnd(b, a), ctx)
    assert r1 == r2


@given(a=ints, b=ints)
async def test_or_commutative(a, b):
    ctx = Context()
    r1 = await runtime.afirst(BitwiseOr(a, b), ctx)
    r2 = await runtime.afirst(BitwiseOr(b, a), ctx)
    assert r1 == r2


@given(a=ints, b=ints)
async def test_xor_commutative(a, b):
    ctx = Context()
    r1 = await runtime.afirst(Xor(a, b), ctx)
    r2 = await runtime.afirst(Xor(b, a), ctx)
    assert r1 == r2


@given(a=ints)
async def test_xor_self_is_zero(a):
    ctx = Context()
    assert await runtime.afirst(Xor(a, a), ctx) == 0


@given(a=ints)
async def test_not_involution(a):
    """~~a == a."""
    ctx = Context()
    assert await runtime.afirst(BitwiseNot(BitwiseNot(a)), ctx) == a


@given(a=pos_ints, n=small_shifts)
async def test_lshift_rshift_inverse(a, n):
    """(a << n) >> n == a for non-negative a."""
    ctx = Context()
    shifted = await runtime.afirst(LShift(a, n), ctx)
    back = await runtime.afirst(RShift(shifted, n), ctx)
    assert back == a


# ---------------------------------------------------------------------------
# Explicit cases
# ---------------------------------------------------------------------------


async def test_and_basic(ctx):
    assert await runtime.afirst(BitwiseAnd(0b1100, 0b1010), ctx) == 0b1000


async def test_or_basic(ctx):
    assert await runtime.afirst(BitwiseOr(0b1100, 0b1010), ctx) == 0b1110


async def test_xor_basic(ctx):
    assert await runtime.afirst(Xor(0b1100, 0b1010), ctx) == 0b0110


async def test_not_basic(ctx):
    assert await runtime.afirst(BitwiseNot(0), ctx) == -1


async def test_lshift_basic(ctx):
    assert await runtime.afirst(LShift(1, 4), ctx) == 16


async def test_rshift_basic(ctx):
    assert await runtime.afirst(RShift(16, 4), ctx) == 1


# ---------------------------------------------------------------------------
# TypeError raises
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "op_cls",
    [BitwiseAnd, BitwiseOr, Xor, LShift, RShift],
)
async def test_binary_type_error_raises(ctx, op_cls):
    with pytest.raises(TypeError):
        await runtime.afirst(op_cls("hello", 3), ctx)


async def test_unary_type_error_raises(ctx):
    with pytest.raises(TypeError):
        await runtime.afirst(BitwiseNot("hello"), ctx)
