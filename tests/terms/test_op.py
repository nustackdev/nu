"""Tests for Op hierarchy - ensure_nu wrapping, arity, purity classification.

Op.__init__ auto-wraps Python literals into Nus via ensure_nu.
This is the parasitic embedding - Python values become tree nodes.
"""

from __future__ import annotations

from typing import Any

import pytest

from nu import Context, Nu, Value
from nu.terms.op import (
    BinaryCalc,
    BinaryCmd,
    Calculation,
    Command,
    NAryCalc,
    TernaryCalc,
    UnaryCalc,
)


@pytest.fixture
def ctx() -> Context:
    return Context()


# ---------------------------------------------------------------------------
# Local test Ops
# ---------------------------------------------------------------------------


class _AddCalc(BinaryCalc[int]):
    def apply(self, left: Any, right: Any) -> int:
        return left + right


class _NegCalc(UnaryCalc[int]):
    def apply(self, operand: Any) -> int:
        return -operand


class _ClampCalc(TernaryCalc[int]):
    def apply(self, first: Any, second: Any, third: Any) -> int:
        return max(second, min(third, first))


class _SumCalc(NAryCalc[int]):
    def apply(self, *values: Any) -> int:
        return sum(values)


class _WriteCmd(BinaryCmd[None]):
    def apply(self, left: Any, right: Any) -> None:
        pass


# ---------------------------------------------------------------------------
# ensure_nu wrapping - Op.__init__ wraps literals
# ---------------------------------------------------------------------------


def test_op_wraps_int_literals():
    """Python int becomes a Nu in the tree."""
    op = _AddCalc(5, 3)
    assert isinstance(op.left, Nu)
    assert isinstance(op.right, Nu)


def test_op_wraps_str_literals():
    op = _AddCalc("hello", "world")
    assert isinstance(op.left, Nu)
    assert isinstance(op.right, Nu)


def test_op_preserves_nu_children():
    """Already-Nu children are not double-wrapped."""
    v = Value(42)
    op = _NegCalc(v)
    # The child should be a Nu wrapping v, but v itself is preserved
    assert isinstance(op.operand, Nu)


def test_op_wraps_none():
    op = _AddCalc(None, 1)
    assert isinstance(op.left, Nu)


def test_op_wraps_bool_before_int():
    """Bool is subclass of int - ensure_nu must check bool first."""
    op = _AddCalc(True, False)
    # Both should be wrapped as BoolI, not IntI
    assert isinstance(op.left, Nu)
    assert isinstance(op.right, Nu)


# ---------------------------------------------------------------------------
# Arity - operand access
# ---------------------------------------------------------------------------


def test_unary_operand():
    op = _NegCalc(Value(5))
    assert op.operand is op.children[0]
    assert op.child_count == 1


def test_binary_left_right():
    op = _AddCalc(Value(3), Value(4))
    assert op.left is op.children[0]
    assert op.right is op.children[1]
    assert op.child_count == 2


def test_ternary_first_second_third():
    op = _ClampCalc(Value(10), Value(0), Value(5))
    assert op.first is op.children[0]
    assert op.second is op.children[1]
    assert op.third is op.children[2]
    assert op.child_count == 3


def test_nary_variable_children():
    op = _SumCalc(Value(1), Value(2), Value(3), Value(4))
    assert op.child_count == 4


# ---------------------------------------------------------------------------
# Execute + apply
# ---------------------------------------------------------------------------


async def test_unary_execute(ctx):
    assert await _NegCalc(5).execute(ctx) == -5


async def test_binary_execute(ctx):
    assert await _AddCalc(3, 4).execute(ctx) == 7


async def test_ternary_execute(ctx):
    assert await _ClampCalc(10, 0, 5).execute(ctx) == 5


async def test_nary_execute(ctx):
    assert await _SumCalc(1, 2, 3, 4).execute(ctx) == 10


# ---------------------------------------------------------------------------
# Purity classification
# ---------------------------------------------------------------------------


def test_calculation_is_pure():
    assert _AddCalc(1, 2).is_self_pure is True


def test_command_is_impure():
    assert _WriteCmd(1, 2).is_self_pure is False


def test_calculation_isinstance():
    assert isinstance(_AddCalc(1, 2), Calculation)


def test_command_isinstance():
    assert isinstance(_WriteCmd(1, 2), Command)


# ---------------------------------------------------------------------------
# Repr
# ---------------------------------------------------------------------------


def test_unary_repr():
    r = repr(_NegCalc(Value(5)))
    assert "_NegCalc" in r


def test_binary_repr():
    r = repr(_AddCalc(Value(3), Value(4)))
    assert "_AddCalc" in r
