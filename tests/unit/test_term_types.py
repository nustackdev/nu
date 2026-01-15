"""Unit tests for term types and operations.

These tests verify that term types can be constructed and operations
properly chain together without requiring execution context.
"""

import pytest

from everyshape.ops import AddOp, GtOp, LtOp, MulOp, NegOp, SubOp
from everyshape.term import literal
from everyshape.types import BoolType, FloatType, IntType, ListType, StrType


class TestIntType:
    """Tests for IntType construction and operations."""

    def test_int_type_literal_creation(self):
        """IntType can wrap a literal integer."""
        x = IntType(42)
        assert x.is_literal
        assert x.source == 42
        assert x.children == ()

    def test_int_type_addition_returns_int_type(self):
        """Adding two IntTypes returns an IntType wrapping AddOp."""
        x = IntType(10)
        y = IntType(5)
        result = x + y
        assert isinstance(result, IntType)
        assert not result.is_literal
        assert isinstance(result.source, AddOp)

    def test_int_type_addition_with_literal(self):
        """IntType + int literal returns IntType."""
        x = IntType(10)
        result = x + 5
        assert isinstance(result, IntType)
        assert isinstance(result.source, AddOp)

    def test_int_type_subtraction(self):
        """IntType subtraction returns IntType wrapping SubOp."""
        x = IntType(20)
        y = IntType(8)
        result = x - y
        assert isinstance(result, IntType)
        assert isinstance(result.source, SubOp)

    def test_int_type_multiplication(self):
        """IntType multiplication returns IntType wrapping MulOp."""
        x = IntType(6)
        result = x * 7
        assert isinstance(result, IntType)
        assert isinstance(result.source, MulOp)

    def test_int_type_division_returns_float(self):
        """IntType division always returns FloatType."""
        x = IntType(10)
        result = x / 3
        assert isinstance(result, FloatType)

    def test_int_type_negation(self):
        """Negating IntType returns IntType wrapping NegOp."""
        x = IntType(42)
        result = -x
        assert isinstance(result, IntType)
        assert isinstance(result.source, NegOp)

    def test_int_type_comparison_returns_bool_type(self):
        """Comparison operations return BoolType."""
        x = IntType(10)
        result = x > 5
        assert isinstance(result, BoolType)
        assert isinstance(result.source, GtOp)

    def test_int_type_less_than(self):
        """Less than comparison returns BoolType wrapping LtOp."""
        x = IntType(3)
        result = x < 10
        assert isinstance(result, BoolType)
        assert isinstance(result.source, LtOp)

    def test_int_type_is_pure(self):
        """IntType expressions are pure."""
        x = IntType(42)
        y = x + 10
        z = y * 2
        assert x.is_pure
        assert y.is_pure
        assert z.is_pure


class TestStrType:
    """Tests for StrType construction and operations."""

    def test_str_type_literal_creation(self):
        """StrType can wrap a literal string."""
        s = StrType("hello")
        assert s.is_literal
        assert s.source == "hello"

    def test_str_type_concatenation(self):
        """StrType + str returns StrType wrapping AddOp."""
        s = StrType("hello")
        result = s + " world"
        assert isinstance(result, StrType)
        assert isinstance(result.source, AddOp)

    def test_str_type_upper_method(self):
        """StrType.upper() returns StrType with operation."""
        s = StrType("hello")
        result = s.upper()
        assert isinstance(result, StrType)
        assert not result.is_literal


class TestBoolType:
    """Tests for BoolType construction and operations."""

    def test_bool_type_literal_creation(self):
        """BoolType can wrap a literal boolean."""
        b = BoolType(True)
        assert b.is_literal
        assert b.source is True

    def test_bool_type_and_operation(self):
        """BoolType.and_() returns BoolType."""
        a = BoolType(True)
        b = BoolType(False)
        result = a.and_(b)
        assert isinstance(result, BoolType)
        assert not result.is_literal

    def test_bool_type_or_operation(self):
        """BoolType.or_() returns BoolType."""
        a = BoolType(True)
        b = BoolType(False)
        result = a.or_(b)
        assert isinstance(result, BoolType)
        assert not result.is_literal

    def test_bool_type_not_operation(self):
        """BoolType.not_() returns BoolType."""
        a = BoolType(True)
        result = a.not_()
        assert isinstance(result, BoolType)


class TestLiteral:
    """Tests for the literal() conversion function."""

    def test_literal_int(self):
        """literal() wraps int in IntType."""
        result = literal(42)
        assert isinstance(result, IntType)
        assert result.source == 42

    def test_literal_str(self):
        """literal() wraps str in StrType."""
        result = literal("hello")
        assert isinstance(result, StrType)
        assert result.source == "hello"

    def test_literal_bool(self):
        """literal() wraps bool in BoolType."""
        result = literal(True)
        assert isinstance(result, BoolType)
        assert result.source is True

    def test_literal_float(self):
        """literal() wraps float in FloatType."""
        result = literal(3.14)
        assert isinstance(result, FloatType)

    def test_literal_list(self):
        """literal() wraps list in ListType."""
        result = literal([1, 2, 3])
        assert isinstance(result, ListType)

    def test_literal_passthrough_term(self):
        """literal() passes through existing Term unchanged."""
        original = IntType(42)
        result = literal(original)
        assert result is original


class TestExpressionChaining:
    """Tests for chaining multiple operations."""

    def test_arithmetic_chain(self):
        """Multiple arithmetic operations can be chained."""
        x = IntType(10)
        y = IntType(5)
        z = IntType(2)
        result = (x + y) * z
        assert isinstance(result, IntType)
        assert isinstance(result.source, MulOp)
        # The MulOp's first child should be an IntType wrapping AddOp
        # result.source is MulOp, result.source.children[0] is the left operand
        mul_op = result.source
        left_operand = mul_op.children[0]
        assert isinstance(left_operand, IntType)
        assert isinstance(left_operand.source, AddOp)

    def test_comparison_with_arithmetic(self):
        """Comparisons can use arithmetic expressions."""
        x = IntType(5)
        y = IntType(3)
        # (5 + 3) > 7
        result = (x + y) > 7
        assert isinstance(result, BoolType)
        assert isinstance(result.source, GtOp)

    def test_logical_with_comparisons(self):
        """Logical operations can combine comparisons."""
        x = IntType(10)
        cond1 = x > 5  # True
        cond2 = x < 20  # True
        result = cond1.and_(cond2)
        assert isinstance(result, BoolType)


class TestBlockedOperators:
    """Tests for operators that are intentionally blocked."""

    def test_eq_blocked(self):
        """Using == on Terms raises TypeError."""
        x = IntType(10)
        y = IntType(10)
        with pytest.raises(TypeError, match="Cannot use =="):
            _ = x == y

    def test_ne_blocked(self):
        """Using != on Terms raises TypeError."""
        x = IntType(10)
        y = IntType(5)
        with pytest.raises(TypeError, match="Cannot use !="):
            _ = x != y

    def test_bool_conversion_blocked(self):
        """Using bool() on Terms raises TypeError."""
        x = IntType(10)
        with pytest.raises(TypeError, match="Cannot convert Term to bool"):
            bool(x)

    def test_eq_method_works(self):
        """The eq() method works for equality checks."""
        x = IntType(10)
        result = x.eq(10)
        assert isinstance(result, BoolType)

    def test_ne_method_works(self):
        """The ne() method works for inequality checks."""
        x = IntType(10)
        result = x.ne(5)
        assert isinstance(result, BoolType)
