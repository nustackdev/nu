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
    assert await nu.first(IsEmptyOp(Literal(EMPTY)), ctx) is True


async def test_is_empty_on_invalid(ctx):
    assert await nu.first(IsEmptyOp(Literal(INVALID)), ctx) is False


async def test_is_empty_on_normal(ctx):
    assert await nu.first(IsEmptyOp(Literal(42)), ctx) is False


async def test_is_empty_on_none(ctx):
    assert await nu.first(IsEmptyOp(Literal(None)), ctx) is False


async def test_is_empty_on_zero(ctx):
    assert await nu.first(IsEmptyOp(Literal(0)), ctx) is False


# ---------------------------------------------------------------------------
# IsInvalidOp
# ---------------------------------------------------------------------------


async def test_is_invalid_on_invalid(ctx):
    assert await nu.first(IsInvalidOp(Literal(INVALID)), ctx) is True


async def test_is_invalid_on_empty(ctx):
    assert await nu.first(IsInvalidOp(Literal(EMPTY)), ctx) is False


async def test_is_invalid_on_normal(ctx):
    assert await nu.first(IsInvalidOp(Literal(42)), ctx) is False


# ---------------------------------------------------------------------------
# NotEmptyOp
# ---------------------------------------------------------------------------


async def test_not_empty_on_empty(ctx):
    assert await nu.first(NotEmptyOp(Literal(EMPTY)), ctx) is False


async def test_not_empty_on_normal(ctx):
    assert await nu.first(NotEmptyOp(Literal(42)), ctx) is True


async def test_not_empty_on_invalid(ctx):
    assert await nu.first(NotEmptyOp(Literal(INVALID)), ctx) is True


# ---------------------------------------------------------------------------
# NotInvalidOp
# ---------------------------------------------------------------------------


async def test_not_invalid_on_invalid(ctx):
    assert await nu.first(NotInvalidOp(Literal(INVALID)), ctx) is False


async def test_not_invalid_on_normal(ctx):
    assert await nu.first(NotInvalidOp(Literal(42)), ctx) is True


async def test_not_invalid_on_empty(ctx):
    assert await nu.first(NotInvalidOp(Literal(EMPTY)), ctx) is True


