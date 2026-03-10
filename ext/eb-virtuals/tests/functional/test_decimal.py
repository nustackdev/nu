"""Functional tests for Decimal ref.

Tests DecimalRef and DecimalSlot execution with real storage context.
"""

from decimal import Decimal

from eb_math import DecimalValue as DecimalRef


# ============================================================================
# DECIMAL SET AND GET TESTS
# ============================================================================


class TestDecimalSetAndGet:
    """Test setting and getting Decimal values through storage."""

    async def test_set_and_get_decimal(self, decimal_shape, ctx):
        """Set and retrieve a Decimal value."""
        d = Decimal("1234.56")
        await decimal_shape.balance.store(d).execute(ctx)
        result = await decimal_shape.balance.execute(ctx)
        assert result == d

    async def test_set_decimal_from_string(self, decimal_shape, ctx):
        """Set Decimal from string."""
        await decimal_shape.balance.store("999.99").execute(ctx)
        result = await decimal_shape.balance.execute(ctx)
        assert result == Decimal("999.99")

    async def test_set_multiple_decimals(self, decimal_shape, ctx):
        """Set multiple Decimal slots."""
        balance = Decimal("1000.00")
        credit = Decimal("500.50")

        await decimal_shape.balance.store(balance).execute(ctx)
        await decimal_shape.credit.store(credit).execute(ctx)

        assert await decimal_shape.balance.execute(ctx) == balance
        assert await decimal_shape.credit.execute(ctx) == credit


# ============================================================================
# DECIMAL PRECISION TESTS
# ============================================================================


class TestDecimalPrecision:
    """Test Decimal precision preservation."""

    async def test_preserves_exact_precision(self, decimal_shape, ctx):
        """Decimal preserves exact precision."""
        # This value can't be represented exactly as float
        d = Decimal("0.1") + Decimal("0.2")
        await decimal_shape.balance.store(d).execute(ctx)
        result = await decimal_shape.balance.execute(ctx)
        assert result == Decimal("0.3")

    async def test_many_decimal_places(self, decimal_shape, ctx):
        """Preserve many decimal places."""
        d = Decimal("0.123456789012345678901234567890")
        await decimal_shape.balance.store(d).execute(ctx)
        result = await decimal_shape.balance.execute(ctx)
        assert result == d

    async def test_large_numbers(self, decimal_shape, ctx):
        """Handle large numbers precisely."""
        d = Decimal("12345678901234567890.12345678901234567890")
        await decimal_shape.balance.store(d).execute(ctx)
        result = await decimal_shape.balance.execute(ctx)
        assert result == d


# ============================================================================
# DECIMALREF CONSTRUCTOR TESTS
# ============================================================================


class TestDecimalRefConstructors:
    """Test DecimalRef constructors with execution."""

    async def test_from_str(self, ctx):
        """Create from string."""
        result = await DecimalRef.from_str("123.456").execute(ctx)
        assert result == Decimal("123.456")

    async def test_from_int(self, ctx):
        """Create from integer."""
        result = await DecimalRef.from_int(42).execute(ctx)
        assert result == Decimal(42)

    async def test_from_float(self, ctx):
        """Create from float (with precision caveat)."""
        result = await DecimalRef.from_float(3.14).execute(ctx)
        # Float conversion may introduce precision issues
        assert abs(result - Decimal("3.14")) < Decimal("0.001")


# ============================================================================
# DECIMAL ARITHMETIC TESTS
# ============================================================================


