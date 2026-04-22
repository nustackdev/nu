"""Tests for sentinel check ops.

IsEmpty, IsInvalid, NotEmpty, NotInvalid

These are inspections, not computations. They bypass NAryScalar's sentinel
propagation - they need to see the sentinel to answer the question.
"""

from __future__ import annotations

from nu import EMPTY, INVALID, Literal
from nu.interactions import IsEmpty, IsInvalid, NotEmpty, NotInvalid


# ---------------------------------------------------------------------------
# IsEmpty
# ---------------------------------------------------------------------------


async def test_is_empty_on_empty(ctx):
    assert await IsEmpty(Literal(EMPTY)).first(ctx) is True


async def test_is_empty_on_invalid(ctx):
    assert await IsEmpty(Literal(INVALID)).first(ctx) is False


async def test_is_empty_on_normal(ctx):
    assert await IsEmpty(Literal(42)).first(ctx) is False


async def test_is_empty_on_none(ctx):
    assert await IsEmpty(Literal(None)).first(ctx) is False


async def test_is_empty_on_zero(ctx):
    assert await IsEmpty(Literal(0)).first(ctx) is False


# ---------------------------------------------------------------------------
# IsInvalid
# ---------------------------------------------------------------------------


async def test_is_invalid_on_invalid(ctx):
    assert await IsInvalid(Literal(INVALID)).first(ctx) is True


async def test_is_invalid_on_empty(ctx):
    assert await IsInvalid(Literal(EMPTY)).first(ctx) is False


async def test_is_invalid_on_normal(ctx):
    assert await IsInvalid(Literal(42)).first(ctx) is False


# ---------------------------------------------------------------------------
# NotEmpty
# ---------------------------------------------------------------------------


async def test_not_empty_on_empty(ctx):
    assert await NotEmpty(Literal(EMPTY)).first(ctx) is False


async def test_not_empty_on_normal(ctx):
    assert await NotEmpty(Literal(42)).first(ctx) is True


async def test_not_empty_on_invalid(ctx):
    assert await NotEmpty(Literal(INVALID)).first(ctx) is True


# ---------------------------------------------------------------------------
# NotInvalid
# ---------------------------------------------------------------------------


async def test_not_invalid_on_invalid(ctx):
    assert await NotInvalid(Literal(INVALID)).first(ctx) is False


async def test_not_invalid_on_normal(ctx):
    assert await NotInvalid(Literal(42)).first(ctx) is True


async def test_not_invalid_on_empty(ctx):
    assert await NotInvalid(Literal(EMPTY)).first(ctx) is True
