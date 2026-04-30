"""Tests for arithmetic ops.

Unary: Neg, Abs, Pos
Binary: Add, Sub, Mul, Div, FloorDiv, Mod, Pow

All pure ops. TypeError -> INVALID per error propagation guide.
ZeroDivisionError raises (not caught - logic bug, not composition problem).
"""

from __future__ import annotations

import pytest
from hypothesis import given
from hypothesis import strategies as st

from nu import Context, runtime
from nu import (
    Abs,
    Add,
    Div,
    FloorDiv,
    Mod,
    Mul,
    Neg,
    Pos,
    Pow,
    Sub,
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
    r1 = await runtime.afirst(Add(a, b), ctx)
    r2 = await runtime.afirst(Add(b, a), ctx)
    assert r1 == r2


@given(a=numbers, b=numbers)
async def test_mul_commutative(a, b):
    ctx = Context()
    r1 = await runtime.afirst(Mul(a, b), ctx)
    r2 = await runtime.afirst(Mul(b, a), ctx)
    assert r1 == r2


@given(a=numbers)
async def test_add_identity(a):
    ctx = Context()
    assert await runtime.afirst(Add(a, 0), ctx) == a


@given(a=numbers)
async def test_mul_identity(a):
    ctx = Context()
    assert await runtime.afirst(Mul(a, 1), ctx) == a


@given(a=numbers)
async def test_neg_involution(a):
    """Double negation returns original."""
    ctx = Context()
    result = await runtime.afirst(Neg(Neg(a)), ctx)
    assert result == a


@given(a=numbers)
async def test_sub_self_is_zero(a):
    ctx = Context()
    assert await runtime.afirst(Sub(a, a), ctx) == 0


@given(a=ints, b=nonzero)
async def test_div_mul_inverse(a, b):
    """a == (a / b) * b for integers (using floor div)."""
    ctx = Context()
    q = await runtime.afirst(FloorDiv(a, b), ctx)
    r = await runtime.afirst(Mod(a, b), ctx)
    assert q * b + r == a


@given(a=small_ints)
async def test_abs_non_negative(a):
    ctx = Context()
    result = await runtime.afirst(Abs(a), ctx)
    assert result >= 0  # type: ignore


@given(a=small_ints, b=small_pos)
async def test_pow_matches_python(a, b):
    ctx = Context()
    assert await runtime.afirst(Pow(a, b), ctx) == a**b


# ---------------------------------------------------------------------------
# Correct computation - explicit edge cases
# ---------------------------------------------------------------------------


async def test_add_strings(ctx):
    """String concatenation via Add."""
    assert await runtime.afirst(Add("hello ", "world"), ctx) == "hello world"


async def test_mul_string_repeat(ctx):
    """String repetition via Mul."""
    assert await runtime.afirst(Mul("ab", 3), ctx) == "ababab"


async def test_div_returns_float(ctx):
    assert await runtime.afirst(Div(7, 2), ctx) == 3.5


async def test_floor_div_truncates(ctx):
    assert await runtime.afirst(FloorDiv(7, 2), ctx) == 3


async def test_floor_div_negative(ctx):
    assert await runtime.afirst(FloorDiv(-7, 2), ctx) == -4


# ---------------------------------------------------------------------------
# Exceptions raise (Ops don't catch, per empty propagation guide)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("op_cls", [Neg, Abs, Pos])
async def test_unary_type_error_raises(ctx, op_cls):
    with pytest.raises(TypeError):
        await runtime.afirst(op_cls("not_a_number"), ctx)


@pytest.mark.parametrize(
    "op_cls, left, right",
    [
        (Add, "hello", 3),
        (Sub, "hello", 3),
        (Mul, "hello", "world"),
        (Div, "hello", 3),
        (FloorDiv, "hello", 3),
        (Mod, "hello", 3),
        (Pow, "hello", 3),
    ],
)
async def test_binary_type_error_raises(ctx, op_cls, left, right):
    with pytest.raises(TypeError):
        await runtime.afirst(op_cls(left, right), ctx)


@pytest.mark.parametrize("op_cls", [Div, FloorDiv, Mod])
async def test_division_by_zero_raises(ctx, op_cls):
    with pytest.raises(ZeroDivisionError):
        await runtime.afirst(op_cls(1, 0), ctx)
