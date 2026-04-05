"""Tests for comparison ops.

Binary: EqOp, NeOp, GtOp, GeOp, LtOp, LeOp, IdCompOp

All Calculations (pure). TypeError -> INVALID.
"""

from __future__ import annotations

import pytest
from hypothesis import given
from hypothesis import strategies as st

from nu import Context, Value
from nu.ops import EqOp, GeOp, GtOp, IdCompOp, LeOp, LtOp, NeOp


ints = st.integers(min_value=-10000, max_value=10000)


# ---------------------------------------------------------------------------
# Properties via hypothesis
# ---------------------------------------------------------------------------


@given(a=ints)
async def test_eq_reflexive(a):
    ctx = Context()
    assert await EqOp(a, a).execute(ctx) is True


@given(a=ints, b=ints)
async def test_eq_symmetric(a, b):
    ctx = Context()
    r1 = await EqOp(a, b).execute(ctx)
    r2 = await EqOp(b, a).execute(ctx)
    assert r1 == r2


@given(a=ints, b=ints)
async def test_ne_is_not_eq(a, b):
    ctx = Context()
    eq = await EqOp(a, b).execute(ctx)
    ne = await NeOp(a, b).execute(ctx)
    assert eq != ne


@given(a=ints, b=ints)
async def test_gt_lt_inverse(a, b):
    """a > b iff b < a."""
    ctx = Context()
    gt = await GtOp(a, b).execute(ctx)
    lt = await LtOp(b, a).execute(ctx)
    assert gt == lt


@given(a=ints, b=ints)
async def test_ge_le_inverse(a, b):
    """a >= b iff b <= a."""
    ctx = Context()
    ge = await GeOp(a, b).execute(ctx)
    le = await LeOp(b, a).execute(ctx)
    assert ge == le


@given(a=ints)
async def test_ge_reflexive(a):
    ctx = Context()
    assert await GeOp(a, a).execute(ctx) is True


@given(a=ints)
async def test_le_reflexive(a):
    ctx = Context()
    assert await LeOp(a, a).execute(ctx) is True


# ---------------------------------------------------------------------------
# Explicit cases
# ---------------------------------------------------------------------------


async def test_gt_true(ctx):
    assert await GtOp(5, 3).execute(ctx) is True


async def test_gt_false(ctx):
    assert await GtOp(3, 5).execute(ctx) is False


async def test_lt_true(ctx):
    assert await LtOp(3, 5).execute(ctx) is True


async def test_eq_different(ctx):
    assert await EqOp(3, 5).execute(ctx) is False


# ---------------------------------------------------------------------------
# IdCompOp - identity, not equality
# ---------------------------------------------------------------------------


async def test_id_comp_same_object(ctx):
    obj = object()
    assert await IdCompOp(Value(obj), Value(obj)).execute(ctx) is True


async def test_id_comp_equal_but_different(ctx):
    """Equal values but different objects."""
    a = [1, 2, 3]
    b = [1, 2, 3]
    assert await IdCompOp(Value(a), Value(b)).execute(ctx) is False


# ---------------------------------------------------------------------------
# TypeError raises
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("op_cls", [GtOp, LtOp, GeOp, LeOp])
async def test_type_error_raises(ctx, op_cls):
    with pytest.raises(TypeError):
        await op_cls("hello", 3).execute(ctx)
