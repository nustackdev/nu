"""Unit tests for term types and operations.

These tests verify that term types can be constructed and operations
properly chain together without requiring execution context.
"""

import pytest

from everybase import (
    AddOp,
    BoolRef,
    FloatRef,
    GtOp,
    IntRef,
    ListRef,
    LtOp,
    MulOp,
    NegOp,
    StrRef,
    SubOp,
    ensure_term,
)


class TestIntRef:
    """Tests for IntRef construction and operations."""

    def test_int_type_literal_creation(self):
        """IntRef can wrap a literal integer."""
        x = IntRef(42)
        assert x.source == 42

    def test_int_type_addition_returns_int_type(self):
        """Adding two IntRefs returns an IntRef wrapping AddOp."""
        x = IntRef(10)
        y = IntRef(5)
        result = x + y
        assert isinstance(result, IntRef)

        assert isinstance(result.source, AddOp)

    def test_int_type_addition_with_ensure_term(self):
        """IntRef + int literal returns IntRef."""
        x = IntRef(10)
        result = x + 5
        assert isinstance(result, IntRef)
        assert isinstance(result.source, AddOp)

    def test_int_type_subtraction(self):
        """IntRef subtraction returns IntRef wrapping SubOp."""
        x = IntRef(20)
        y = IntRef(8)
        result = x - y
        assert isinstance(result, IntRef)
        assert isinstance(result.source, SubOp)

    def test_int_type_multiplication(self):
        """IntRef multiplication returns IntRef wrapping MulOp."""
        x = IntRef(6)
        result = x * 7
        assert isinstance(result, IntRef)
        assert isinstance(result.source, MulOp)

    def test_int_type_division_returns_float(self):
        """IntRef division always returns FloatRef."""
        x = IntRef(10)
        result = x / 3
        assert isinstance(result, FloatRef)

    def test_int_type_negation(self):
        """Negating IntRef returns IntRef wrapping NegOp."""
        x = IntRef(42)
        result = -x
        assert isinstance(result, IntRef)
        assert isinstance(result.source, NegOp)

    def test_int_type_comparison_returns_bool_type(self):
        """Comparison operations return BoolRef."""
        x = IntRef(10)
        result = x > 5
        assert isinstance(result, BoolRef)
        assert isinstance(result.source, GtOp)

    def test_int_type_less_than(self):
        """Less than comparison returns BoolRef wrapping LtOp."""
        x = IntRef(3)
        result = x < 10
        assert isinstance(result, BoolRef)
        assert isinstance(result.source, LtOp)

    def test_int_type_is_pure(self):
        """IntRef expressions are pure."""
        x = IntRef(42)
        y = x + 10
        z = y * 2
        assert x.is_self_pure
        assert y.is_self_pure
        assert z.is_self_pure


class TestStrRef:
    """Tests for StrRef construction and operations."""

    def test_str_type_literal_creation(self):
        """StrRef can wrap a literal string."""
        s = StrRef("hello")

        assert s.source == "hello"

    def test_str_type_concatenation(self):
        """StrRef + str returns StrRef wrapping AddOp."""
        s = StrRef("hello")
        result = s + " world"
        assert isinstance(result, StrRef)
        assert isinstance(result.source, AddOp)

    def test_str_type_upper_method(self):
        """StrRef.upper() returns StrRef with operation."""
        s = StrRef("hello")
        result = s.upper()
        assert isinstance(result, StrRef)


class TestBoolRef:
    """Tests for BoolRef construction and operations."""

    def test_bool_type_literal_creation(self):
        """BoolRef can wrap a literal boolean."""
        b = BoolRef(True)

        assert b.source is True

    def test_bool_type_and_operation(self):
        """BoolRef.and_() returns BoolRef."""
        a = BoolRef(True)
        b = BoolRef(False)
        result = a.and_(b)
        assert isinstance(result, BoolRef)

    def test_bool_type_or_operation(self):
        """BoolRef.or_() returns BoolRef."""
        a = BoolRef(True)
        b = BoolRef(False)
        result = a.or_(b)
        assert isinstance(result, BoolRef)

    def test_bool_type_not_operation(self):
        """BoolRef.not_() returns BoolRef."""
        a = BoolRef(True)
        result = a.not_()
        assert isinstance(result, BoolRef)


