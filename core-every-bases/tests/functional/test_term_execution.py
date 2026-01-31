"""Functional tests for term execution.

These tests verify that term expressions execute correctly and produce
expected results. Uses a minimal mock context since pure expressions
don't require storage access.
"""

import pytest

from everyabc import INVALID, Context
from everybase import BoolValue, FloatValue, IntValue, ListValue, StrValue, all_, any_, ifelse


@pytest.fixture
def ctx():
    """Create a minimal mock context for term execution.

    For pure expressions (literals and operations), the context is
    passed through but not used for storage access.
    """
    return Context()


class TestArithmeticExecution:
    """Tests for arithmetic expression execution."""

    async def test_int_addition(self, ctx):
        """IntValue addition executes correctly: 5 + 3 = 8."""
        x = IntValue(5)
        y = IntValue(3)
        result = await (x + y).execute(ctx)
        assert result == 8

    async def test_int_subtraction(self, ctx):
        """IntValue subtraction executes correctly: 10 - 4 = 6."""
        x = IntValue(10)
        y = IntValue(4)
        result = await (x - y).execute(ctx)
        assert result == 6

    async def test_int_multiplication(self, ctx):
        """IntValue multiplication executes correctly: 6 * 7 = 42."""
        x = IntValue(6)
        result = await (x * 7).execute(ctx)
        assert result == 42

    async def test_int_division(self, ctx):
        """IntValue division executes correctly: 10 / 4 = 2.5."""
        x = IntValue(10)
        result = await (x / 4).execute(ctx)
        assert result == 2.5

    async def test_int_floor_division(self, ctx):
        """IntValue floor division executes correctly: 10 // 3 = 3."""
        x = IntValue(10)
        result = await (x // 3).execute(ctx)
        assert result == 3

    async def test_int_modulo(self, ctx):
        """IntValue modulo executes correctly: 10 % 3 = 1."""
        x = IntValue(10)
        result = await (x % 3).execute(ctx)
        assert result == 1

    async def test_int_power(self, ctx):
        """IntValue power executes correctly: 2 ** 10 = 1024."""
        x = IntValue(2)
        result = await (x**10).execute(ctx)
        assert result == 1024

    async def test_negation(self, ctx):
        """IntValue negation executes correctly: -42 = -42."""
        x = IntValue(42)
        result = await (-x).execute(ctx)
        assert result == -42

    async def test_chained_arithmetic(self, ctx):
        """Chained arithmetic executes correctly: (5 + 3) * 2 = 16."""
        x = IntValue(5)
        y = IntValue(3)
        z = IntValue(2)
        result = await ((x + y) * z).execute(ctx)
        assert result == 16

    async def test_complex_expression(self, ctx):
        """Complex expression executes: ((10 - 2) * 3) + 4 = 28."""
        result = await (((IntValue(10) - 2) * 3) + 4).execute(ctx)
        assert result == 28


class TestComparisonExecution:
    """Tests for comparison expression execution."""

    async def test_greater_than_true(self, ctx):
        """Greater than comparison: 10 > 5 = True."""
        x = IntValue(10)
        result = await (x > 5).execute(ctx)
        assert result is True

    async def test_greater_than_false(self, ctx):
        """Greater than comparison: 3 > 5 = False."""
        x = IntValue(3)
        result = await (x > 5).execute(ctx)
        assert result is False

    async def test_less_than(self, ctx):
        """Less than comparison: 3 < 10 = True."""
        x = IntValue(3)
        result = await (x < 10).execute(ctx)
        assert result is True

    async def test_greater_or_equal(self, ctx):
        """Greater or equal comparison: 5 >= 5 = True."""
        x = IntValue(5)
        result = await (x >= 5).execute(ctx)
        assert result is True

    async def test_less_or_equal(self, ctx):
        """Less or equal comparison: 5 <= 10 = True."""
        x = IntValue(5)
        result = await (x <= 10).execute(ctx)
        assert result is True

    async def test_equality(self, ctx):
        """Equality comparison: 42 == 42 = True."""
        x = IntValue(42)
        result = await x.eq(42).execute(ctx)
        assert result is True

    async def test_inequality(self, ctx):
        """Inequality comparison: 42 != 10 = True."""
        x = IntValue(42)
        result = await x.ne(10).execute(ctx)
        assert result is True

    async def test_arithmetic_then_compare(self, ctx):
        """Arithmetic result can be compared: (5 + 3) < 10 = True."""
        x = IntValue(5)
        y = IntValue(3)
        result = await ((x + y) < 10).execute(ctx)
        assert result is True


class TestLogicalExecution:
    """Tests for logical expression execution."""

    async def test_and_true(self, ctx):
        """Logical AND with both true: True AND True = True."""
        a = BoolValue(True)
        b = BoolValue(True)
        result = await a.and_(b).execute(ctx)
        assert result is True

    async def test_and_false(self, ctx):
        """Logical AND with one false: True AND False = False."""
        a = BoolValue(True)
        b = BoolValue(False)
        result = await a.and_(b).execute(ctx)
        assert result is False

    async def test_or_true(self, ctx):
        """Logical OR with one true: False OR True = True."""
        a = BoolValue(False)
        b = BoolValue(True)
        result = await a.or_(b).execute(ctx)
        assert result is True

    async def test_or_false(self, ctx):
        """Logical OR with both false: False OR False = False."""
        a = BoolValue(False)
        b = BoolValue(False)
        result = await a.or_(b).execute(ctx)
        assert result is False

    async def test_not_true(self, ctx):
        """Logical NOT: NOT True = False."""
        a = BoolValue(True)
        result = await a.not_().execute(ctx)
        assert result is False

    async def test_not_false(self, ctx):
        """Logical NOT: NOT False = True."""
        a = BoolValue(False)
        result = await a.not_().execute(ctx)
        assert result is True

    async def test_combined_logical(self, ctx):
        """Combined logical: (True AND False) OR True = True."""
        a = BoolValue(True)
        b = BoolValue(False)
        c = BoolValue(True)
        result = await a.and_(b).or_(c).execute(ctx)
        assert result is True

    async def test_comparison_to_logical(self, ctx):
        """Comparisons can be combined with logical ops: (5 > 3) AND (10 < 20)."""
        x = IntValue(5)
        y = IntValue(10)
        cond1 = x > 3
        cond2 = y < 20
        result = await cond1.and_(cond2).execute(ctx)
        assert result is True


class TestStringExecution:
    """Tests for string expression execution."""

    async def test_string_concatenation(self, ctx):
        """String concatenation: 'hello' + ' world' = 'hello world'."""
        s = StrValue("hello")
        result = await (s + " world").execute(ctx)
        assert result == "hello world"

    async def test_string_upper(self, ctx):
        """String upper: 'hello'.upper() = 'HELLO'."""
        s = StrValue("hello")
        result = await s.upper().execute(ctx)
        assert result == "HELLO"

    async def test_string_lower(self, ctx):
        """String lower: 'HELLO'.lower() = 'hello'."""
        s = StrValue("HELLO")
        result = await s.lower().execute(ctx)
        assert result == "hello"

    async def test_string_comparison(self, ctx):
        """String comparison: 'abc' < 'abd' = True."""
        s = StrValue("abc")
        result = await (s < "abd").execute(ctx)
        assert result is True

    async def test_string_equality(self, ctx):
        """String equality: 'hello' == 'hello' = True."""
        s = StrValue("hello")
        result = await s.eq("hello").execute(ctx)
        assert result is True


class TestFloatExecution:
    """Tests for float expression execution."""

    async def test_float_ensure_term(self, ctx):
        """Float literal executes to value."""
        f = FloatValue(3.14)
        result = await f.execute(ctx)
        assert result == 3.14

    async def test_float_arithmetic(self, ctx):
        """Float arithmetic: 1.5 + 2.5 = 4.0."""
        f = FloatValue(1.5)
        result = await (f + 2.5).execute(ctx)
        assert result == 4.0

    async def test_int_plus_float_returns_float(self, ctx):
        """Int + float returns float: 5 + 2.5 = 7.5."""
        i = IntValue(5)
        result = await (i + 2.5).execute(ctx)
        assert result == 7.5


class TestListExecution:
    """Tests for list expression execution."""

    async def test_list_ensure_term(self, ctx):
        """List literal executes to value."""
        lst = ListValue([1, 2, 3])
        result = await lst.execute(ctx)
        assert result == [1, 2, 3]

    async def test_list_concatenation(self, ctx):
        """List concatenation: [1,2] + [3,4] = [1,2,3,4]."""
        lst = ListValue([1, 2])
        result = await (lst + [3, 4]).execute(ctx)  # noqa: RUF005
        assert result == [1, 2, 3, 4]


class TestCombinerExecution:
    """Tests for combiner functions (all_, any_, ifelse, coalesce)."""

    async def test_all_true(self, ctx):
        """all_() with all true conditions returns True."""
        result = await all_(
            IntValue(5) > 3,
            IntValue(10) < 20,
            BoolValue(True),
        ).execute(ctx)
        assert result is True

    async def test_all_false(self, ctx):
        """all_() with one false condition returns False."""
        result = await all_(
            IntValue(5) > 3,
            IntValue(10) > 20,  # False
            BoolValue(True),
        ).execute(ctx)
        assert result is False

    async def test_any_true(self, ctx):
        """any_() with at least one true returns True."""
        result = await any_(
            IntValue(5) > 100,  # False
            IntValue(10) < 20,  # True
            BoolValue(False),
        ).execute(ctx)
        assert result is True

    async def test_any_false(self, ctx):
        """any_() with all false returns False."""
        result = await any_(
            IntValue(5) > 100,
            IntValue(10) > 20,
            BoolValue(False),
        ).execute(ctx)
        assert result is False

    async def test_ifelse_true_branch(self, ctx):
        """ifelse() returns then_value when condition is true."""
        result = await ifelse(
            IntValue(10) > 5,
            IntValue(100),
            IntValue(0),
        ).execute(ctx)
        assert result == 100

    async def test_ifelse_false_branch(self, ctx):
        """ifelse() returns else_value when condition is false."""
        result = await ifelse(
            IntValue(10) < 5,
            IntValue(100),
            IntValue(0),
        ).execute(ctx)
        assert result == 0


class TestSpecialValues:
    """Tests for special value handling (EMPTY, INVALID)."""

    async def test_division_by_zero_returns_nan(self, ctx):
        """Division by zero returns INVALID."""
        x = IntValue(10)
        result = await (x / 0).execute(ctx)
        assert result is INVALID

    async def test_floor_division_by_zero_returns_nan(self, ctx):
        """Floor division by zero returns INVALID."""
        x = IntValue(10)
        result = await (x // 0).execute(ctx)
        assert result is INVALID

    async def test_modulo_by_zero_returns_nan(self, ctx):
        """Modulo by zero returns INVALID."""
        x = IntValue(10)
        result = await (x % 0).execute(ctx)
        assert result is INVALID
