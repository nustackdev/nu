"""Tests for comparison ops.

Binary: Eq, Ne, Gt, Ge, Lt, Le, IdComp

All pure ops. TypeError -> INVALID.
"""

from __future__ import annotations

import pytest
from hypothesis import given
from hypothesis import strategies as st

from nu import Context, Literal
from nu.interactions import Eq, Ge, Gt, IdComp, Le, Lt, Ne


ints = st.integers(min_value=-10000, max_value=10000)


# ---------------------------------------------------------------------------
# Properties via hypothesis
# ---------------------------------------------------------------------------


@given(a=ints)
async def test_eq_reflexive(a):
    ctx = Context()
    assert await Eq(a, a).afirst(ctx) is True


@given(a=ints, b=ints)
async def test_eq_symmetric(a, b):
    ctx = Context()
    r1 = await Eq(a, b).afirst(ctx)
    r2 = await Eq(b, a).afirst(ctx)
    assert r1 == r2


@given(a=ints, b=ints)
async def test_ne_is_not_eq(a, b):
    ctx = Context()
    eq = await Eq(a, b).afirst(ctx)
    ne = await Ne(a, b).afirst(ctx)
    assert eq != ne


@given(a=ints, b=ints)
async def test_gt_lt_inverse(a, b):
    """a > b iff b < a."""
    ctx = Context()
    gt = await Gt(a, b).afirst(ctx)
    lt = await Lt(b, a).afirst(ctx)
    assert gt == lt


@given(a=ints, b=ints)
async def test_ge_le_inverse(a, b):
    """a >= b iff b <= a."""
    ctx = Context()
    ge = await Ge(a, b).afirst(ctx)
    le = await Le(b, a).afirst(ctx)
    assert ge == le


@given(a=ints)
async def test_ge_reflexive(a):
    ctx = Context()
    assert await Ge(a, a).afirst(ctx) is True


@given(a=ints)
async def test_le_reflexive(a):
    ctx = Context()
    assert await Le(a, a).afirst(ctx) is True


# ---------------------------------------------------------------------------
# Explicit cases
# ---------------------------------------------------------------------------


async def test_gt_true(ctx):
    assert await Gt(5, 3).afirst(ctx) is True


async def test_gt_false(ctx):
    assert await Gt(3, 5).afirst(ctx) is False


async def test_lt_true(ctx):
    assert await Lt(3, 5).afirst(ctx) is True


async def test_eq_different(ctx):
    assert await Eq(3, 5).afirst(ctx) is False


# ---------------------------------------------------------------------------
# IdComp - identity, not equality
# ---------------------------------------------------------------------------


async def test_id_comp_same_object(ctx):
    obj = object()
    assert await IdComp(Literal(obj), Literal(obj)).afirst(ctx) is True


async def test_id_comp_equal_but_different(ctx):
    """Equal values but different objects."""
    a = [1, 2, 3]
    b = [1, 2, 3]
    assert await IdComp(Literal(a), Literal(b)).afirst(ctx) is False


# ---------------------------------------------------------------------------
# TypeError raises
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("op_cls", [Gt, Lt, Ge, Le])
async def test_type_error_raises(ctx, op_cls):
    with pytest.raises(TypeError):
        await op_cls("hello", 3).afirst(ctx)
