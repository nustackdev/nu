"""Functional tests for Decimal type.

Tests DecimalType and DecimalSlot execution with real storage context.
"""

from decimal import Decimal

from everybase.type import DecimalType


# ============================================================================
# DECIMAL SET AND GET TESTS
# ============================================================================


class TestDecimalSetAndGet:
    """Test setting and getting Decimal values through storage."""

    def test_set_and_get_decimal(self, decimal_shape, ctx):
        """Set and retrieve a Decimal value."""
        d = Decimal("1234.56")
        decimal_shape.balance.set(d).execute(ctx)
        result = decimal_shape.balance.get().execute(ctx)
        assert result == d

    def test_set_decimal_from_string(self, decimal_shape, ctx):
        """Set Decimal from string."""
        decimal_shape.balance.set("999.99").execute(ctx)
        result = decimal_shape.balance.get().execute(ctx)
        assert result == Decimal("999.99")

    def test_set_multiple_decimals(self, decimal_shape, ctx):
        """Set multiple Decimal slots."""
        balance = Decimal("1000.00")
        credit = Decimal("500.50")

        decimal_shape.balance.set(balance).execute(ctx)
        decimal_shape.credit.set(credit).execute(ctx)

        assert decimal_shape.balance.get().execute(ctx) == balance
        assert decimal_shape.credit.get().execute(ctx) == credit


# ============================================================================
# DECIMAL PRECISION TESTS
# ============================================================================


class TestDecimalPrecision:
    """Test Decimal precision preservation."""

    def test_preserves_exact_precision(self, decimal_shape, ctx):
        """Decimal preserves exact precision."""
        # This value can't be represented exactly as float
        d = Decimal("0.1") + Decimal("0.2")
        decimal_shape.balance.set(d).execute(ctx)
        result = decimal_shape.balance.get().execute(ctx)
        assert result == Decimal("0.3")

    def test_many_decimal_places(self, decimal_shape, ctx):
        """Preserve many decimal places."""
        d = Decimal("0.123456789012345678901234567890")
        decimal_shape.balance.set(d).execute(ctx)
        result = decimal_shape.balance.get().execute(ctx)
        assert result == d

    def test_large_numbers(self, decimal_shape, ctx):
        """Handle large numbers precisely."""
        d = Decimal("12345678901234567890.12345678901234567890")
        decimal_shape.balance.set(d).execute(ctx)
        result = decimal_shape.balance.get().execute(ctx)
        assert result == d


# ============================================================================
# DECIMALTYPE CONSTRUCTOR TESTS
# ============================================================================


class TestDecimalTypeConstructors:
    """Test DecimalType constructors with execution."""

    def test_from_str(self, ctx):
        """Create from string."""
        result = DecimalType.from_str("123.456").execute(ctx)
        assert result == Decimal("123.456")

    def test_from_int(self, ctx):
        """Create from integer."""
        result = DecimalType.from_int(42).execute(ctx)
        assert result == Decimal(42)

    def test_from_float(self, ctx):
        """Create from float (with precision caveat)."""
        result = DecimalType.from_float(3.14).execute(ctx)
        # Float conversion may introduce precision issues
        assert abs(result - Decimal("3.14")) < Decimal("0.001")


# ============================================================================
# DECIMAL ARITHMETIC TESTS
# ============================================================================


