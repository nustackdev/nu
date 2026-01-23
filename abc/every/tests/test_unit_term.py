"""Unit tests for every.term module.

Tests for the term system components:
- Term, LValue, RValue base classes
- Gettable protocol
- Morphism hierarchy (Unary, Binary, Ternary)
- Operation and Command purity mixins
- Children management interface
- Sentinel propagation
"""

from __future__ import annotations

from typing import Any

import pytest

from every.sentinel import EMPTY, INVALID, Sentinel
from every.term import (
    BinaryMorphism,
    Command,
    Context,
    Gettable,
    LValue,
    Morphism,
    NAryMorphism,
    Operation,
    RValue,
    Term,
    TernaryMorphism,
    UnaryMorphism,
)


# ============================================================================
# TEST FIXTURES - CONCRETE IMPLEMENTATIONS FOR TESTING
# ============================================================================


class SimpleTerm(Term[int]):
    """Simple Term implementation for testing."""

    def __init__(self, value: int, pure: bool = True) -> None:
        self._value = value
        self._pure = pure

    def execute(self, context: Context) -> int:
        return self._value

    @property
    def is_pure(self) -> bool:
        return self._pure


class SimpleLValue(LValue[str]):
    """Simple LValue implementation for testing."""

    def __init__(self, path: str) -> None:
        self._path = path

    def execute(self, context: Context) -> str:
        return self._path

    @property
    def is_pure(self) -> bool:
        return True

    def resolve(self, context: Context) -> object:
        return self._path


class SimpleRValue(RValue[float]):
    """Simple RValue implementation for testing."""

    def __init__(self, value: float, children: tuple = ()) -> None:
        self._value = value
        self.children = children

    def execute(self, context: Context) -> float:
        return self._value

    @property
    def is_pure(self) -> bool:
        return True


class SimpleGettable:
    """Simple Gettable implementation for testing."""

    def __init__(self, value: Any) -> None:
        self._value = value

    def get(self, ctx: Context) -> Any:
        return self._value


# Concrete morphism implementations for testing


class NegateOp(Operation, UnaryMorphism[float]):
    """Negate a number."""

    def _apply(self, operand: float) -> float:
        return -operand


class AbsOp(Operation, UnaryMorphism[float]):
    """Absolute value."""

    def _apply(self, operand: float) -> float:
        return abs(operand)


class AddOp(Operation, BinaryMorphism[float]):
    """Add two numbers."""

    def _apply(self, left: float, right: float) -> float:
        return left + right


class SubOp(Operation, BinaryMorphism[float]):
    """Subtract two numbers."""

    def _apply(self, left: float, right: float) -> float:
        return left - right


class MulOp(Operation, BinaryMorphism[float]):
    """Multiply two numbers."""

    def _apply(self, left: float, right: float) -> float:
        return left * right


class GreaterThanOp(Operation, BinaryMorphism[bool]):
    """Compare two numbers."""

    def _apply(self, left: float, right: float) -> bool:
        return left > right


class IfThenElseOp(Operation, TernaryMorphism[Any]):
    """Conditional expression."""

    def _apply(self, condition: bool, then_val: Any, else_val: Any) -> Any:
        return then_val if condition else else_val


class ClampOp(Operation, TernaryMorphism[float]):
    """Clamp value between min and max."""

    def _apply(self, value: float, min_val: float, max_val: float) -> float:
        return max(min_val, min(max_val, value))


class SetValueCmd(Command, UnaryMorphism[int]):
    """Impure command that simulates setting a value."""

    def __init__(self, value: int | Term) -> None:
        super().__init__(value)
        self.side_effect_called = False

    def _apply(self, value: int) -> int:
        self.side_effect_called = True
        return value


class WriteCmd(Command, BinaryMorphism[str]):
    """Impure command that simulates writing key-value."""

    def __init__(self, key: str | Term, value: str | Term) -> None:
        super().__init__(key, value)
        self.written: tuple[str, str] | None = None

    def _apply(self, key: str, value: str) -> str:
        self.written = (key, value)
        return value


# ============================================================================
# TERM BASE CLASS TESTS
# ============================================================================


