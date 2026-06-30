"""Tests for comparison ops.

Binary: Eq, Ne, Gt, Ge, Lt, Le, IdComp

All pure ops. TypeError -> INVALID.
"""

from __future__ import annotations

import pytest
from hypothesis import given
from hypothesis import strategies as st

from nu import Context, Literal, runtime
from nu import Eq, Ge, Gt, IdComp, Le, Lt, Ne


ints = st.integers(min_value=-10000, max_value=10000)


# ---------------------------------------------------------------------------
# Properties via hypothesis
# ---------------------------------------------------------------------------


@given(a=ints)
async def test_eq_reflexive(a):
    ctx = Context()
    assert await runtime.afirst(Eq(a, a), ctx) is True


@given(a=ints, b=ints)
async def test_eq_symmetric(a, b):
    ctx = Context()
    r1 = await runtime.afirst(Eq(a, b), ctx)
    r2 = await runtime.afirst(Eq(b, a), ctx)
    assert r1 == r2


@given(a=ints, b=ints)
async def test_ne_is_not_eq(a, b):
    ctx = Context()
    eq = await runtime.afirst(Eq(a, b), ctx)
    ne = await runtime.afirst(Ne(a, b), ctx)
    assert eq != ne


@given(a=ints, b=ints)
async def test_gt_lt_inverse(a, b):
    """a > b iff b < a."""
    ctx = Context()
    gt = await runtime.afirst(Gt(a, b), ctx)
    lt = await runtime.afirst(Lt(b, a), ctx)
    assert gt == lt


@given(a=ints, b=ints)
async def test_ge_le_inverse(a, b):
    """a >= b iff b <= a."""
    ctx = Context()
    ge = await runtime.afirst(Ge(a, b), ctx)
    le = await runtime.afirst(Le(b, a), ctx)
    assert ge == le


@given(a=ints)
async def test_ge_reflexive(a):
    ctx = Context()
    assert await runtime.afirst(Ge(a, a), ctx) is True


@given(a=ints)
async def test_le_reflexive(a):
    ctx = Context()
    assert await runtime.afirst(Le(a, a), ctx) is True


# ---------------------------------------------------------------------------
# Explicit cases
# ---------------------------------------------------------------------------


async def test_gt_true(ctx):
    assert await runtime.afirst(Gt(5, 3), ctx) is True


async def test_gt_false(ctx):
    assert await runtime.afirst(Gt(3, 5), ctx) is False


async def test_lt_true(ctx):
    assert await runtime.afirst(Lt(3, 5), ctx) is True


async def test_eq_different(ctx):
    assert await runtime.afirst(Eq(3, 5), ctx) is False


# ---------------------------------------------------------------------------
# IdComp - identity, not equality
# ---------------------------------------------------------------------------


async def test_id_comp_same_object(ctx):
    obj = object()
    assert await runtime.afirst(IdComp(Literal(obj), Literal(obj)), ctx) is True


async def test_id_comp_equal_but_different(ctx):
    """Equal values but different objects."""
    a = [1, 2, 3]
    b = [1, 2, 3]
    assert await runtime.afirst(IdComp(Literal(a), Literal(b)), ctx) is False


# ---------------------------------------------------------------------------
# TypeError raises
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("op_cls", [Gt, Lt, Ge, Le])
async def test_type_error_raises(ctx, op_cls):
    with pytest.raises(TypeError):
        await runtime.afirst(op_cls("hello", 3), ctx)
