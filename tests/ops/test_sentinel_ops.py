"""Tests for sentinel check ops.

IsEmpty, IsInvalid, NotEmpty, NotInvalid

These are inspections, not computations. They bypass ScalarQuery's sentinel
propagation - they need to see the sentinel to answer the question.
"""

from __future__ import annotations

from nu import EMPTY, INVALID, Literal
from nu.interactions import IsEmpty, IsInvalid, NotEmpty, NotInvalid


# ---------------------------------------------------------------------------
# IsEmpty
# ---------------------------------------------------------------------------


async def test_is_empty_on_empty(ctx):
    assert await IsEmpty(Literal(EMPTY)).afirst(ctx) is True


async def test_is_empty_on_invalid(ctx):
    assert await IsEmpty(Literal(INVALID)).afirst(ctx) is False


async def test_is_empty_on_normal(ctx):
    assert await IsEmpty(Literal(42)).afirst(ctx) is False


async def test_is_empty_on_none(ctx):
    assert await IsEmpty(Literal(None)).afirst(ctx) is False


async def test_is_empty_on_zero(ctx):
    assert await IsEmpty(Literal(0)).afirst(ctx) is False


# ---------------------------------------------------------------------------
# IsInvalid
# ---------------------------------------------------------------------------


async def test_is_invalid_on_invalid(ctx):
    assert await IsInvalid(Literal(INVALID)).afirst(ctx) is True


async def test_is_invalid_on_empty(ctx):
    assert await IsInvalid(Literal(EMPTY)).afirst(ctx) is False


async def test_is_invalid_on_normal(ctx):
    assert await IsInvalid(Literal(42)).afirst(ctx) is False


# ---------------------------------------------------------------------------
# NotEmpty
# ---------------------------------------------------------------------------


async def test_not_empty_on_empty(ctx):
    assert await NotEmpty(Literal(EMPTY)).afirst(ctx) is False


async def test_not_empty_on_normal(ctx):
    assert await NotEmpty(Literal(42)).afirst(ctx) is True


async def test_not_empty_on_invalid(ctx):
    assert await NotEmpty(Literal(INVALID)).afirst(ctx) is True


# ---------------------------------------------------------------------------
# NotInvalid
# ---------------------------------------------------------------------------


async def test_not_invalid_on_invalid(ctx):
    assert await NotInvalid(Literal(INVALID)).afirst(ctx) is False


async def test_not_invalid_on_normal(ctx):
    assert await NotInvalid(Literal(42)).afirst(ctx) is True


async def test_not_invalid_on_empty(ctx):
    assert await NotInvalid(Literal(EMPTY)).afirst(ctx) is True