def test_term_is_abstract() -> None:
    """Test that Term cannot be instantiated directly."""
    with pytest.raises(TypeError):
        Term()  # type: ignore


def test_simple_term_execute() -> None:
    """Test Term.execute() returns expected value."""
    ctx = Context()
    term = SimpleTerm(42)
    assert term.execute(ctx) == 42


def test_simple_term_is_pure() -> None:
    """Test Term.is_pure property."""
    pure_term = SimpleTerm(1, pure=True)
    impure_term = SimpleTerm(1, pure=False)
    assert pure_term.is_pure is True
    assert impure_term.is_pure is False


# ============================================================================
# LVALUE TESTS
# ============================================================================


def test_lvalue_is_abstract() -> None:
    """Test that LValue cannot be instantiated directly."""
    with pytest.raises(TypeError):
        LValue()  # type: ignore


def test_simple_lvalue_execute() -> None:
    """Test LValue.execute() returns expected value."""
    ctx = Context()
    lvalue = SimpleLValue("/path/to/value")
    assert lvalue.execute(ctx) == "/path/to/value"


def test_simple_lvalue_resolve() -> None:
    """Test LValue.resolve() returns path."""
    ctx = Context()
    lvalue = SimpleLValue("/path/to/value")
    assert lvalue.resolve(ctx) == "/path/to/value"


def test_simple_lvalue_is_pure() -> None:
    """Test LValue.is_pure is always True."""
    lvalue = SimpleLValue("/path")
    assert lvalue.is_pure is True


# ============================================================================
# RVALUE TESTS
# ============================================================================


def test_rvalue_is_abstract() -> None:
    """Test that RValue cannot be instantiated directly."""
    with pytest.raises(TypeError):
        RValue()  # type: ignore


def test_simple_rvalue_execute() -> None:
    """Test RValue.execute() returns expected value."""
    ctx = Context()
    rvalue = SimpleRValue(3.14)
    assert rvalue.execute(ctx) == 3.14


def test_simple_rvalue_children() -> None:
    """Test RValue.children property."""
    child1 = SimpleTerm(1)
    child2 = SimpleTerm(2)
    rvalue = SimpleRValue(0.0, children=(child1, child2))
    assert rvalue.children == (child1, child2)


def test_simple_rvalue_empty_children() -> None:
    """Test RValue with no children."""
    rvalue = SimpleRValue(1.0)
    assert rvalue.children == ()


# ============================================================================
# GETTABLE PROTOCOL TESTS
# ============================================================================


def test_gettable_is_runtime_checkable() -> None:
    """Test that Gettable is a runtime checkable protocol."""
    gettable = SimpleGettable(42)
    assert isinstance(gettable, Gettable)


def test_gettable_get_returns_value() -> None:
    """Test Gettable.get() returns the value."""
    ctx = Context()
    gettable = SimpleGettable(42)
    assert gettable.get(ctx) == 42


def test_gettable_get_returns_sentinel() -> None:
    """Test Gettable.get() can return sentinels."""
    ctx = Context()
    empty_gettable = SimpleGettable(EMPTY)
    invalid_gettable = SimpleGettable(INVALID)
    assert empty_gettable.get(ctx) is EMPTY
    assert invalid_gettable.get(ctx) is INVALID


def test_non_gettable_not_instance() -> None:
    """Test that non-Gettable objects are not instances."""
    assert not isinstance(42, Gettable)
    assert not isinstance("string", Gettable)
    assert not isinstance([], Gettable)


# ============================================================================
# MORPHISM BASE TESTS
# ============================================================================


def test_morphism_is_abstract() -> None:
    """Test that Morphism cannot be instantiated directly."""
    with pytest.raises(TypeError):
        Morphism()  # type: ignore


def test_morphism_is_rvalue() -> None:
    """Test that Morphism inherits from RValue."""
    assert issubclass(Morphism, RValue)


def test_nary_morphism_is_abstract() -> None:
    """Test that NAryMorphism cannot be instantiated directly."""
    with pytest.raises(TypeError):
        NAryMorphism()  # type: ignore


