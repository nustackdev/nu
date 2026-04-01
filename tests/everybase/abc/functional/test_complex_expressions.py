"""Complex expression test suite.

Tests realistic scenarios with chained operations, nested expressions,
and combinations of different operation types. These tests verify that
the term system works correctly for real-world use cases.
"""

import pytest

from nu import Context
from nu import (
    BoolI,
    DictI,
    FloatI,
    IntI,
    ListI,
    StrI,
    all_,
    any_,
    fn,
)


@pytest.fixture
def ctx():
    """Create a minimal mock context for term execution."""
    return Context()


# =============================================================================
# ARITHMETIC EXPRESSION CHAINS
# =============================================================================


class TestArithmeticChains:
    """Test chained arithmetic expressions."""

    async def test_simple_chain(self, ctx):
        """(5 + 3) * 2 = 16."""
        x = IntI(5)
        y = IntI(3)
        z = IntI(2)
        result = await ((x + y) * z).execute(ctx)
        assert result == 16

    async def test_complex_arithmetic(self, ctx):
        """((10 - 2) * 3 + 4) / 2 = 14.0."""
        result = await ((((IntI(10) - 2) * 3) + 4) / 2).execute(ctx)
        assert result == 14.0

    async def test_mixed_types(self, ctx):
        """(10 + 5) / 3.0 = 5.0."""
        result = await ((IntI(10) + 5) / 3.0).execute(ctx)
        assert result == 5.0

    async def test_power_chain(self, ctx):
        """(2 ** 3) ** 2 = 64."""
        result = await ((IntI(2) ** 3) ** 2).execute(ctx)
        assert result == 64

    async def test_modulo_chain(self, ctx):
        """((100 % 30) % 7) = 3.  (100 % 30 = 10, 10 % 7 = 3)"""
        result = await ((IntI(100) % 30) % 7).execute(ctx)
        assert result == 3

    async def test_quadratic_formula_discriminant(self, ctx):
        """b^2 - 4ac where a=1, b=5, c=6: 25 - 24 = 1."""
        a = IntI(1)
        b = IntI(5)
        c = IntI(6)
        discriminant = (b**2) - (IntI(4) * a * c)
        assert await discriminant.execute(ctx) == 1

    async def test_compound_interest_simple(self, ctx):
        """Principal * (1 + rate)^time: 1000 * 1.05^2 = 1102.5."""
        principal = FloatI(1000.0)
        rate = FloatI(0.05)
        time = IntI(2)
        # (1 + rate) ** time * principal
        result = await (principal * ((FloatI(1.0) + rate) ** time)).execute(ctx)
        assert result == 1102.5


# =============================================================================
# COMPARISON EXPRESSION CHAINS
# =============================================================================


class TestComparisonChains:
    """Test chained comparison expressions."""

    async def test_range_check(self, ctx):
        """x > 0 AND x < 100 where x = 50."""
        x = IntI(50)
        result = await (x > 0).and_(x < 100).execute(ctx)
        assert result is True

    async def test_range_check_false(self, ctx):
        """x > 0 AND x < 100 where x = 150."""
        x = IntI(150)
        result = await (x > 0).and_(x < 100).execute(ctx)
        assert result is False

    async def test_equality_chain(self, ctx):
        """(a == b) AND (b == c) where all equal."""
        a = IntI(42)
        b = IntI(42)
        c = IntI(42)
        result = await a.eq(b).and_(b.eq(c)).execute(ctx)
        assert result is True

    async def test_comparison_after_arithmetic(self, ctx):
        """(a + b) > (c - d) where 5+3 > 10-5."""
        a, b, c, d = IntI(5), IntI(3), IntI(10), IntI(5)
        result = await ((a + b) > (c - d)).execute(ctx)
        assert result is True  # 8 > 5

    async def test_string_comparison_chain(self, ctx):
        """'a' < 'b' AND 'b' < 'c'."""
        result = await (StrI("a") < "b").and_(StrI("b") < "c").execute(ctx)
        assert result is True


# =============================================================================
# LOGICAL EXPRESSION CHAINS
# =============================================================================


