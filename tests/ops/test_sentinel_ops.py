"""Tests for sentinel check ops.

IsEmptyOp, IsInvalidOp, NotEmptyOp, NotInvalidOp

These are inspections, not computations. They bypass NAryOp's sentinel
propagation - they need to see the sentinel to answer the question.
"""

from __future__ import annotations

import nu

from nu import EMPTY, INVALID, Literal
from nu.ops import IsEmptyOp, IsInvalidOp, NotEmptyOp, NotInvalidOp


# ---------------------------------------------------------------------------
# IsEmptyOp
# ---------------------------------------------------------------------------


async def test_is_empty_on_empty(ctx):
    assert await IsEmptyOp(Literal(EMPTY)).first(ctx) is True


async def test_is_empty_on_invalid(ctx):
    assert await IsEmptyOp(Literal(INVALID)).first(ctx) is False


async def test_is_empty_on_normal(ctx):
    assert await IsEmptyOp(Literal(42)).first(ctx) is False


async def test_is_empty_on_none(ctx):
    assert await IsEmptyOp(Literal(None)).first(ctx) is False


async def test_is_empty_on_zero(ctx):
    assert await IsEmptyOp(Literal(0)).first(ctx) is False


# ---------------------------------------------------------------------------
# IsInvalidOp
# ---------------------------------------------------------------------------


async def test_is_invalid_on_invalid(ctx):
    assert await IsInvalidOp(Literal(INVALID)).first(ctx) is True


async def test_is_invalid_on_empty(ctx):
    assert await IsInvalidOp(Literal(EMPTY)).first(ctx) is False


async def test_is_invalid_on_normal(ctx):
    assert await IsInvalidOp(Literal(42)).first(ctx) is False


# ---------------------------------------------------------------------------
# NotEmptyOp
# ---------------------------------------------------------------------------


async def test_not_empty_on_empty(ctx):
    assert await NotEmptyOp(Literal(EMPTY)).first(ctx) is False


async def test_not_empty_on_normal(ctx):
    assert await NotEmptyOp(Literal(42)).first(ctx) is True


async def test_not_empty_on_invalid(ctx):
    assert await NotEmptyOp(Literal(INVALID)).first(ctx) is True


# ---------------------------------------------------------------------------
# NotInvalidOp
# ---------------------------------------------------------------------------


async def test_not_invalid_on_invalid(ctx):
    assert await NotInvalidOp(Literal(INVALID)).first(ctx) is False


async def test_not_invalid_on_normal(ctx):
    assert await NotInvalidOp(Literal(42)).first(ctx) is True


async def test_not_invalid_on_empty(ctx):
    assert await NotInvalidOp(Literal(EMPTY)).first(ctx) is True