# ============================================================================
# UNARY MORPHISM TESTS
# ============================================================================


def test_unary_morphism_with_literal() -> None:
    """Test UnaryMorphism with literal operand."""
    ctx = Context()
    neg = NegateOp(5.0)
    assert neg.execute(ctx) == -5.0


def test_unary_morphism_with_term() -> None:
    """Test UnaryMorphism with Term operand."""
    ctx = Context()
    inner = SimpleTerm(10)

    class DoubleOp(Operation, UnaryMorphism[int]):
        def _apply(self, operand: int) -> int:
            return operand * 2

    double = DoubleOp(inner)
    assert double.execute(ctx) == 20


def test_unary_morphism_with_gettable() -> None:
    """Test UnaryMorphism with Gettable operand."""
    ctx = Context()
    gettable = SimpleGettable(7.0)
    neg = NegateOp(gettable)
    assert neg.execute(ctx) == -7.0


def test_unary_morphism_operand_property() -> None:
    """Test UnaryMorphism.operand property."""
    neg = NegateOp(42.0)
    assert neg.operand == 42.0


def test_unary_morphism_children() -> None:
    """Test UnaryMorphism.children tuple."""
    neg = NegateOp(42.0)
    assert neg.children == (42.0,)


def test_unary_morphism_child_count() -> None:
    """Test UnaryMorphism.child_count()."""
    neg = NegateOp(42.0)
    assert neg.child_count() == 1


def test_unary_morphism_sentinel_propagation_empty() -> None:
    """Test UnaryMorphism returns INVALID when operand is EMPTY."""
    ctx = Context()
    neg = NegateOp(EMPTY)
    assert neg.execute(ctx) is INVALID


def test_unary_morphism_sentinel_propagation_invalid() -> None:
    """Test UnaryMorphism returns INVALID when operand is INVALID."""
    ctx = Context()
    neg = NegateOp(INVALID)
    assert neg.execute(ctx) is INVALID


def test_unary_morphism_sentinel_from_term() -> None:
    """Test UnaryMorphism propagates sentinel from Term child."""
    ctx = Context()

    class EmptyTerm(Term[Sentinel]):
        def execute(self, context: Context) -> Sentinel:
            return EMPTY

        @property
        def is_pure(self) -> bool:
            return True

    neg = NegateOp(EmptyTerm())
    assert neg.execute(ctx) is INVALID


def test_unary_morphism_sentinel_from_gettable() -> None:
    """Test UnaryMorphism propagates sentinel from Gettable."""
    ctx = Context()
    gettable = SimpleGettable(INVALID)
    neg = NegateOp(gettable)
    assert neg.execute(ctx) is INVALID


# ============================================================================
# BINARY MORPHISM TESTS
# ============================================================================


def test_binary_morphism_with_literals() -> None:
    """Test BinaryMorphism with literal operands."""
    ctx = Context()
    add = AddOp(3.0, 4.0)
    assert add.execute(ctx) == 7.0


def test_binary_morphism_with_terms() -> None:
    """Test BinaryMorphism with Term operands."""
    ctx = Context()
    left = SimpleTerm(10)
    right = SimpleTerm(5)

    class IntSubOp(Operation, BinaryMorphism[int]):
        def _apply(self, left: int, right: int) -> int:
            return left - right

    sub = IntSubOp(left, right)
    assert sub.execute(ctx) == 5


def test_binary_morphism_with_gettables() -> None:
    """Test BinaryMorphism with Gettable operands."""
    ctx = Context()
    left = SimpleGettable(10.0)
    right = SimpleGettable(3.0)
    mul = MulOp(left, right)
    assert mul.execute(ctx) == 30.0


def test_binary_morphism_mixed_operands() -> None:
    """Test BinaryMorphism with mixed operand types."""
    ctx = Context()
    term = SimpleTerm(5)

    class IntAddOp(Operation, BinaryMorphism[int]):
        def _apply(self, left: int, right: int) -> int:
            return left + right

    # Term + literal
    add = IntAddOp(term, 10)
    assert add.execute(ctx) == 15


