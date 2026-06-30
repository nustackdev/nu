"""Tests for sentinels and sentinel propagation through ScalarQuery.

Sentinel propagation is the most critical behavioral contract in Nu.
If any operand resolves to EMPTY or INVALID, ScalarQuery returns INVALID
without calling apply(). This is the safety net for the entire algebra.
"""

from __future__ import annotations

from typing import Any, ClassVar

from nu import Literal, runtime
from nu.terms import Mode
from nu.terms.query import ScalarQuery
from nu.terms.sentinels import (
    EMPTY,
    INVALID,
    Empty,
    Invalid,
    is_empty,
    is_invalid,
    is_sentinel,
)


# ---------------------------------------------------------------------------
# Sentinel identity and truthiness
# ---------------------------------------------------------------------------


def test_empty_is_falsy():
    assert bool(EMPTY) is False


def test_invalid_is_falsy():
    assert bool(INVALID) is False


def test_empty_repr():
    assert repr(EMPTY) == "<EMPTY>"


def test_invalid_repr():
    assert repr(INVALID) == "<INVALID>"


# ---------------------------------------------------------------------------
# Equality - isinstance-based, not identity
# ---------------------------------------------------------------------------


def test_empty_equals_fresh_empty():
    assert EMPTY == Empty()


def test_invalid_equals_fresh_invalid():
    assert INVALID == Invalid()


def test_empty_not_equal_to_invalid():
    assert EMPTY != INVALID


def test_empty_not_equal_to_none():
    assert EMPTY != None


def test_invalid_not_equal_to_none():
    assert INVALID != None


def test_empty_hashable():
    assert hash(EMPTY) == hash(Empty())


def test_invalid_hashable():
    assert hash(INVALID) == hash(Invalid())


# ---------------------------------------------------------------------------
# Type guards
# ---------------------------------------------------------------------------


def test_is_sentinel_on_empty():
    assert is_sentinel(EMPTY) is True


def test_is_sentinel_on_invalid():
    assert is_sentinel(INVALID) is True


def test_is_sentinel_on_normal():
    assert is_sentinel(42) is False
    assert is_sentinel(None) is False
    assert is_sentinel("") is False


def test_is_empty():
    assert is_empty(EMPTY) is True
    assert is_empty(INVALID) is False
    assert is_empty(42) is False


def test_is_invalid():
    assert is_invalid(INVALID) is True
    assert is_invalid(EMPTY) is False
    assert is_invalid(42) is False


# ---------------------------------------------------------------------------
# ScalarQuery sentinel propagation
# ---------------------------------------------------------------------------

# Local test Interaction - verifies apply() is/isn't called.


class _TestAddOp(ScalarQuery):
    """ScalarQuery that tracks whether _apply was called."""

    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})

    apply_called: bool = False

    def __init__(self, left: Any, right: Any) -> None:
        super().__init__(left, right)

    def _apply(self, ctx: Any, ops: list[Any]) -> int:
        _TestAddOp.apply_called = True
        return ops[0] + ops[1]


class TestNAryOpSentinelPropagation:
    """ScalarQuery.aexecute intercepts sentinels before apply."""

    def setup_method(self):
        _TestAddOp.apply_called = False

    async def test_clean_operands_calls_apply(self, ctx):
        result = await runtime.afirst(_TestAddOp(Literal(3), Literal(4)), ctx)
        assert result == 7
        assert _TestAddOp.apply_called is True

    async def test_empty_operand_returns_invalid(self, ctx):
        """EMPTY child -> INVALID result, apply never called."""
        result = await runtime.afirst(_TestAddOp(Literal(EMPTY), Literal(4)), ctx)
        assert is_invalid(result)
        assert _TestAddOp.apply_called is False

    async def test_invalid_operand_returns_invalid(self, ctx):
        """INVALID child -> INVALID result, apply never called."""
        result = await runtime.afirst(_TestAddOp(Literal(3), Literal(INVALID)), ctx)
        assert is_invalid(result)
        assert _TestAddOp.apply_called is False

    async def test_both_sentinels_returns_invalid(self, ctx):
        result = await runtime.afirst(_TestAddOp(Literal(EMPTY), Literal(INVALID)), ctx)
        assert is_invalid(result)
        assert _TestAddOp.apply_called is False

    async def test_nested_sentinel_propagation(self, ctx):
        """Sentinel propagates through nested ops."""
        inner = _TestAddOp(Literal(EMPTY), Literal(1))
        outer = _TestAddOp(inner, Literal(2))
        result = await runtime.afirst(outer, ctx)
        assert is_invalid(result)