class TestEnsureTerm:
    """Tests for the ensure_term() conversion function."""

    def test_ensure_term_int(self):
        """ensure_term() wraps int in IntRef."""
        result = ensure_term(42)
        assert isinstance(result, IntRef)
        assert result.source == 42

    def test_ensure_term_str(self):
        """ensure_term() wraps str in StrRef."""
        result = ensure_term("hello")
        assert isinstance(result, StrRef)
        assert result.source == "hello"

    def test_ensure_term_bool(self):
        """ensure_term() wraps bool in BoolRef."""
        result = ensure_term(True)
        assert isinstance(result, BoolRef)
        assert result.source is True

    def test_ensure_term_float(self):
        """ensure_term() wraps float in FloatRef."""
        result = ensure_term(3.14)
        assert isinstance(result, FloatRef)

    def test_ensure_term_list(self):
        """ensure_term() wraps list in ListRef."""
        result = ensure_term([1, 2, 3])
        assert isinstance(result, ListRef)

    def test_ensure_term_passthrough(self):
        """ensure_term() passes through existing Term unchanged."""
        original = IntRef(42)
        result = ensure_term(original)
        assert result is original


class TestExpressionChaining:
    """Tests for chaining multiple operations."""

    def test_arithmetic_chain(self):
        """Multiple arithmetic operations can be chained."""
        x = IntRef(10)
        y = IntRef(5)
        z = IntRef(2)
        result = (x + y) * z
        assert isinstance(result, IntRef)
        assert isinstance(result.source, MulOp)
        # The MulOp's first child should be an IntRef wrapping AddOp
        # result.source is MulOp, result.source.children[0] is the left operand
        mul_op = result.source
        left_operand = mul_op.children[0]
        assert isinstance(left_operand, IntRef)
        assert isinstance(left_operand.source, AddOp)

    def test_comparison_with_arithmetic(self):
        """Comparisons can use arithmetic expressions."""
        x = IntRef(5)
        y = IntRef(3)
        # (5 + 3) > 7
        result = (x + y) > 7
        assert isinstance(result, BoolRef)
        assert isinstance(result.source, GtOp)

    def test_logical_with_comparisons(self):
        """Logical operations can combine comparisons."""
        x = IntRef(10)
        cond1 = x > 5  # True
        cond2 = x < 20  # True
        result = cond1.and_(cond2)
        assert isinstance(result, BoolRef)


class TestBlockedOperators:
    """Tests for operators that are intentionally blocked."""

    def test_eq_blocked(self):
        """Using == on Terms raises TypeError."""
        x = IntRef(10)
        y = IntRef(10)
        with pytest.raises(TypeError, match="Cannot use =="):
            _ = x == y

    def test_ne_blocked(self):
        """Using != on Terms raises TypeError."""
        x = IntRef(10)
        y = IntRef(5)
        with pytest.raises(TypeError, match="Cannot use !="):
            _ = x != y

    def test_bool_conversion_blocked(self):
        """Using bool() on Terms raises TypeError."""
        x = IntRef(10)
        with pytest.raises(TypeError, match="Cannot convert Term to bool"):
            bool(x)

    def test_eq_method_works(self):
        """The eq() method works for equality checks."""
        x = IntRef(10)
        result = x.eq(10)
        assert isinstance(result, BoolRef)

    def test_ne_method_works(self):
        """The ne() method works for inequality checks."""
        x = IntRef(10)
        result = x.ne(5)
        assert isinstance(result, BoolRef)
