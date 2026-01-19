"""Functional tests for Fraction type.

Tests FractionType and FractionSlot execution with real storage context.
"""

from decimal import Decimal
from fractions import Fraction

from everybase.type import FractionType


# ============================================================================
# FRACTION SET AND GET TESTS
# ============================================================================


class TestFractionSetAndGet:
    """Test setting and getting fraction values through storage."""

    def test_set_and_get_fraction(self, fraction_shape, ctx):
        """Set and retrieve a fraction value."""
        f = Fraction(3, 4)
        fraction_shape.portion.set(f).execute(ctx)
        result = fraction_shape.portion.get().execute(ctx)
        assert result == f

    def test_set_fraction_integer(self, fraction_shape, ctx):
        """Set fraction as integer."""
        f = Fraction(5)
        fraction_shape.portion.set(f).execute(ctx)
        result = fraction_shape.portion.get().execute(ctx)
        assert result == f
        assert result == Fraction(5, 1)

    def test_set_fraction_from_string(self, fraction_shape, ctx):
        """Set fraction from string representation."""
        fraction_shape.portion.set("3/4").execute(ctx)
        result = fraction_shape.portion.get().execute(ctx)
        assert result == Fraction(3, 4)

    def test_set_multiple_fractions(self, fraction_shape, ctx):
        """Set multiple fraction slots."""
        portion = Fraction(1, 4)
        scale = Fraction(2, 3)

        fraction_shape.portion.set(portion).execute(ctx)
        fraction_shape.scale.set(scale).execute(ctx)

        assert fraction_shape.portion.get().execute(ctx) == portion
        assert fraction_shape.scale.get().execute(ctx) == scale


# ============================================================================
# FRACTIONTYPE CONSTRUCTOR TESTS
# ============================================================================


class TestFractionTypeConstructors:
    """Test FractionType constructors with execution."""

    def test_from_components(self, ctx):
        """Create from numerator and denominator."""
        result = FractionType.from_components(3, 4).execute(ctx)
        assert result == Fraction(3, 4)

    def test_from_components_integer(self, ctx):
        """Create from integer (denominator defaults to 1)."""
        result = FractionType.from_components(5).execute(ctx)
        assert result == Fraction(5, 1)

    def test_from_str(self, ctx):
        """Create from string."""
        result = FractionType.from_str("3/4").execute(ctx)
        assert result == Fraction(3, 4)

    def test_from_float(self, ctx):
        """Create from float."""
        result = FractionType.from_float(0.5).execute(ctx)
        assert result == Fraction(1, 2)

    def test_from_decimal(self, ctx):
        """Create from Decimal."""
        result = FractionType.from_decimal(Decimal("0.75")).execute(ctx)
        assert result == Fraction(3, 4)


# ============================================================================
# FRACTION COMPONENT ACCESS TESTS
# ============================================================================


class TestFractionComponentAccess:
    """Test accessing fraction components."""

    def test_numerator(self, fraction_shape, ctx):
        """Access numerator."""
        f = Fraction(3, 4)
        fraction_shape.portion.set(f).execute(ctx)
        result = fraction_shape.portion.numerator().execute(ctx)
        assert result == 3

    def test_denominator(self, fraction_shape, ctx):
        """Access denominator."""
        f = Fraction(3, 4)
        fraction_shape.portion.set(f).execute(ctx)
        result = fraction_shape.portion.denominator().execute(ctx)
        assert result == 4

    def test_auto_reduction(self, fraction_shape, ctx):
        """Fractions are automatically reduced."""
        f = Fraction(6, 8)  # Should reduce to 3/4
        fraction_shape.portion.set(f).execute(ctx)

        assert fraction_shape.portion.numerator().execute(ctx) == 3
        assert fraction_shape.portion.denominator().execute(ctx) == 4


# ============================================================================
# FRACTION ARITHMETIC TESTS
# ============================================================================


