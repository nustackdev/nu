"""Tests for arithmetic ops.

Unary: NegOp, AbsOp, PosOp
Binary: AddOp, SubOp, MulOp, DivOp, FloorDivOp, ModOp, PowOp

All pure ops. TypeError -> INVALID per error propagation guide.
ZeroDivisionError raises (not caught - logic bug, not composition problem).
"""

from __future__ import annotations

import nu

import pytest
from hypothesis import given
from hypothesis import strategies as st

from nu import Context
from nu.ops import (
    AbsOp,
    AddOp,
    DivOp,
    FloorDivOp,
    ModOp,
    MulOp,
    NegOp,
    PosOp,
    PowOp,
    SubOp,
)
# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

numbers = st.one_of(
    st.integers(min_value=-10000, max_value=10000), st.floats(allow_nan=False, allow_infinity=False)
)
ints = st.integers(min_value=-10000, max_value=10000)
nonzero = st.one_of(
    st.integers(min_value=1, max_value=10000),
    st.integers(min_value=-10000, max_value=-1),
)
small_ints = st.integers(min_value=-100, max_value=100)
small_pos = st.integers(min_value=0, max_value=10)


# ---------------------------------------------------------------------------
# Mathematical properties via hypothesis
# ---------------------------------------------------------------------------


@given(a=numbers, b=numbers)
async def test_add_commutative(a, b):
    ctx = Context()
    r1 = await AddOp(a, b).first(ctx)
    r2 = await AddOp(b, a).first(ctx)
    assert r1 == r2


@given(a=numbers, b=numbers)
async def test_mul_commutative(a, b):
    ctx = Context()
    r1 = await MulOp(a, b).first(ctx)
    r2 = await MulOp(b, a).first(ctx)
    assert r1 == r2


@given(a=numbers)
async def test_add_identity(a):
    ctx = Context()
    assert await AddOp(a, 0).first(ctx) == a


@given(a=numbers)
async def test_mul_identity(a):
    ctx = Context()
    assert await MulOp(a, 1).first(ctx) == a


@given(a=numbers)
async def test_neg_involution(a):
    """Double negation returns original."""
    ctx = Context()
    result = await NegOp(NegOp(a)).first(ctx)
    assert result == a


@given(a=numbers)
async def test_sub_self_is_zero(a):
    ctx = Context()
    assert await SubOp(a, a).first(ctx) == 0


@given(a=ints, b=nonzero)
async def test_div_mul_inverse(a, b):
    """a == (a / b) * b for integers (using floor div)."""
    ctx = Context()
    q = await FloorDivOp(a, b).first(ctx)
    r = await ModOp(a, b).first(ctx)
    assert q * b + r == a


@given(a=small_ints)
async def test_abs_non_negative(a):
    ctx = Context()
    result = await AbsOp(a).first(ctx)
    assert result >= 0 # type: ignore


@given(a=small_ints, b=small_pos)
async def test_pow_matches_python(a, b):
    ctx = Context()
    assert await PowOp(a, b).first(ctx) == a**b


# ---------------------------------------------------------------------------
# Correct computation - explicit edge cases
# ---------------------------------------------------------------------------


async def test_add_strings(ctx):
    """String concatenation via AddOp."""
    assert await AddOp("hello ", "world").first(ctx) == "hello world"


async def test_mul_string_repeat(ctx):
    """String repetition via MulOp."""
    assert await MulOp("ab", 3).first(ctx) == "ababab"


async def test_div_returns_float(ctx):
    assert await DivOp(7, 2).first(ctx) == 3.5


async def test_floor_div_truncates(ctx):
    assert await FloorDivOp(7, 2).first(ctx) == 3


async def test_floor_div_negative(ctx):
    assert await FloorDivOp(-7, 2).first(ctx) == -4


# ---------------------------------------------------------------------------
# Exceptions raise (Ops don't catch, per empty propagation guide)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("op_cls", [NegOp, AbsOp, PosOp])
async def test_unary_type_error_raises(ctx, op_cls):
    with pytest.raises(TypeError):
        await op_cls("not_a_number").first(ctx)


@pytest.mark.parametrize(
    "op_cls, left, right",
    [
        (AddOp, "hello", 3),
        (SubOp, "hello", 3),
        (MulOp, "hello", "world"),
        (DivOp, "hello", 3),
        (FloorDivOp, "hello", 3),
        (ModOp, "hello", 3),
        (PowOp, "hello", 3),
    ],
)
async def test_binary_type_error_raises(ctx, op_cls, left, right):
    with pytest.raises(TypeError):
        await op_cls(left, right).first(ctx)


@pytest.mark.parametrize("op_cls", [DivOp, FloorDivOp, ModOp])
async def test_division_by_zero_raises(ctx, op_cls):
    with pytest.raises(ZeroDivisionError):
        await op_cls(1, 0).first(ctx)
