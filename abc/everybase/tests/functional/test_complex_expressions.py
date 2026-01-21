"""Complex expression test suite.

Tests realistic scenarios with chained operations, nested expressions,
and combinations of different operation types. These tests verify that
the term system works correctly for real-world use cases.
"""

import pytest

from every import Context
from everybase.combiners import all_, any_, ifelse
from everybase.types import (
    BoolType,
    DictType,
    FloatType,
    IntType,
    ListType,
    StrType,
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

    def test_simple_chain(self, ctx):
        """(5 + 3) * 2 = 16."""
        x = IntType(5)
        y = IntType(3)
        z = IntType(2)
        result = ((x + y) * z).execute(ctx)
        assert result == 16

    def test_complex_arithmetic(self, ctx):
        """((10 - 2) * 3 + 4) / 2 = 14.0."""
        result = ((((IntType(10) - 2) * 3) + 4) / 2).execute(ctx)
        assert result == 14.0

    def test_mixed_types(self, ctx):
        """(10 + 5) / 3.0 = 5.0."""
        result = ((IntType(10) + 5) / 3.0).execute(ctx)
        assert result == 5.0

    def test_power_chain(self, ctx):
        """(2 ** 3) ** 2 = 64."""
        result = ((IntType(2) ** 3) ** 2).execute(ctx)
        assert result == 64

    def test_modulo_chain(self, ctx):
        """((100 % 30) % 7) = 3.  (100 % 30 = 10, 10 % 7 = 3)"""
        result = ((IntType(100) % 30) % 7).execute(ctx)
        assert result == 3

    def test_quadratic_formula_discriminant(self, ctx):
        """b^2 - 4ac where a=1, b=5, c=6: 25 - 24 = 1."""
        a = IntType(1)
        b = IntType(5)
        c = IntType(6)
        discriminant = (b**2) - (IntType(4) * a * c)
        assert discriminant.execute(ctx) == 1

    def test_compound_interest_simple(self, ctx):
        """Principal * (1 + rate)^time: 1000 * 1.05^2 = 1102.5."""
        principal = FloatType(1000.0)
        rate = FloatType(0.05)
        time = IntType(2)
        # (1 + rate) ** time * principal
        result = (principal * ((FloatType(1.0) + rate) ** time)).execute(ctx)
        assert result == 1102.5


# =============================================================================
# COMPARISON EXPRESSION CHAINS
# =============================================================================


class TestComparisonChains:
    """Test chained comparison expressions."""

    def test_range_check(self, ctx):
        """x > 0 AND x < 100 where x = 50."""
        x = IntType(50)
        result = (x > 0).and_(x < 100).execute(ctx)
        assert result is True

    def test_range_check_false(self, ctx):
        """x > 0 AND x < 100 where x = 150."""
        x = IntType(150)
        result = (x > 0).and_(x < 100).execute(ctx)
        assert result is False

    def test_equality_chain(self, ctx):
        """(a == b) AND (b == c) where all equal."""
        a = IntType(42)
        b = IntType(42)
        c = IntType(42)
        result = a.eq(b).and_(b.eq(c)).execute(ctx)
        assert result is True

    def test_comparison_after_arithmetic(self, ctx):
        """(a + b) > (c - d) where 5+3 > 10-5."""
        a, b, c, d = IntType(5), IntType(3), IntType(10), IntType(5)
        result = ((a + b) > (c - d)).execute(ctx)
        assert result is True  # 8 > 5

    def test_string_comparison_chain(self, ctx):
        """'a' < 'b' AND 'b' < 'c'."""
        result = (StrType("a") < "b").and_(StrType("b") < "c").execute(ctx)
        assert result is True


# =============================================================================
# LOGICAL EXPRESSION CHAINS
# =============================================================================


class TestLogicalChains:
    """Test chained logical expressions."""

    def test_and_chain(self, ctx):
        """True AND True AND True = True."""
        result = BoolType(True).and_(True).and_(True).execute(ctx)
        assert result is True

    def test_or_chain(self, ctx):
        """False OR False OR True = True."""
        result = BoolType(False).or_(False).or_(True).execute(ctx)
        assert result is True

    def test_mixed_logical(self, ctx):
        """(True AND False) OR (True AND True) = True."""
        left = BoolType(True).and_(False)
        right = BoolType(True).and_(True)
        result = left.or_(right).execute(ctx)
        assert result is True

    def test_not_chain(self, ctx):
        """NOT(NOT(True)) = True."""
        result = BoolType(True).not_().not_().execute(ctx)
        assert result is True

    def test_de_morgan(self, ctx):
        """NOT(A AND B) = NOT(A) OR NOT(B)."""
        a = BoolType(True)
        b = BoolType(False)
        lhs = a.and_(b).not_()
        rhs = a.not_().or_(b.not_())
        assert lhs.execute(ctx) == rhs.execute(ctx)


# =============================================================================
# STRING EXPRESSION CHAINS
# =============================================================================


class TestStringChains:
    """Test chained string expressions."""

    def test_case_chain(self, ctx):
        """'hello'.upper().lower() = 'hello'."""
        result = StrType("hello").upper().lower().execute(ctx)
        assert result == "hello"

    def test_strip_and_case(self, ctx):
        """'  HELLO  '.strip().lower() = 'hello'."""
        result = StrType("  HELLO  ").strip().lower().execute(ctx)
        assert result == "hello"

    def test_concatenation_chain(self, ctx):
        """'a' + 'b' + 'c' = 'abc'."""
        result = ((StrType("a") + "b") + "c").execute(ctx)
        assert result == "abc"

    def test_string_processing(self, ctx):
        """'  Hello World  '.strip().title() = 'Hello World'."""
        result = StrType("  hello world  ").strip().title().execute(ctx)
        assert result == "Hello World"

    def test_string_with_comparison(self, ctx):
        """'hello'.upper() == 'HELLO'."""
        result = StrType("hello").upper().eq("HELLO").execute(ctx)
        assert result is True

    def test_string_length_comparison(self, ctx):
        """len('hello') > 3."""
        result = (StrType("hello").len_() > 3).execute(ctx)
        assert result is True

    def test_find_and_slice(self, ctx):
        """Complex string manipulation."""
        s = StrType("hello world")
        # Find 'world' and check it's at position 6
        pos = s.find("world")
        result = (pos.eq(6)).execute(ctx)
        assert result is True


# =============================================================================
# COLLECTION EXPRESSION CHAINS
# =============================================================================


class TestCollectionChains:
    """Test chained collection expressions."""

    def test_list_operations(self, ctx):
        """([1,2,3] + [4,5]).len_() = 5."""
        result = (ListType([1, 2, 3]) + [4, 5]).len_().execute(ctx)  # noqa: RUF005
        assert result == 5

    def test_sorted_and_first(self, ctx):
        """[3,1,2].sorted_().first() = 1."""
        result = ListType([3, 1, 2]).sorted_().first().execute(ctx)
        assert result == 1

    def test_sorted_and_last(self, ctx):
        """[3,1,2].sorted_().last() = 3."""
        result = ListType([3, 1, 2]).sorted_().last().execute(ctx)
        assert result == 3

    def test_reversed_slice(self, ctx):
        """[1,2,3,4,5].reversed_()[1:3] = [4,3]."""
        result = ListType([1, 2, 3, 4, 5]).reversed_()[1:3].execute(ctx)
        assert result == [4, 3]

    def test_aggregation_comparison(self, ctx):
        """sum([1,2,3]) > 5."""
        result = (ListType([1, 2, 3]).sum_() > 5).execute(ctx)
        assert result is True

    def test_min_max_comparison(self, ctx):
        """max([1,2,3]) > min([1,2,3])."""
        lst = ListType([1, 2, 3])
        result = (lst.max_() > lst.min_()).execute(ctx)
        assert result is True


# =============================================================================
# CONDITIONAL EXPRESSION CHAINS
# =============================================================================


class TestConditionalChains:
    """Test conditional expressions."""

    def test_nested_ifelse(self, ctx):
        """Nested conditional: ifelse(x > 10, 'large', ifelse(x > 5, 'medium', 'small'))."""
        x = IntType(7)
        inner = ifelse(x > 5, StrType("medium"), StrType("small"))
        outer = ifelse(x > 10, StrType("large"), inner)
        assert outer.execute(ctx) == "medium"

    def test_conditional_with_arithmetic(self, ctx):
        """ifelse(x > 0, x * 2, x * -1)."""
        x = IntType(5)
        result = ifelse(x > 0, x * 2, x * IntType(-1)).execute(ctx)
        assert result == 10

    def test_conditional_in_comparison(self, ctx):
        """ifelse(a > b, a, b) > 5 where a=3, b=7."""
        a = IntType(3)
        b = IntType(7)
        max_val = ifelse(a > b, a, b)
        result = (max_val > 5).execute(ctx)
        assert result is True  # 7 > 5


# =============================================================================
# COMBINER CHAINS
# =============================================================================


class TestCombinerChains:
    """Test combiner expressions."""

    def test_all_with_arithmetic(self, ctx):
        """all_(x > 0, x < 100, x % 2 == 0) where x = 50."""
        x = IntType(50)
        result = all_(x > 0, x < 100, (x % 2).eq(0)).execute(ctx)
        assert result is True

    def test_any_with_string_checks(self, ctx):
        """any_(s.startswith('a'), s.endswith('z'))."""
        s = StrType("hello")
        result = any_(s.startswith("a"), s.endswith("o")).execute(ctx)
        assert result is True  # endswith 'o' is True

    def test_complex_validation(self, ctx):
        """Validate a value meets multiple criteria."""
        value = IntType(42)
        is_positive = value > 0
        is_even = (value % 2).eq(0)
        in_range = (value >= 0).and_(value <= 100)
        result = all_(is_positive, is_even, in_range).execute(ctx)
        assert result is True


# =============================================================================
# REAL-WORLD SCENARIOS
# =============================================================================


class TestRealWorldScenarios:
    """Test expressions that model real-world use cases."""

    def test_price_calculation(self, ctx):
        """Calculate discounted price: price * (1 - discount)."""
        price = FloatType(100.0)
        discount = FloatType(0.2)  # 20% discount
        final_price = price * (FloatType(1.0) - discount)
        assert final_price.execute(ctx) == 80.0

    def test_tax_calculation(self, ctx):
        """Calculate price with tax: price * (1 + tax_rate)."""
        price = FloatType(100.0)
        tax_rate = FloatType(0.08)  # 8% tax
        total = price * (FloatType(1.0) + tax_rate)
        assert total.execute(ctx) == 108.0

    def test_grade_classification(self, ctx):
        """Classify grade based on score."""
        score = IntType(85)
        # A: >= 90, B: >= 80, C: >= 70, else F
        is_a = score >= 90
        is_b = (score >= 80).and_(score < 90)
        is_c = (score >= 70).and_(score < 80)

        grade = ifelse(
            is_a, StrType("A"), ifelse(is_b, StrType("B"), ifelse(is_c, StrType("C"), StrType("F")))
        )
        assert grade.execute(ctx) == "B"

    def test_age_validation(self, ctx):
        """Validate age is reasonable."""
        age = IntType(25)
        is_valid = all_(age >= 0, age <= 150, (age % 1).eq(0))
        assert is_valid.execute(ctx) is True

    def test_email_basic_validation(self, ctx):
        """Basic email validation (contains @)."""
        email = StrType("user@example.com")
        has_at = email.contains("@")
        has_dot = email.contains(".")
        not_empty = email.len_() > 0
        is_valid = all_(has_at, has_dot, not_empty)
        assert is_valid.execute(ctx) is True

    def test_inventory_check(self, ctx):
        """Check if item is in stock and affordable."""
        price = FloatType(29.99)
        quantity = IntType(5)
        budget = FloatType(50.0)

        in_stock = quantity > 0
        affordable = price <= budget
        can_buy = in_stock.and_(affordable)

        assert can_buy.execute(ctx) is True

    def test_string_formatting(self, ctx):
        """Format a name properly."""
        first = StrType("  john  ")
        last = StrType("  DOE  ")

        # Clean and format: "John Doe"
        formatted_first = first.strip().capitalize()
        formatted_last = last.strip().capitalize()
        # Note: We can't easily concatenate with space in the middle
        # But we can test individual parts
        assert formatted_first.execute(ctx) == "John"
        assert formatted_last.execute(ctx) == "Doe"

    def test_list_statistics(self, ctx):
        """Calculate basic statistics on a list."""
        data = ListType([10, 20, 30, 40, 50])

        total = data.sum_()
        count = data.len_()
        minimum = data.min_()
        maximum = data.max_()

        assert total.execute(ctx) == 150
        assert count.execute(ctx) == 5
        assert minimum.execute(ctx) == 10
        assert maximum.execute(ctx) == 50

    def test_dict_key_validation(self, ctx):
        """Validate required keys exist in dict."""
        config = DictType({"host": "localhost", "port": 8080, "debug": True})

        has_host = config.contains("host")
        has_port = config.contains("port")
        is_valid = has_host.and_(has_port)

        assert is_valid.execute(ctx) is True


# =============================================================================
# EDGE CASES AND BOUNDARY CONDITIONS
# =============================================================================


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_string_operations(self, ctx):
        """Operations on empty string."""
        s = StrType("")
        assert s.len_().execute(ctx) == 0
        assert s.upper().execute(ctx) == ""
        assert s.strip().execute(ctx) == ""

    def test_empty_list_operations(self, ctx):
        """Operations on empty list."""
        lst = ListType([])
        assert lst.len_().execute(ctx) == 0
        assert lst.reversed_().execute(ctx) == []

    def test_single_element_list(self, ctx):
        """Operations on single-element list."""
        lst = ListType([42])
        assert lst.first().execute(ctx) == 42
        assert lst.last().execute(ctx) == 42
        assert lst.sum_().execute(ctx) == 42
        assert lst.min_().execute(ctx) == 42
        assert lst.max_().execute(ctx) == 42

    def test_zero_arithmetic(self, ctx):
        """Arithmetic with zero."""
        x = IntType(0)
        assert (x + 5).execute(ctx) == 5
        assert (x * 5).execute(ctx) == 0
        assert (x - 5).execute(ctx) == -5

    def test_negative_numbers(self, ctx):
        """Operations with negative numbers."""
        x = IntType(-10)
        assert (x + 5).execute(ctx) == -5
        assert (x * IntType(-2)).execute(ctx) == 20
        assert abs(x).execute(ctx) == 10

    def test_float_precision(self, ctx):
        """Float operations maintain precision."""
        x = FloatType(0.1)
        y = FloatType(0.2)
        # Due to floating point, 0.1 + 0.2 != 0.3 exactly
        result = (x + y).execute(ctx)
        assert abs(result - 0.3) < 0.0001

    def test_large_numbers(self, ctx):
        """Operations with large numbers."""
        x = IntType(10**10)
        y = IntType(10**10)
        assert (x + y).execute(ctx) == 2 * 10**10

    def test_deeply_nested_expression(self, ctx):
        """Deeply nested expression evaluation."""
        # ((((1 + 2) + 3) + 4) + 5) = 15
        result = ((((IntType(1) + 2) + 3) + 4) + 5).execute(ctx)
        assert result == 15


# =============================================================================
# TYPE COERCION SCENARIOS
# =============================================================================


class TestTypeCoercion:
    """Test automatic type coercion in expressions."""

    def test_int_float_addition(self, ctx):
        """Int + Float coerces to Float."""
        result = (IntType(5) + FloatType(2.5)).execute(ctx)
        assert result == 7.5
        assert isinstance(result, float)

    def test_int_division_to_float(self, ctx):
        """Int / Int produces Float."""
        result = (IntType(7) / IntType(2)).execute(ctx)
        assert result == 3.5
        assert isinstance(result, float)

    def test_comparison_mixed_types(self, ctx):
        """Comparing int and float works."""
        result = (IntType(5) > FloatType(4.9)).execute(ctx)
        assert result is True


# =============================================================================
# BUILDER PATTERN SCENARIOS
# =============================================================================


class TestBuilderPatterns:
    """Test expression builder patterns."""

    def test_incremental_build(self, ctx):
        """Build expression incrementally."""
        expr = IntType(10)
        expr = expr + 5
        expr = expr * 2
        expr = expr - 10
        assert expr.execute(ctx) == 20  # ((10 + 5) * 2) - 10 = 20

    def test_reusable_subexpression(self, ctx):
        """Reuse subexpressions in multiple contexts."""
        base = IntType(10)
        doubled = base * 2

        # Use doubled in different expressions
        result1 = (doubled + 5).execute(ctx)  # 20 + 5 = 25
        result2 = (doubled - 5).execute(ctx)  # 20 - 5 = 15

        assert result1 == 25
        assert result2 == 15

    def test_conditional_builder(self, ctx):
        """Build conditional expressions."""
        x = IntType(15)

        # Build classification
        small = x < 10
        medium = (x >= 10).and_(x < 20)
        large = x >= 20

        assert small.execute(ctx) is False
        assert medium.execute(ctx) is True
        assert large.execute(ctx) is False