class TestFractionArithmetic:
    """Test fraction arithmetic operations."""

    def test_addition(self, fraction_shape, ctx):
        """Add fractions."""
        fraction_shape.portion.set(Fraction(1, 4)).execute(ctx)
        result = (fraction_shape.portion.get() + Fraction(1, 2)).execute(ctx)
        assert result == Fraction(3, 4)

    def test_addition_slots(self, fraction_shape, ctx):
        """Add two fraction slots."""
        fraction_shape.portion.set(Fraction(1, 4)).execute(ctx)
        fraction_shape.scale.set(Fraction(1, 2)).execute(ctx)

        result = (fraction_shape.portion.get() + fraction_shape.scale.get()).execute(ctx)
        assert result == Fraction(3, 4)

    def test_addition_int(self, fraction_shape, ctx):
        """Add fraction and integer."""
        fraction_shape.portion.set(Fraction(1, 4)).execute(ctx)
        result = (fraction_shape.portion.get() + 1).execute(ctx)
        assert result == Fraction(5, 4)

    def test_subtraction(self, fraction_shape, ctx):
        """Subtract fractions."""
        fraction_shape.portion.set(Fraction(3, 4)).execute(ctx)
        result = (fraction_shape.portion.get() - Fraction(1, 4)).execute(ctx)
        assert result == Fraction(1, 2)

    def test_multiplication(self, fraction_shape, ctx):
        """Multiply fractions."""
        fraction_shape.portion.set(Fraction(1, 2)).execute(ctx)
        result = (fraction_shape.portion.get() * Fraction(2, 3)).execute(ctx)
        assert result == Fraction(1, 3)

    def test_multiplication_int(self, fraction_shape, ctx):
        """Multiply fraction by integer."""
        fraction_shape.portion.set(Fraction(1, 4)).execute(ctx)
        result = (fraction_shape.portion.get() * 2).execute(ctx)
        assert result == Fraction(1, 2)

    def test_division(self, fraction_shape, ctx):
        """Divide fractions."""
        fraction_shape.portion.set(Fraction(1, 2)).execute(ctx)
        result = (fraction_shape.portion.get() / Fraction(1, 4)).execute(ctx)
        assert result == Fraction(2, 1)

    def test_floor_division(self, fraction_shape, ctx):
        """Floor divide fractions."""
        fraction_shape.portion.set(Fraction(7, 2)).execute(ctx)
        result = (fraction_shape.portion.get() // Fraction(3, 2)).execute(ctx)
        assert result == 2

    def test_modulo(self, fraction_shape, ctx):
        """Modulo operation."""
        fraction_shape.portion.set(Fraction(7, 2)).execute(ctx)
        result = (fraction_shape.portion.get() % Fraction(3, 2)).execute(ctx)
        assert result == Fraction(1, 2)

    def test_power(self, fraction_shape, ctx):
        """Raise fraction to power."""
        fraction_shape.portion.set(Fraction(2, 3)).execute(ctx)
        result = (fraction_shape.portion.get() ** 2).execute(ctx)
        assert result == Fraction(4, 9)

    def test_negation(self, fraction_shape, ctx):
        """Negate fraction."""
        fraction_shape.portion.set(Fraction(3, 4)).execute(ctx)
        result = (-fraction_shape.portion.get()).execute(ctx)
        assert result == Fraction(-3, 4)

    def test_abs(self, fraction_shape, ctx):
        """Absolute value."""
        fraction_shape.portion.set(Fraction(-3, 4)).execute(ctx)
        result = abs(fraction_shape.portion.get()).execute(ctx)
        assert result == Fraction(3, 4)


# ============================================================================
# FRACTION CONVERSION TESTS
# ============================================================================


class TestFractionConversions:
    """Test fraction conversions."""

    def test_limit_denominator(self, fraction_shape, ctx):
        """Limit denominator."""
        # pi approximation
        f = Fraction(314159265, 100000000)
        fraction_shape.portion.set(f).execute(ctx)

        result = fraction_shape.portion.limit_denominator(100).execute(ctx)
        # Should get 22/7 or similar approximation
        assert result.denominator <= 100

    def test_as_float(self, fraction_shape, ctx):
        """Convert to float."""
        fraction_shape.portion.set(Fraction(1, 2)).execute(ctx)
        result = fraction_shape.portion.as_float().execute(ctx)
        assert result == 0.5

    def test_as_integer_ratio(self, fraction_shape, ctx):
        """Get as integer ratio tuple."""
        fraction_shape.portion.set(Fraction(3, 4)).execute(ctx)
        result = fraction_shape.portion.as_integer_ratio().execute(ctx)
        assert result == (3, 4)


# ============================================================================
# FRACTION COMPARISON TESTS
# ============================================================================


class TestFractionComparison:
    """Test fraction comparison operations."""

    def test_less_than(self, fraction_shape, ctx):
        """Compare fractions with less than."""
        fraction_shape.portion.set(Fraction(1, 4)).execute(ctx)
        fraction_shape.scale.set(Fraction(1, 2)).execute(ctx)

        result = (fraction_shape.portion.get() < fraction_shape.scale.get()).execute(ctx)
        assert result is True

    def test_greater_than(self, fraction_shape, ctx):
        """Compare fractions with greater than."""
        fraction_shape.portion.set(Fraction(3, 4)).execute(ctx)
        fraction_shape.scale.set(Fraction(1, 2)).execute(ctx)

        result = (fraction_shape.portion.get() > fraction_shape.scale.get()).execute(ctx)
        assert result is True

    def test_equals(self, fraction_shape, ctx):
        """Compare fractions for equality."""
        fraction_shape.portion.set(Fraction(1, 2)).execute(ctx)
        fraction_shape.scale.set(Fraction(2, 4)).execute(ctx)

        result = (fraction_shape.portion.get() == fraction_shape.scale.get()).execute(ctx)
        assert result is True

    def test_equals_int(self, fraction_shape, ctx):
        """Compare fraction to integer."""
        fraction_shape.portion.set(Fraction(4, 2)).execute(ctx)

        result = (fraction_shape.portion.get() == 2).execute(ctx)
        assert result is True


# ============================================================================
# FRACTION PRECISION TESTS
# ============================================================================


class TestFractionPrecision:
    """Test fraction precision preservation."""

    def test_exact_representation(self, fraction_shape, ctx):
        """Fractions preserve exact values."""
        # 1/3 cannot be exactly represented as float
        fraction_shape.portion.set(Fraction(1, 3)).execute(ctx)
        result = fraction_shape.portion.get().execute(ctx)
        assert result == Fraction(1, 3)
        assert result.numerator == 1
        assert result.denominator == 3

    def test_complex_fraction(self, fraction_shape, ctx):
        """Handle complex fractions exactly."""
        # Large numerator and denominator
        f = Fraction(123456789, 987654321)
        fraction_shape.portion.set(f).execute(ctx)
        result = fraction_shape.portion.get().execute(ctx)
        assert result == f