class TestLogicalChains:
    """Test chained logical expressions."""

    async def test_and_chain(self, ctx):
        """True AND True AND True = True."""
        result = await BoolI(True).and_(True).and_(True).execute(ctx)
        assert result is True

    async def test_or_chain(self, ctx):
        """False OR False OR True = True."""
        result = await BoolI(False).or_(False).or_(True).execute(ctx)
        assert result is True

    async def test_mixed_logical(self, ctx):
        """(True AND False) OR (True AND True) = True."""
        left = BoolI(True).and_(False)
        right = BoolI(True).and_(True)
        result = await left.or_(right).execute(ctx)
        assert result is True

    async def test_not_chain(self, ctx):
        """NOT(NOT(True)) = True."""
        result = await BoolI(True).not_().not_().execute(ctx)
        assert result is True

    async def test_de_morgan(self, ctx):
        """NOT(A AND B) = NOT(A) OR NOT(B)."""
        a = BoolI(True)
        b = BoolI(False)
        lhs = a.and_(b).not_()
        rhs = a.not_().or_(b.not_())
        assert await lhs.execute(ctx) == await rhs.execute(ctx)


# =============================================================================
# STRING EXPRESSION CHAINS
# =============================================================================


class TestStringChains:
    """Test chained string expressions."""

    async def test_case_chain(self, ctx):
        """'hello'.upper().lower() = 'hello'."""
        result = await StrI("hello").upper().lower().execute(ctx)
        assert result == "hello"

    async def test_strip_and_case(self, ctx):
        """'  HELLO  '.strip().lower() = 'hello'."""
        result = await StrI("  HELLO  ").strip().lower().execute(ctx)
        assert result == "hello"

    async def test_concatenation_chain(self, ctx):
        """'a' + 'b' + 'c' = 'abc'."""
        result = await ((StrI("a") + "b") + "c").execute(ctx)
        assert result == "abc"

    async def test_string_processing(self, ctx):
        """'  Hello World  '.strip().title() = 'Hello World'."""
        result = await StrI("  hello world  ").strip().title().execute(ctx)
        assert result == "Hello World"

    async def test_string_with_comparison(self, ctx):
        """'hello'.upper() == 'HELLO'."""
        result = await StrI("hello").upper().eq("HELLO").execute(ctx)
        assert result is True

    async def test_string_length_comparison(self, ctx):
        """len('hello') > 3."""
        result = await (fn.Len(StrI("hello")) > 3).execute(ctx)
        assert result is True

    async def test_find_and_slice(self, ctx):
        """Complex string manipulation."""
        s = StrI("hello world")
        # Find 'world' and check it's at position 6
        pos = s.find("world")
        result = await (pos.eq(6)).execute(ctx)
        assert result is True


# =============================================================================
# COLLECTION EXPRESSION CHAINS
# =============================================================================


class TestCollectionChains:
    """Test chained collection expressions."""

    async def test_list_operations(self, ctx):
        """len([1,2,3] + [4,5]) = 5."""
        result = await fn.Len(ListI([1, 2, 3]) + [4, 5]).execute(ctx)  # noqa: RUF005
        assert result == 5

    async def test_sorted_and_first(self, ctx):
        """Sorted([3,1,2]).first() = 1."""
        result = await fn.Sorted(ListI([3, 1, 2])).first().execute(ctx)
        assert result == 1

    async def test_sorted_and_last(self, ctx):
        """Sorted([3,1,2]).last() = 3."""
        result = await fn.Sorted(ListI([3, 1, 2])).last().execute(ctx)
        assert result == 3

    async def test_reversed_slice(self, ctx):
        """Reversed([1,2,3,4,5]).to_list()[1:3] = [4,3]."""
        result = await fn.Reversed(ListI([1, 2, 3, 4, 5])).to_list()[1:3].execute(ctx)
        assert result == [4, 3]

    async def test_aggregation_comparison(self, ctx):
        """Sum([1,2,3]) > 5."""
        result = await (fn.Sum(ListI([1, 2, 3])) > 5).execute(ctx)
        assert result is True

    async def test_min_max_comparison(self, ctx):
        """Max([1,2,3]) > Min([1,2,3])."""
        lst = ListI([1, 2, 3])
        result = await (fn.Max(lst) > fn.Min(lst)).execute(ctx)
        assert result is True