def test_binary_morphism_left_property() -> None:
    """Test BinaryMorphism.left property."""
    add = AddOp(1.0, 2.0)
    assert add.left == 1.0


def test_binary_morphism_right_property() -> None:
    """Test BinaryMorphism.right property."""
    add = AddOp(1.0, 2.0)
    assert add.right == 2.0


def test_binary_morphism_children() -> None:
    """Test BinaryMorphism.children tuple."""
    add = AddOp(1.0, 2.0)
    assert add.children == (1.0, 2.0)


def test_binary_morphism_child_count() -> None:
    """Test BinaryMorphism.child_count()."""
    add = AddOp(1.0, 2.0)
    assert add.child_count() == 2


def test_binary_morphism_sentinel_left() -> None:
    """Test BinaryMorphism returns INVALID when left operand is sentinel."""
    ctx = Context()
    add = AddOp(EMPTY, 5.0)
    assert add.execute(ctx) is INVALID


def test_binary_morphism_sentinel_right() -> None:
    """Test BinaryMorphism returns INVALID when right operand is sentinel."""
    ctx = Context()
    add = AddOp(5.0, INVALID)
    assert add.execute(ctx) is INVALID


def test_binary_morphism_sentinel_both() -> None:
    """Test BinaryMorphism returns INVALID when both operands are sentinels."""
    ctx = Context()
    add = AddOp(EMPTY, INVALID)
    assert add.execute(ctx) is INVALID


# ============================================================================
# TERNARY MORPHISM TESTS
# ============================================================================


def test_ternary_morphism_with_literals() -> None:
    """Test TernaryMorphism with literal operands."""
    ctx = Context()
    ite = IfThenElseOp(True, "yes", "no")
    assert ite.execute(ctx) == "yes"

    ite2 = IfThenElseOp(False, "yes", "no")
    assert ite2.execute(ctx) == "no"


def test_ternary_morphism_with_terms() -> None:
    """Test TernaryMorphism with Term operands."""
    ctx = Context()

    class BoolTerm(Term[bool]):
        def __init__(self, value: bool) -> None:
            self._value = value

        def execute(self, context: Context) -> bool:
            return self._value

        @property
        def is_pure(self) -> bool:
            return True

    cond = BoolTerm(True)
    then_val = SimpleTerm(100)
    else_val = SimpleTerm(0)
    ite = IfThenElseOp(cond, then_val, else_val)
    assert ite.execute(ctx) == 100


def test_ternary_morphism_clamp() -> None:
    """Test TernaryMorphism clamp operation."""
    ctx = Context()
    # Value within range
    clamp1 = ClampOp(5.0, 0.0, 10.0)
    assert clamp1.execute(ctx) == 5.0

    # Value below range
    clamp2 = ClampOp(-5.0, 0.0, 10.0)
    assert clamp2.execute(ctx) == 0.0

    # Value above range
    clamp3 = ClampOp(15.0, 0.0, 10.0)
    assert clamp3.execute(ctx) == 10.0


def test_ternary_morphism_first_property() -> None:
    """Test TernaryMorphism.first property."""
    ite = IfThenElseOp(True, 1, 2)
    assert ite.first is True


def test_ternary_morphism_second_property() -> None:
    """Test TernaryMorphism.second property."""
    ite = IfThenElseOp(True, 1, 2)
    assert ite.second == 1


def test_ternary_morphism_third_property() -> None:
    """Test TernaryMorphism.third property."""
    ite = IfThenElseOp(True, 1, 2)
    assert ite.third == 2


def test_ternary_morphism_children() -> None:
    """Test TernaryMorphism.children tuple."""
    ite = IfThenElseOp(True, 1, 2)
    assert ite.children == (True, 1, 2)


def test_ternary_morphism_child_count() -> None:
    """Test TernaryMorphism.child_count()."""
    ite = IfThenElseOp(True, 1, 2)
    assert ite.child_count() == 3


def test_ternary_morphism_sentinel_first() -> None:
    """Test TernaryMorphism returns INVALID when first operand is sentinel."""
    ctx = Context()
    ite = IfThenElseOp(EMPTY, 1, 2)
    assert ite.execute(ctx) is INVALID


