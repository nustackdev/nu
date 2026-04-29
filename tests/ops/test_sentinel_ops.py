"""Tests for sentinel check ops.

IsEmpty, IsInvalid, NotEmpty, NotInvalid

These are inspections, not computations. They bypass ScalarQuery's sentinel
propagation - they need to see the sentinel to answer the question.
"""

from __future__ import annotations

from nu import Literal, runtime
from nu.interactions import IsEmpty, IsInvalid, NotEmpty, NotInvalid
from nu.terms.sentinels import EMPTY, INVALID


# ---------------------------------------------------------------------------
# IsEmpty
# ---------------------------------------------------------------------------


async def test_is_empty_on_empty(ctx):
    assert await runtime.afirst(IsEmpty(Literal(EMPTY)), ctx) is True


async def test_is_empty_on_invalid(ctx):
    assert await runtime.afirst(IsEmpty(Literal(INVALID)), ctx) is False


async def test_is_empty_on_normal(ctx):
    assert await runtime.afirst(IsEmpty(Literal(42)), ctx) is False


async def test_is_empty_on_none(ctx):
    assert await runtime.afirst(IsEmpty(Literal(None)), ctx) is False


async def test_is_empty_on_zero(ctx):
    assert await runtime.afirst(IsEmpty(Literal(0)), ctx) is False


# ---------------------------------------------------------------------------
# IsInvalid
# ---------------------------------------------------------------------------


async def test_is_invalid_on_invalid(ctx):
    assert await runtime.afirst(IsInvalid(Literal(INVALID)), ctx) is True


async def test_is_invalid_on_empty(ctx):
    assert await runtime.afirst(IsInvalid(Literal(EMPTY)), ctx) is False


async def test_is_invalid_on_normal(ctx):
    assert await runtime.afirst(IsInvalid(Literal(42)), ctx) is False


# ---------------------------------------------------------------------------
# NotEmpty
# ---------------------------------------------------------------------------


async def test_not_empty_on_empty(ctx):
    assert await runtime.afirst(NotEmpty(Literal(EMPTY)), ctx) is False


async def test_not_empty_on_normal(ctx):
    assert await runtime.afirst(NotEmpty(Literal(42)), ctx) is True


async def test_not_empty_on_invalid(ctx):
    assert await runtime.afirst(NotEmpty(Literal(INVALID)), ctx) is True


# ---------------------------------------------------------------------------
# NotInvalid
# ---------------------------------------------------------------------------


async def test_not_invalid_on_invalid(ctx):
    assert await runtime.afirst(NotInvalid(Literal(INVALID)), ctx) is False


async def test_not_invalid_on_normal(ctx):
    assert await runtime.afirst(NotInvalid(Literal(42)), ctx) is True


async def test_not_invalid_on_empty(ctx):
    assert await runtime.afirst(NotInvalid(Literal(EMPTY)), ctx) is True
