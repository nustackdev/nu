"""Tests for Interaction hierarchy - ensure_nu wrapping and arity.

Interaction.__init__ auto-wraps Python literals into Nus via ensure_nu.
This is the parasitic embedding - Python values become tree nodes.
"""

from __future__ import annotations

from typing import Any, ClassVar

from nu import Literal, Nu
from nu.terms import (
    BinaryScalar,
    Interaction,
    Mode,
    NAryScalar,
    TernaryScalar,
    UnaryScalar,
)


# ---------------------------------------------------------------------------
# Local test Ops
# ---------------------------------------------------------------------------


class _AddOp(BinaryScalar[int]):
    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def apply(self, left: Any, right: Any) -> int:
        return left + right


class _NegOp(UnaryScalar[int]):
    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def apply(self, operand: Any) -> int:
        return -operand


class _ClampOp(TernaryScalar[int]):
    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def apply(self, first: Any, second: Any, third: Any) -> int:
        return max(second, min(third, first))


class _SumOp(NAryScalar[int]):
    own_mode: ClassVar[Mode] = Mode.BOTH
    func_mode: ClassVar[Mode] = Mode.SYNC

    def apply(self, *values: Any) -> int:
        return sum(values)


# ---------------------------------------------------------------------------
# ensure_nu wrapping - Interaction.__init__ wraps literals
# ---------------------------------------------------------------------------


def test_op_wraps_int_literals():
    """Python int becomes a Nu in the tree."""
    op = _AddOp(5, 3)
    assert isinstance(op.left, Nu)
    assert isinstance(op.right, Nu)


def test_op_wraps_str_literals():
    op = _AddOp("hello", "world")
    assert isinstance(op.left, Nu)
    assert isinstance(op.right, Nu)


def test_op_preserves_nu_children():
    """Already-Nu children are not double-wrapped."""
    v = Literal(42)
    op = _NegOp(v)
    # The child should be a Nu wrapping v, but v itself is preserved
    assert isinstance(op.operand, Nu)


def test_op_wraps_none():
    op = _AddOp(None, 1)
    assert isinstance(op.left, Nu)


def test_op_wraps_bool_before_int():
    """Bool is subclass of int - ensure_nu must check bool first."""
    op = _AddOp(True, False)
    # Both should be wrapped as BoolI, not IntI
    assert isinstance(op.left, Nu)
    assert isinstance(op.right, Nu)


# ---------------------------------------------------------------------------
# Arity - operand access
# ---------------------------------------------------------------------------


def test_unary_operand():
    op = _NegOp(Literal(5))
    assert op.operand is op.children[0]
    assert op._child_count == 1


def test_binary_left_right():
    op = _AddOp(Literal(3), Literal(4))
    assert op.left is op.children[0]
    assert op.right is op.children[1]
    assert op._child_count == 2


def test_ternary_children():
    op = _ClampOp(Literal(10), Literal(0), Literal(5))
    assert op._child_count == 3


def test_nary_variable_children():
    op = _SumOp(Literal(1), Literal(2), Literal(3), Literal(4))
    assert op._child_count == 4


# ---------------------------------------------------------------------------
# Execute + apply
# ---------------------------------------------------------------------------


async def test_unary_execute(ctx):
    assert await _NegOp(5).afirst(ctx) == -5


async def test_binary_execute(ctx):
    assert await _AddOp(3, 4).afirst(ctx) == 7


async def test_ternary_execute(ctx):
    assert await _ClampOp(10, 0, 5).afirst(ctx) == 5


async def test_nary_execute(ctx):
    assert await _SumOp(1, 2, 3, 4).afirst(ctx) == 10


# ---------------------------------------------------------------------------
# Arity + isinstance
# ---------------------------------------------------------------------------


def test_unary_is_op():
    op = _NegOp(1)
    assert isinstance(op, Interaction)
    assert op._child_count == 1


def test_binary_is_op():
    op = _AddOp(1, 2)
    assert isinstance(op, Interaction)
    assert op._child_count == 2


def test_ternary_is_op():
    op = _ClampOp(10, 0, 5)
    assert isinstance(op, Interaction)
    assert op._child_count == 3


# ---------------------------------------------------------------------------
# Repr
# ---------------------------------------------------------------------------


def test_unary_repr():
    r = repr(_NegOp(Literal(5)))
    assert "_NegOp" in r


def test_binary_repr():
    r = repr(_AddOp(Literal(3), Literal(4)))
    assert "_AddOp" in r