def test_ternary_morphism_sentinel_second() -> None:
    """Test TernaryMorphism returns INVALID when second operand is sentinel."""
    ctx = Context()
    ite = IfThenElseOp(True, INVALID, 2)
    assert ite.execute(ctx) is INVALID


def test_ternary_morphism_sentinel_third() -> None:
    """Test TernaryMorphism returns INVALID when third operand is sentinel."""
    ctx = Context()
    ite = IfThenElseOp(True, 1, EMPTY)
    assert ite.execute(ctx) is INVALID


# ============================================================================
# CHILDREN MANAGEMENT INTERFACE TESTS
# ============================================================================


def test_iter_children() -> None:
    """Test iter_children() iterates over all children."""
    add = AddOp(1.0, 2.0)
    children = list(add.iter_children())
    assert children == [1.0, 2.0]


def test_get_child() -> None:
    """Test get_child() returns child at index."""
    ite = IfThenElseOp("a", "b", "c")
    assert ite.get_child(0) == "a"
    assert ite.get_child(1) == "b"
    assert ite.get_child(2) == "c"


def test_get_child_out_of_bounds() -> None:
    """Test get_child() raises IndexError for invalid index."""
    neg = NegateOp(1.0)
    with pytest.raises(IndexError):
        neg.get_child(5)


def test_iter_term_children() -> None:
    """Test iter_term_children() yields only Term children."""
    term1 = SimpleTerm(1)
    term2 = SimpleTerm(2)

    class MultiOp(Operation, TernaryMorphism[int]):
        def _apply(self, a: Any, b: Any, c: Any) -> int:
            return 0

    op = MultiOp(term1, "literal", term2)
    term_children = list(op.iter_term_children())
    assert term_children == [term1, term2]


def test_iter_term_children_no_terms() -> None:
    """Test iter_term_children() with no Term children."""
    add = AddOp(1.0, 2.0)
    term_children = list(add.iter_term_children())
    assert term_children == []


def test_iter_resolved() -> None:
    """Test iter_resolved() resolves all children."""
    ctx = Context()
    term = SimpleTerm(10)
    gettable = SimpleGettable(20)
    literal = 30

    class MultiOp(Operation, TernaryMorphism[int]):
        def _apply(self, a: int, b: int, c: int) -> int:
            return a + b + c

    op = MultiOp(term, gettable, literal)
    resolved = list(op.iter_resolved(ctx))
    assert resolved == [10, 20, 30]


# ============================================================================
# OPERATION MIXIN TESTS
# ============================================================================


def test_operation_is_pure_with_literals() -> None:
    """Test Operation.is_pure with literal children."""
    add = AddOp(1.0, 2.0)
    assert add.is_pure is True


def test_operation_is_pure_with_pure_terms() -> None:
    """Test Operation.is_pure with pure Term children."""
    pure_term = SimpleTerm(1, pure=True)
    neg = NegateOp(pure_term)
    assert neg.is_pure is True


def test_operation_is_impure_with_impure_child() -> None:
    """Test Operation.is_pure is False when any child is impure."""
    impure_term = SimpleTerm(1, pure=False)
    neg = NegateOp(impure_term)
    assert neg.is_pure is False


def test_operation_is_pure_mixed_children() -> None:
    """Test Operation.is_pure with mixed pure/literal children."""
    pure_term = SimpleTerm(1, pure=True)

    class MixedOp(Operation, BinaryMorphism[int]):
        def _apply(self, left: int, right: int) -> int:
            return left + right

    op = MixedOp(pure_term, 42)  # Term + literal
    assert op.is_pure is True


def test_operation_nested_purity() -> None:
    """Test Operation.is_pure propagates through nested morphisms."""
    inner = NegateOp(5.0)  # Pure
    outer = NegateOp(inner)  # Should also be pure
    assert outer.is_pure is True


def test_operation_nested_impurity() -> None:
    """Test Operation.is_pure detects nested impure morphisms."""
    impure_term = SimpleTerm(1, pure=False)
    inner = NegateOp(impure_term)  # Impure (has impure child)
    outer = NegateOp(inner)  # Should be impure
    assert outer.is_pure is False