# =============================================================================
# COMBINER CHAINS
# =============================================================================


class TestCombinerChains:
    """Test combiner expressions."""

    async def test_all_with_arithmetic(self, ctx):
        """all_(x > 0, x < 100, x % 2 == 0) where x = 50."""
        x = IntI(50)
        result = await all_(x > 0, x < 100, (x % 2).eq(0)).execute(ctx)
        assert result is True

    async def test_any_with_string_checks(self, ctx):
        """any_(s.startswith('a'), s.endswith('z'))."""
        s = StrI("hello")
        result = await any_(s.startswith("a"), s.endswith("o")).execute(ctx)
        assert result is True  # endswith 'o' is True

    async def test_complex_validation(self, ctx):
        """Validate a value meets multiple criteria."""
        value = IntI(42)
        is_positive = value > 0
        is_even = (value % 2).eq(0)
        in_range = (value >= 0).and_(value <= 100)
        result = await all_(is_positive, is_even, in_range).execute(ctx)
        assert result is True


# =============================================================================
# REAL-WORLD SCENARIOS
# =============================================================================


class TestRealWorldScenarios:
    """Test expressions that model real-world use cases."""

    async def test_price_calculation(self, ctx):
        """Calculate discounted price: price * (1 - discount)."""
        price = FloatI(100.0)
        discount = FloatI(0.2)  # 20% discount
        final_price = price * (FloatI(1.0) - discount)
        assert await final_price.execute(ctx) == 80.0

    async def test_tax_calculation(self, ctx):
        """Calculate price with tax: price * (1 + tax_rate)."""
        price = FloatI(100.0)
        tax_rate = FloatI(0.08)  # 8% tax
        total = price * (FloatI(1.0) + tax_rate)
        assert await total.execute(ctx) == 108.0

    async def test_age_validation(self, ctx):
        """Validate age is reasonable."""
        age = IntI(25)
        is_valid = all_(age >= 0, age <= 150, (age % 1).eq(0))
        assert await is_valid.execute(ctx) is True

    async def test_email_basic_validation(self, ctx):
        """Basic email validation (contains @)."""
        email = StrI("user@example.com")
        has_at = fn.Contains(email, "@")
        has_dot = fn.Contains(email, ".")
        not_empty = fn.Len(email) > 0
        is_valid = all_(has_at, has_dot, not_empty)
        assert await is_valid.execute(ctx) is True

    async def test_inventory_check(self, ctx):
        """Check if item is in stock and affordable."""
        price = FloatI(29.99)
        quantity = IntI(5)
        budget = FloatI(50.0)

        in_stock = quantity > 0
        affordable = price <= budget
        can_buy = in_stock.and_(affordable)

        assert await can_buy.execute(ctx) is True

    async def test_string_formatting(self, ctx):
        """Format a name properly."""
        first = StrI("  john  ")
        last = StrI("  DOE  ")

        # Clean and format: "John Doe"
        formatted_first = first.strip().capitalize()
        formatted_last = last.strip().capitalize()
        # Note: We can't easily concatenate with space in the middle
        # But we can test individual parts
        assert await formatted_first.execute(ctx) == "John"
        assert await formatted_last.execute(ctx) == "Doe"

    async def test_list_statistics(self, ctx):
        """Calculate basic statistics on a list."""
        data = ListI([10, 20, 30, 40, 50])

        total = fn.Sum(data)
        count = fn.Len(data)
        minimum = fn.Min(data)
        maximum = fn.Max(data)

        assert await total.execute(ctx) == 150
        assert await count.execute(ctx) == 5
        assert await minimum.execute(ctx) == 10
        assert await maximum.execute(ctx) == 50

    async def test_dict_key_validation(self, ctx):
        """Validate required keys exist in dict."""
        config = DictI({"host": "localhost", "port": 8080, "debug": True})

        has_host = fn.Contains(config, "host")
        has_port = fn.Contains(config, "port")
        is_valid = has_host.and_(has_port)

        assert await is_valid.execute(ctx) is True