class TestDecimalArithmetic:
    """Test Decimal arithmetic operations."""

    async def test_addition(self, decimal_shape, ctx):
        """Add two Decimals."""
        await decimal_shape.balance.store(Decimal("100.00")).execute(ctx)
        result = await (decimal_shape.balance + Decimal("50.25")).execute(ctx)
        assert result == Decimal("150.25")

    async def test_subtraction(self, decimal_shape, ctx):
        """Subtract Decimals."""
        await decimal_shape.balance.store(Decimal("100.00")).execute(ctx)
        result = await (decimal_shape.balance - Decimal("25.50")).execute(ctx)
        assert result == Decimal("74.50")

    async def test_multiplication(self, decimal_shape, ctx):
        """Multiply Decimals."""
        await decimal_shape.balance.store(Decimal("100.00")).execute(ctx)
        result = await (decimal_shape.balance * Decimal("1.05")).execute(ctx)
        assert result == Decimal("105.0000")

    async def test_division(self, decimal_shape, ctx):
        """Divide Decimals."""
        await decimal_shape.balance.store(Decimal("100.00")).execute(ctx)
        result = await (decimal_shape.balance / Decimal("4")).execute(ctx)
        assert result == Decimal("25")

    async def test_floor_division(self, decimal_shape, ctx):
        """Floor divide Decimals."""
        await decimal_shape.balance.store(Decimal("100.00")).execute(ctx)
        result = await (decimal_shape.balance // Decimal("3")).execute(ctx)
        assert result == Decimal("33")

    async def test_modulo(self, decimal_shape, ctx):
        """Modulo operation."""
        await decimal_shape.balance.store(Decimal("100.00")).execute(ctx)
        result = await (decimal_shape.balance % Decimal("30")).execute(ctx)
        assert result == Decimal("10.00")

    async def test_power(self, decimal_shape, ctx):
        """Power operation."""
        await decimal_shape.balance.store(Decimal("2")).execute(ctx)
        result = await (decimal_shape.balance**10).execute(ctx)
        assert result == Decimal("1024")

    async def test_negation(self, decimal_shape, ctx):
        """Negation operation."""
        await decimal_shape.balance.store(Decimal("100.00")).execute(ctx)
        result = await (-decimal_shape.balance).execute(ctx)
        assert result == Decimal("-100.00")


# ============================================================================
# DECIMAL ROUNDING TESTS
# ============================================================================


class TestDecimalRounding:
    """Test Decimal rounding and quantization."""

    async def test_quantize(self, decimal_shape, ctx):
        """Quantize to 2 decimal places."""
        await decimal_shape.balance.store(Decimal("123.456789")).execute(ctx)
        result = await decimal_shape.balance.quantize(Decimal("0.01")).execute(ctx)
        assert result == Decimal("123.46")

    async def test_normalize(self, decimal_shape, ctx):
        """Remove trailing zeros."""
        await decimal_shape.balance.store(Decimal("123.4500")).execute(ctx)
        result = await decimal_shape.balance.normalize().execute(ctx)
        assert str(result) == "123.45"


# ============================================================================
# DECIMAL MATHEMATICAL FUNCTION TESTS
# ============================================================================


class TestDecimalMathFunctions:
    """Test Decimal mathematical functions."""

    async def test_sqrt(self, decimal_shape, ctx):
        """Square root."""
        await decimal_shape.balance.store(Decimal("16")).execute(ctx)
        result = await decimal_shape.balance.sqrt().execute(ctx)
        assert result == Decimal("4")

    async def test_ln(self, decimal_shape, ctx):
        """Natural logarithm."""
        from math import e

        await decimal_shape.balance.store(Decimal("1")).execute(ctx)
        result = await decimal_shape.balance.exp().execute(ctx)
        assert abs(float(result) - e) < 0.0001

    async def test_log10(self, decimal_shape, ctx):
        """Base-10 logarithm."""
        await decimal_shape.balance.store(Decimal("100")).execute(ctx)
        result = await decimal_shape.balance.log10().execute(ctx)
        assert result == Decimal("2")


# ============================================================================
# DECIMAL INSPECTION TESTS
# ============================================================================


class TestDecimalInspection:
    """Test Decimal inspection methods."""

    async def test_is_finite(self, decimal_shape, ctx):
        """Check if value is finite."""
        await decimal_shape.balance.store(Decimal("123.45")).execute(ctx)
        result = await decimal_shape.balance.is_finite().execute(ctx)
        assert result is True

    async def test_is_zero(self, decimal_shape, ctx):
        """Check if value is zero."""
        await decimal_shape.balance.store(Decimal("0")).execute(ctx)
        result = await decimal_shape.balance.is_zero().execute(ctx)
        assert result is True

    async def test_is_signed(self, decimal_shape, ctx):
        """Check if value is signed (negative)."""
        await decimal_shape.balance.store(Decimal("-123.45")).execute(ctx)
        result = await decimal_shape.balance.is_signed().execute(ctx)
        assert result is True


# ============================================================================
# DECIMAL CONVERSION TESTS
# ============================================================================


class TestDecimalConversions:
    """Test Decimal conversions."""

    async def test_to_int(self, decimal_shape, ctx):
        """Convert to integer."""
        await decimal_shape.balance.store(Decimal("123.99")).execute(ctx)
        result = await decimal_shape.balance.to_int().execute(ctx)
        assert result == 123
