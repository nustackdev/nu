"""Tests for comparison ops.

Binary: EqOp, NeOp, GtOp, GeOp, LtOp, LeOp, IdCompOp

All pure ops. TypeError -> INVALID.
"""

from __future__ import annotations

import nu

import pytest
from hypothesis import given
from hypothesis import strategies as st

from nu import Context, Literal
from nu.ops import EqOp, GeOp, GtOp, IdCompOp, LeOp, LtOp, NeOp


ints = st.integers(min_value=-10000, max_value=10000)


# ---------------------------------------------------------------------------
# Properties via hypothesis
# ---------------------------------------------------------------------------


@given(a=ints)
async def test_eq_reflexive(a):
    ctx = Context()
    assert await nu.first(EqOp(a, a), ctx) is True


@given(a=ints, b=ints)
async def test_eq_symmetric(a, b):
    ctx = Context()
    r1 = await nu.first(EqOp(a, b), ctx)
    r2 = await nu.first(EqOp(b, a), ctx)
    assert r1 == r2


@given(a=ints, b=ints)
async def test_ne_is_not_eq(a, b):
    ctx = Context()
    eq = await nu.first(EqOp(a, b), ctx)
    ne = await nu.first(NeOp(a, b), ctx)
    assert eq != ne


@given(a=ints, b=ints)
async def test_gt_lt_inverse(a, b):
    """a > b iff b < a."""
    ctx = Context()
    gt = await nu.first(GtOp(a, b), ctx)
    lt = await nu.first(LtOp(b, a), ctx)
    assert gt == lt


@given(a=ints, b=ints)
async def test_ge_le_inverse(a, b):
    """a >= b iff b <= a."""
    ctx = Context()
    ge = await nu.first(GeOp(a, b), ctx)
    le = await nu.first(LeOp(b, a), ctx)
    assert ge == le


@given(a=ints)
async def test_ge_reflexive(a):
    ctx = Context()
    assert await nu.first(GeOp(a, a), ctx) is True


@given(a=ints)
async def test_le_reflexive(a):
    ctx = Context()
    assert await nu.first(LeOp(a, a), ctx) is True


# ---------------------------------------------------------------------------
# Explicit cases
# ---------------------------------------------------------------------------


async def test_gt_true(ctx):
    assert await nu.first(GtOp(5, 3), ctx) is True


async def test_gt_false(ctx):
    assert await nu.first(GtOp(3, 5), ctx) is False


async def test_lt_true(ctx):
    assert await nu.first(LtOp(3, 5), ctx) is True


async def test_eq_different(ctx):
    assert await nu.first(EqOp(3, 5), ctx) is False


# ---------------------------------------------------------------------------
# IdCompOp - identity, not equality
# ---------------------------------------------------------------------------


async def test_id_comp_same_object(ctx):
    obj = object()
    assert await nu.first(IdCompOp(Literal(obj), Literal(obj)), ctx) is True


async def test_id_comp_equal_but_different(ctx):
    """Equal values but different objects."""
    a = [1, 2, 3]
    b = [1, 2, 3]
    assert await nu.first(IdCompOp(Literal(a), Literal(b)), ctx) is False


# ---------------------------------------------------------------------------
# TypeError raises
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("op_cls", [GtOp, LtOp, GeOp, LeOp])
async def test_type_error_raises(ctx, op_cls):
    with pytest.raises(TypeError):
        await nu.first(op_cls("hello", 3), ctx)
