"""Tests for sentinel check ops.

IsEmptyOp, IsInvalidOp, NotEmptyOp, NotInvalidOp

These are inspections, not computations. They bypass NAryOp's sentinel
propagation - they need to see the sentinel to answer the question.
"""

from __future__ import annotations

from nu import EMPTY, INVALID, Value
from nu.ops import IsEmptyOp, IsInvalidOp, NotEmptyOp, NotInvalidOp


# ---------------------------------------------------------------------------
# IsEmptyOp
# ---------------------------------------------------------------------------


async def test_is_empty_on_empty(ctx):
    assert await IsEmptyOp(Value(EMPTY)).execute(ctx) is True


async def test_is_empty_on_invalid(ctx):
    assert await IsEmptyOp(Value(INVALID)).execute(ctx) is False


async def test_is_empty_on_normal(ctx):
    assert await IsEmptyOp(Value(42)).execute(ctx) is False


async def test_is_empty_on_none(ctx):
    assert await IsEmptyOp(Value(None)).execute(ctx) is False


async def test_is_empty_on_zero(ctx):
    assert await IsEmptyOp(Value(0)).execute(ctx) is False


# ---------------------------------------------------------------------------
# IsInvalidOp
# ---------------------------------------------------------------------------


async def test_is_invalid_on_invalid(ctx):
    assert await IsInvalidOp(Value(INVALID)).execute(ctx) is True


async def test_is_invalid_on_empty(ctx):
    assert await IsInvalidOp(Value(EMPTY)).execute(ctx) is False


async def test_is_invalid_on_normal(ctx):
    assert await IsInvalidOp(Value(42)).execute(ctx) is False


# ---------------------------------------------------------------------------
# NotEmptyOp
# ---------------------------------------------------------------------------


async def test_not_empty_on_empty(ctx):
    assert await NotEmptyOp(Value(EMPTY)).execute(ctx) is False


async def test_not_empty_on_normal(ctx):
    assert await NotEmptyOp(Value(42)).execute(ctx) is True


async def test_not_empty_on_invalid(ctx):
    assert await NotEmptyOp(Value(INVALID)).execute(ctx) is True


# ---------------------------------------------------------------------------
# NotInvalidOp
# ---------------------------------------------------------------------------


async def test_not_invalid_on_invalid(ctx):
    assert await NotInvalidOp(Value(INVALID)).execute(ctx) is False


async def test_not_invalid_on_normal(ctx):
    assert await NotInvalidOp(Value(42)).execute(ctx) is True


async def test_not_invalid_on_empty(ctx):
    assert await NotInvalidOp(Value(EMPTY)).execute(ctx) is True


