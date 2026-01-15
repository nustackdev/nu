"""Functional tests for term execution.

These tests verify that term expressions execute correctly and produce
expected results. Uses a minimal mock context since pure expressions
don't require storage access.
"""

from unittest.mock import MagicMock

import pytest

from everyshape.term import Context, all_, any_, ifelse
from everyshape.types import BoolType, FloatType, IntType, ListType, StrType
from everyshape.typing import NAN


@pytest.fixture
def ctx():
    """Create a minimal mock context for term execution.

    For pure expressions (literals and operations), the context is
    passed through but not used for storage access.
    """
    mock_view = MagicMock()
    mock_storage_ctx = MagicMock()
    return Context.create(mock_view, mock_storage_ctx)


class TestArithmeticExecution:
    """Tests for arithmetic expression execution."""

    def test_int_addition(self, ctx):
        """IntType addition executes correctly: 5 + 3 = 8."""
        x = IntType(5)
        y = IntType(3)
        result = (x + y).execute(ctx)
        assert result == 8

    def test_int_subtraction(self, ctx):
        """IntType subtraction executes correctly: 10 - 4 = 6."""
        x = IntType(10)
        y = IntType(4)
        result = (x - y).execute(ctx)
        assert result == 6

    def test_int_multiplication(self, ctx):
        """IntType multiplication executes correctly: 6 * 7 = 42."""
        x = IntType(6)
        result = (x * 7).execute(ctx)
        assert result == 42

    def test_int_division(self, ctx):
        """IntType division executes correctly: 10 / 4 = 2.5."""
        x = IntType(10)
        result = (x / 4).execute(ctx)
        assert result == 2.5

    def test_int_floor_division(self, ctx):
        """IntType floor division executes correctly: 10 // 3 = 3."""
        x = IntType(10)
        result = (x // 3).execute(ctx)
        assert result == 3

    def test_int_modulo(self, ctx):
        """IntType modulo executes correctly: 10 % 3 = 1."""
        x = IntType(10)
        result = (x % 3).execute(ctx)
        assert result == 1

    def test_int_power(self, ctx):
        """IntType power executes correctly: 2 ** 10 = 1024."""
        x = IntType(2)
        result = (x**10).execute(ctx)
        assert result == 1024

    def test_negation(self, ctx):
        """IntType negation executes correctly: -42 = -42."""
        x = IntType(42)
        result = (-x).execute(ctx)
        assert result == -42

    def test_chained_arithmetic(self, ctx):
        """Chained arithmetic executes correctly: (5 + 3) * 2 = 16."""
        x = IntType(5)
        y = IntType(3)
        z = IntType(2)
        result = ((x + y) * z).execute(ctx)
        assert result == 16

    def test_complex_expression(self, ctx):
        """Complex expression executes: ((10 - 2) * 3) + 4 = 28."""
        result = (((IntType(10) - 2) * 3) + 4).execute(ctx)
        assert result == 28


class TestComparisonExecution:
    """Tests for comparison expression execution."""

    def test_greater_than_true(self, ctx):
        """Greater than comparison: 10 > 5 = True."""
        x = IntType(10)
        result = (x > 5).execute(ctx)
        assert result is True

    def test_greater_than_false(self, ctx):
        """Greater than comparison: 3 > 5 = False."""
        x = IntType(3)
        result = (x > 5).execute(ctx)
        assert result is False

    def test_less_than(self, ctx):
        """Less than comparison: 3 < 10 = True."""
        x = IntType(3)
        result = (x < 10).execute(ctx)
        assert result is True

    def test_greater_or_equal(self, ctx):
        """Greater or equal comparison: 5 >= 5 = True."""
        x = IntType(5)
        result = (x >= 5).execute(ctx)
        assert result is True

    def test_less_or_equal(self, ctx):
        """Less or equal comparison: 5 <= 10 = True."""
        x = IntType(5)
        result = (x <= 10).execute(ctx)
        assert result is True

    def test_equality(self, ctx):
        """Equality comparison: 42 == 42 = True."""
        x = IntType(42)
        result = x.eq(42).execute(ctx)
        assert result is True

    def test_inequality(self, ctx):
        """Inequality comparison: 42 != 10 = True."""
        x = IntType(42)
        result = x.ne(10).execute(ctx)
        assert result is True

    def test_arithmetic_then_compare(self, ctx):
        """Arithmetic result can be compared: (5 + 3) < 10 = True."""
        x = IntType(5)
        y = IntType(3)
        result = ((x + y) < 10).execute(ctx)
        assert result is True


class TestLogicalExecution:
    """Tests for logical expression execution."""

    def test_and_true(self, ctx):
        """Logical AND with both true: True AND True = True."""
        a = BoolType(True)
        b = BoolType(True)
        result = a.and_(b).execute(ctx)
        assert result is True

    def test_and_false(self, ctx):
        """Logical AND with one false: True AND False = False."""
        a = BoolType(True)
        b = BoolType(False)
        result = a.and_(b).execute(ctx)
        assert result is False

    def test_or_true(self, ctx):
        """Logical OR with one true: False OR True = True."""
        a = BoolType(False)
        b = BoolType(True)
        result = a.or_(b).execute(ctx)
        assert result is True

    def test_or_false(self, ctx):
        """Logical OR with both false: False OR False = False."""
        a = BoolType(False)
        b = BoolType(False)
        result = a.or_(b).execute(ctx)
        assert result is False

    def test_not_true(self, ctx):
        """Logical NOT: NOT True = False."""
        a = BoolType(True)
        result = a.not_().execute(ctx)
        assert result is False

    def test_not_false(self, ctx):
        """Logical NOT: NOT False = True."""
        a = BoolType(False)
        result = a.not_().execute(ctx)
        assert result is True

    def test_combined_logical(self, ctx):
        """Combined logical: (True AND False) OR True = True."""
        a = BoolType(True)
        b = BoolType(False)
        c = BoolType(True)
        result = a.and_(b).or_(c).execute(ctx)
        assert result is True

    def test_comparison_to_logical(self, ctx):
        """Comparisons can be combined with logical ops: (5 > 3) AND (10 < 20)."""
        x = IntType(5)
        y = IntType(10)
        cond1 = x > 3
        cond2 = y < 20
        result = cond1.and_(cond2).execute(ctx)
        assert result is True


class TestStringExecution:
    """Tests for string expression execution."""

    def test_string_concatenation(self, ctx):
        """String concatenation: 'hello' + ' world' = 'hello world'."""
        s = StrType("hello")
        result = (s + " world").execute(ctx)
        assert result == "hello world"

    def test_string_upper(self, ctx):
        """String upper: 'hello'.upper() = 'HELLO'."""
        s = StrType("hello")
        result = s.upper().execute(ctx)
        assert result == "HELLO"

    def test_string_lower(self, ctx):
        """String lower: 'HELLO'.lower() = 'hello'."""
        s = StrType("HELLO")
        result = s.lower().execute(ctx)
        assert result == "hello"

    def test_string_comparison(self, ctx):
        """String comparison: 'abc' < 'abd' = True."""
        s = StrType("abc")
        result = (s < "abd").execute(ctx)
        assert result is True

    def test_string_equality(self, ctx):
        """String equality: 'hello' == 'hello' = True."""
        s = StrType("hello")
        result = s.eq("hello").execute(ctx)
        assert result is True


class TestFloatExecution:
    """Tests for float expression execution."""

    def test_float_literal(self, ctx):
        """Float literal executes to value."""
        f = FloatType(3.14)
        result = f.execute(ctx)
        assert result == 3.14

    def test_float_arithmetic(self, ctx):
        """Float arithmetic: 1.5 + 2.5 = 4.0."""
        f = FloatType(1.5)
        result = (f + 2.5).execute(ctx)
        assert result == 4.0

    def test_int_plus_float_returns_float(self, ctx):
        """Int + float returns float: 5 + 2.5 = 7.5."""
        i = IntType(5)
        result = (i + 2.5).execute(ctx)
        assert result == 7.5


class TestListExecution:
    """Tests for list expression execution."""

    def test_list_literal(self, ctx):
        """List literal executes to value."""
        lst = ListType([1, 2, 3])
        result = lst.execute(ctx)
        assert result == [1, 2, 3]

    def test_list_concatenation(self, ctx):
        """List concatenation: [1,2] + [3,4] = [1,2,3,4]."""
        lst = ListType([1, 2])
        result = (lst + [3, 4]).execute(ctx)  # noqa: RUF005
        assert result == [1, 2, 3, 4]


class TestCombinerExecution:
    """Tests for combiner functions (all_, any_, ifelse, coalesce)."""

    def test_all_true(self, ctx):
        """all_() with all true conditions returns True."""
        result = all_(
            IntType(5) > 3,
            IntType(10) < 20,
            BoolType(True),
        ).execute(ctx)
        assert result is True

    def test_all_false(self, ctx):
        """all_() with one false condition returns False."""
        result = all_(
            IntType(5) > 3,
            IntType(10) > 20,  # False
            BoolType(True),
        ).execute(ctx)
        assert result is False

    def test_any_true(self, ctx):
        """any_() with at least one true returns True."""
        result = any_(
            IntType(5) > 100,  # False
            IntType(10) < 20,  # True
            BoolType(False),
        ).execute(ctx)
        assert result is True

    def test_any_false(self, ctx):
        """any_() with all false returns False."""
        result = any_(
            IntType(5) > 100,
            IntType(10) > 20,
            BoolType(False),
        ).execute(ctx)
        assert result is False

    def test_ifelse_true_branch(self, ctx):
        """ifelse() returns then_value when condition is true."""
        result = ifelse(
            IntType(10) > 5,
            IntType(100),
            IntType(0),
        ).execute(ctx)
        assert result == 100

    def test_ifelse_false_branch(self, ctx):
        """ifelse() returns else_value when condition is false."""
        result = ifelse(
            IntType(10) < 5,
            IntType(100),
            IntType(0),
        ).execute(ctx)
        assert result == 0


class TestSpecialValues:
    """Tests for special value handling (EMPTY, NAN)."""

    def test_division_by_zero_returns_nan(self, ctx):
        """Division by zero returns NAN."""
        x = IntType(10)
        result = (x / 0).execute(ctx)
        assert result is NAN

    def test_floor_division_by_zero_returns_nan(self, ctx):
        """Floor division by zero returns NAN."""
        x = IntType(10)
        result = (x // 0).execute(ctx)
        assert result is NAN

    def test_modulo_by_zero_returns_nan(self, ctx):
        """Modulo by zero returns NAN."""
        x = IntType(10)
        result = (x % 0).execute(ctx)
        assert result is NAN