# =============================================================================
# EDGE CASES AND BOUNDARY CONDITIONS
# =============================================================================


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    async def test_empty_string_operations(self, ctx):
        """Operations on empty string."""
        s = StrI("")
        assert await fn.Len(s).execute(ctx) == 0
        assert await s.upper().execute(ctx) == ""
        assert await s.strip().execute(ctx) == ""

    async def test_empty_list_operations(self, ctx):
        """Operations on empty list."""
        lst = ListI([])
        assert await fn.Len(lst).execute(ctx) == 0
        assert await fn.ToList(fn.Reversed(lst)).execute(ctx) == []

    async def test_single_element_list(self, ctx):
        """Operations on single-element list."""
        lst = ListI([42])
        assert await lst.first().execute(ctx) == 42
        assert await lst.last().execute(ctx) == 42
        assert await fn.Sum(lst).execute(ctx) == 42
        assert await fn.Min(lst).execute(ctx) == 42
        assert await fn.Max(lst).execute(ctx) == 42

    async def test_zero_arithmetic(self, ctx):
        """Arithmetic with zero."""
        x = IntI(0)
        assert await (x + 5).execute(ctx) == 5
        assert await (x * 5).execute(ctx) == 0
        assert await (x - 5).execute(ctx) == -5

    async def test_negative_numbers(self, ctx):
        """Operations with negative numbers."""
        x = IntI(-10)
        assert await (x + 5).execute(ctx) == -5
        assert await (x * IntI(-2)).execute(ctx) == 20
        assert await abs(x).execute(ctx) == 10

    async def test_float_precision(self, ctx):
        """Float operations maintain precision."""
        x = FloatI(0.1)
        y = FloatI(0.2)
        # Due to floating point, 0.1 + 0.2 != 0.3 exactly
        result = await (x + y).execute(ctx)
        assert abs(result - 0.3) < 0.0001

    async def test_large_numbers(self, ctx):
        """Operations with large numbers."""
        x = IntI(10**10)
        y = IntI(10**10)
        assert await (x + y).execute(ctx) == 2 * 10**10

    async def test_deeply_nested_expression(self, ctx):
        """Deeply nested expression evaluation."""
        # ((((1 + 2) + 3) + 4) + 5) = 15
        result = await ((((IntI(1) + 2) + 3) + 4) + 5).execute(ctx)
        assert result == 15


# =============================================================================
# TYPE COERCION SCENARIOS
# =============================================================================


class TestTypeCoercion:
    """Test automatic type coercion in expressions."""

    async def test_int_float_addition(self, ctx):
        """Int + Float coerces to Float."""
        result = await (IntI(5) + FloatI(2.5)).execute(ctx)
        assert result == 7.5
        assert isinstance(result, float)

    async def test_int_division_to_float(self, ctx):
        """Int / Int produces Float."""
        result = await (IntI(7) / IntI(2)).execute(ctx)
        assert result == 3.5
        assert isinstance(result, float)

    async def test_comparison_mixed_types(self, ctx):
        """Comparing int and float works."""
        result = await (IntI(5) > FloatI(4.9)).execute(ctx)
        assert result is True


# =============================================================================
# BUILDER PATTERN SCENARIOS
# =============================================================================


class TestBuilderPatterns:
    """Test expression builder patterns."""

    async def test_incremental_build(self, ctx):
        """Build expression incrementally."""
        expr = IntI(10)
        expr = expr + 5
        expr = expr * 2
        expr = expr - 10
        assert await expr.execute(ctx) == 20  # ((10 + 5) * 2) - 10 = 20

    async def test_reusable_subexpression(self, ctx):
        """Reuse subexpressions in multiple contexts."""
        base = IntI(10)
        doubled = base * 2

        # Use doubled in different expressions
        result1 = await (doubled + 5).execute(ctx)  # 20 + 5 = 25
        result2 = await (doubled - 5).execute(ctx)  # 20 - 5 = 15

        assert result1 == 25
        assert result2 == 15

    async def test_conditional_builder(self, ctx):
        """Build conditional expressions."""
        x = IntI(15)

        # Build classification
        small = x < 10
        medium = (x >= 10).and_(x < 20)
        large = x >= 20

        assert await small.execute(ctx) is False
        assert await medium.execute(ctx) is True
        assert await large.execute(ctx) is False
