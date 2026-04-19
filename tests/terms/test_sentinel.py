"""Tests for sentinels and sentinel propagation through NAryOp.

Sentinel propagation is the most critical behavioral contract in Nu.
If any operand resolves to EMPTY or INVALID, NAryOp returns INVALID
without calling apply(). This is the safety net for the entire algebra.
"""

from __future__ import annotations

from typing import Any

import nu
from nu import EMPTY, INVALID, Literal
from nu.terms.op import BinaryOp
from nu.terms.sentinel import Empty, Invalid, is_empty, is_invalid, is_sentinel, propagate_special


# ---------------------------------------------------------------------------
# Sentinel identity and truthiness
# ---------------------------------------------------------------------------


def test_empty_is_falsy():
    assert bool(EMPTY) is False


def test_invalid_is_falsy():
    assert bool(INVALID) is False


def test_empty_repr():
    assert repr(EMPTY) == "<Empty>"


def test_invalid_repr():
    assert repr(INVALID) == "<Invalid>"


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
# propagate_special
# ---------------------------------------------------------------------------


def test_propagate_special_all_clean():
    assert propagate_special(1, 2, 3) is None


def test_propagate_special_with_empty():
    """EMPTY in any position -> returns INVALID."""
    result = propagate_special(1, EMPTY, 3)
    assert is_invalid(result)


def test_propagate_special_with_invalid():
    result = propagate_special(1, INVALID, 3)
    assert is_invalid(result)


def test_propagate_special_both_sentinels():
    result = propagate_special(EMPTY, INVALID)
    assert is_invalid(result)


def test_propagate_special_no_args():
    assert propagate_special() is None


# ---------------------------------------------------------------------------
# NAryOp sentinel propagation
# ---------------------------------------------------------------------------

# Local test Op - verifies apply() is/isn't called.


class _TestAddOp(BinaryOp[int]):
    """BinaryOp that tracks whether apply was called."""

    apply_called: bool = False

    def apply(self, left: Any, right: Any) -> int:
        _TestAddOp.apply_called = True
        return left + right


class TestNAryOpSentinelPropagation:
    """NAryOp.execute intercepts sentinels before apply."""

    def setup_method(self):
        _TestAddOp.apply_called = False

    async def test_clean_operands_calls_apply(self, ctx):
        result = await nu.first(_TestAddOp(Literal(3), Literal(4)), ctx)
        assert result == 7
        assert _TestAddOp.apply_called is True

    async def test_empty_operand_returns_invalid(self, ctx):
        """EMPTY child -> INVALID result, apply never called."""
        result = await nu.first(_TestAddOp(Literal(EMPTY), Literal(4)), ctx)
        assert is_invalid(result)
        assert _TestAddOp.apply_called is False

    async def test_invalid_operand_returns_invalid(self, ctx):
        """INVALID child -> INVALID result, apply never called."""
        result = await nu.first(_TestAddOp(Literal(3), Literal(INVALID)), ctx)
        assert is_invalid(result)
        assert _TestAddOp.apply_called is False

    async def test_both_sentinels_returns_invalid(self, ctx):
        result = await nu.first(_TestAddOp(Literal(EMPTY), Literal(INVALID)), ctx)
        assert is_invalid(result)
        assert _TestAddOp.apply_called is False

    async def test_nested_sentinel_propagation(self, ctx):
        """Sentinel propagates through nested ops."""
        inner = _TestAddOp(Literal(EMPTY), Literal(1))
        outer = _TestAddOp(inner, Literal(2))
        result = await nu.first(outer, ctx)
        assert is_invalid(result)