# ============================================================================
# COMMAND MIXIN TESTS
# ============================================================================


def test_command_is_always_impure() -> None:
    """Test Command.is_pure is always False."""
    cmd = SetValueCmd(42)
    assert cmd.is_pure is False


def test_command_is_impure_even_with_pure_children() -> None:
    """Test Command.is_pure is False even with pure children."""
    pure_term = SimpleTerm(1, pure=True)
    cmd = SetValueCmd(pure_term)
    assert cmd.is_pure is False


def test_command_executes_side_effect() -> None:
    """Test Command executes and has side effects."""
    ctx = Context()
    cmd = SetValueCmd(42)
    result = cmd.execute(ctx)
    assert result == 42
    assert cmd.side_effect_called is True


def test_command_with_sentinel() -> None:
    """Test Command returns INVALID when operand is sentinel."""
    ctx = Context()
    cmd = SetValueCmd(EMPTY)
    assert cmd.execute(ctx) is INVALID


def test_binary_command() -> None:
    """Test binary Command execution."""
    ctx = Context()
    cmd = WriteCmd("key1", "value1")
    result = cmd.execute(ctx)
    assert result == "value1"
    assert cmd.written == ("key1", "value1")


# ============================================================================
# COMPOSITION TESTS
# ============================================================================


def test_nested_morphism_composition() -> None:
    """Test nested morphism composition."""
    ctx = Context()
    # (3 + 4) * 2 = 14
    add = AddOp(3.0, 4.0)
    mul = MulOp(add, 2.0)
    assert mul.execute(ctx) == 14.0


def test_deep_morphism_nesting() -> None:
    """Test deeply nested morphism composition."""
    ctx = Context()
    # abs(-(5 - 8)) = abs(-(-3)) = abs(3) = 3
    sub = SubOp(5.0, 8.0)  # -3
    neg = NegateOp(sub)  # 3
    abs_op = AbsOp(neg)  # 3
    assert abs_op.execute(ctx) == 3.0


def test_morphism_with_conditional() -> None:
    """Test morphism with conditional logic."""
    ctx = Context()
    # if 5 > 3 then 100 else 0
    gt = GreaterThanOp(5.0, 3.0)
    ite = IfThenElseOp(gt, 100, 0)
    assert ite.execute(ctx) == 100


def test_sentinel_propagation_through_composition() -> None:
    """Test sentinel propagation through nested morphisms."""
    ctx = Context()
    inner = NegateOp(EMPTY)  # Returns INVALID
    outer = NegateOp(inner)  # Should propagate INVALID
    assert outer.execute(ctx) is INVALID


# ============================================================================
# EDGE CASES
# ============================================================================


def test_morphism_with_none_value() -> None:
    """Test morphism handling None as a valid value (not sentinel)."""
    ctx = Context()

    class IdentityOp(Operation, UnaryMorphism[Any]):
        def _apply(self, operand: Any) -> Any:
            return operand

    op = IdentityOp(None)
    assert op.execute(ctx) is None


def test_morphism_with_zero() -> None:
    """Test morphism handling zero correctly."""
    ctx = Context()
    neg = NegateOp(0.0)
    assert neg.execute(ctx) == 0.0


def test_morphism_with_empty_string() -> None:
    """Test morphism handling empty string correctly."""
    ctx = Context()

    class LenOp(Operation, UnaryMorphism[int]):
        def _apply(self, operand: str) -> int:
            return len(operand)

    op = LenOp("")
    assert op.execute(ctx) == 0


def test_morphism_with_empty_list() -> None:
    """Test morphism handling empty list correctly."""
    ctx = Context()

    class SumOp(Operation, UnaryMorphism[int]):
        def _apply(self, operand: list) -> int:
            return sum(operand)

    op = SumOp([])
    assert op.execute(ctx) == 0


def test_operation_with_gettable_returning_sentinel() -> None:
    """Test Operation with Gettable that returns sentinel."""
    ctx = Context()
    gettable = SimpleGettable(INVALID)
    add = AddOp(gettable, 5.0)
    assert add.execute(ctx) is INVALID