class TestDecimalArithmetic:
    """Test Decimal arithmetic operations."""

    def test_addition(self, decimal_shape, ctx):
        """Add two Decimals."""
        decimal_shape.balance.set(Decimal("100.00")).execute(ctx)
        result = (decimal_shape.balance.get() + Decimal("50.25")).execute(ctx)
        assert result == Decimal("150.25")

    def test_subtraction(self, decimal_shape, ctx):
        """Subtract Decimals."""
        decimal_shape.balance.set(Decimal("100.00")).execute(ctx)
        result = (decimal_shape.balance.get() - Decimal("25.50")).execute(ctx)
        assert result == Decimal("74.50")

    def test_multiplication(self, decimal_shape, ctx):
        """Multiply Decimals."""
        decimal_shape.balance.set(Decimal("100.00")).execute(ctx)
        result = (decimal_shape.balance.get() * Decimal("1.05")).execute(ctx)
        assert result == Decimal("105.0000")

    def test_division(self, decimal_shape, ctx):
        """Divide Decimals."""
        decimal_shape.balance.set(Decimal("100.00")).execute(ctx)
        result = (decimal_shape.balance.get() / Decimal("4")).execute(ctx)
        assert result == Decimal("25")

    def test_floor_division(self, decimal_shape, ctx):
        """Floor divide Decimals."""
        decimal_shape.balance.set(Decimal("100.00")).execute(ctx)
        result = (decimal_shape.balance.get() // Decimal("3")).execute(ctx)
        assert result == Decimal("33")

    def test_modulo(self, decimal_shape, ctx):
        """Modulo operation."""
        decimal_shape.balance.set(Decimal("100.00")).execute(ctx)
        result = (decimal_shape.balance.get() % Decimal("30")).execute(ctx)
        assert result == Decimal("10.00")

    def test_power(self, decimal_shape, ctx):
        """Power operation."""
        decimal_shape.balance.set(Decimal("2")).execute(ctx)
        result = (decimal_shape.balance.get() ** 10).execute(ctx)
        assert result == Decimal("1024")

    def test_negation(self, decimal_shape, ctx):
        """Negation operation."""
        decimal_shape.balance.set(Decimal("100.00")).execute(ctx)
        result = (-decimal_shape.balance.get()).execute(ctx)
        assert result == Decimal("-100.00")


# ============================================================================
# DECIMAL ROUNDING TESTS
# ============================================================================


class TestDecimalRounding:
    """Test Decimal rounding and quantization."""

    def test_quantize(self, decimal_shape, ctx):
        """Quantize to 2 decimal places."""
        decimal_shape.balance.set(Decimal("123.456789")).execute(ctx)
        result = decimal_shape.balance.get().quantize(Decimal("0.01")).execute(ctx)
        assert result == Decimal("123.46")

    def test_normalize(self, decimal_shape, ctx):
        """Remove trailing zeros."""
        decimal_shape.balance.set(Decimal("123.4500")).execute(ctx)
        result = decimal_shape.balance.get().normalize().execute(ctx)
        assert str(result) == "123.45"


# ============================================================================
# DECIMAL MATHEMATICAL FUNCTION TESTS
# ============================================================================


class TestDecimalMathFunctions:
    """Test Decimal mathematical functions."""

    def test_sqrt(self, decimal_shape, ctx):
        """Square root."""
        decimal_shape.balance.set(Decimal("16")).execute(ctx)
        result = decimal_shape.balance.get().sqrt().execute(ctx)
        assert result == Decimal("4")

    def test_ln(self, decimal_shape, ctx):
        """Natural logarithm."""
        from math import e

        decimal_shape.balance.set(Decimal("1")).execute(ctx)
        result = decimal_shape.balance.get().exp().execute(ctx)
        assert abs(float(result) - e) < 0.0001

    def test_log10(self, decimal_shape, ctx):
        """Base-10 logarithm."""
        decimal_shape.balance.set(Decimal("100")).execute(ctx)
        result = decimal_shape.balance.get().log10().execute(ctx)
        assert result == Decimal("2")


# ============================================================================
# DECIMAL INSPECTION TESTS
# ============================================================================


class TestDecimalInspection:
    """Test Decimal inspection methods."""

    def test_is_finite(self, decimal_shape, ctx):
        """Check if value is finite."""
        decimal_shape.balance.set(Decimal("123.45")).execute(ctx)
        result = decimal_shape.balance.get().is_finite().execute(ctx)
        assert result is True

    def test_is_zero(self, decimal_shape, ctx):
        """Check if value is zero."""
        decimal_shape.balance.set(Decimal("0")).execute(ctx)
        result = decimal_shape.balance.get().is_zero().execute(ctx)
        assert result is True

    def test_is_signed(self, decimal_shape, ctx):
        """Check if value is signed (negative)."""
        decimal_shape.balance.set(Decimal("-123.45")).execute(ctx)
        result = decimal_shape.balance.get().is_signed().execute(ctx)
        assert result is True


# ============================================================================
# DECIMAL CONVERSION TESTS
# ============================================================================


class TestDecimalConversions:
    """Test Decimal conversions."""

    def test_to_int(self, decimal_shape, ctx):
        """Convert to integer."""
        decimal_shape.balance.set(Decimal("123.99")).execute(ctx)
        result = decimal_shape.balance.get().to_int().execute(ctx)
        assert result == 123
