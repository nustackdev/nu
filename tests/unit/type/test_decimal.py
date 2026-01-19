"""Unit tests for Decimal type.

Tests for:
- DecimalType (constructors, operations, methods)
"""

from decimal import Decimal

from everybase.type.decimal import DecimalType
from everyterm.ops import (
    AddOp,
    DivOp,
    FloorDivOp,
    FuncCallOp,
    MethodCallOp,
    ModOp,
    MulOp,
    PowOp,
    SubOp,
)
from everyterm.types import BoolType, IntType


# =============================================================================
# DECIMALTYPE CONSTRUCTION TESTS
# =============================================================================


class TestDecimalTypeConstruction:
    """DecimalType construction tests."""

    def test_from_str(self):
        """Create from string."""
        dt = DecimalType.from_str("123.456")
        assert isinstance(dt, DecimalType)
        assert isinstance(dt.source, FuncCallOp)

    def test_from_int(self):
        """Create from integer."""
        dt = DecimalType.from_int(42)
        assert isinstance(dt, DecimalType)

    def test_from_float(self):
        """Create from float."""
        dt = DecimalType.from_float(3.14)
        assert isinstance(dt, DecimalType)

    def test_from_tuple(self):
        """Create from tuple (sign, digits, exponent)."""
        dt = DecimalType.from_tuple(0, (1, 2, 3, 4, 5, 6), -3)
        assert isinstance(dt, DecimalType)


# =============================================================================
# DECIMALTYPE ARITHMETIC TESTS
# =============================================================================


class TestDecimalTypeArithmetic:
    """DecimalType arithmetic tests."""

    def test_add_returns_decimaltype(self):
        """Addition returns DecimalType."""
        dt = DecimalType.from_str("10.00")
        result = dt + Decimal("5.00")
        assert isinstance(result, DecimalType)
        assert isinstance(result.source, AddOp)

    def test_radd(self):
        """Right addition works."""
        dt = DecimalType.from_str("10.00")
        result = Decimal("5.00") + dt
        assert isinstance(result, DecimalType)

    def test_sub_returns_decimaltype(self):
        """Subtraction returns DecimalType."""
        dt = DecimalType.from_str("10.00")
        result = dt - Decimal("3.00")
        assert isinstance(result, DecimalType)
        assert isinstance(result.source, SubOp)

    def test_rsub(self):
        """Right subtraction works."""
        dt = DecimalType.from_str("10.00")
        result = Decimal("15.00") - dt
        assert isinstance(result, DecimalType)

    def test_mul_returns_decimaltype(self):
        """Multiplication returns DecimalType."""
        dt = DecimalType.from_str("10.00")
        result = dt * Decimal("2.00")
        assert isinstance(result, DecimalType)
        assert isinstance(result.source, MulOp)

    def test_rmul(self):
        """Right multiplication works."""
        dt = DecimalType.from_str("10.00")
        result = 3 * dt
        assert isinstance(result, DecimalType)

    def test_truediv_returns_decimaltype(self):
        """Division returns DecimalType."""
        dt = DecimalType.from_str("10.00")
        result = dt / Decimal("2.00")
        assert isinstance(result, DecimalType)
        assert isinstance(result.source, DivOp)

    def test_rtruediv(self):
        """Right division works."""
        dt = DecimalType.from_str("2.00")
        result = Decimal("10.00") / dt
        assert isinstance(result, DecimalType)

    def test_floordiv_returns_decimaltype(self):
        """Floor division returns DecimalType."""
        dt = DecimalType.from_str("10.00")
        result = dt // Decimal("3.00")
        assert isinstance(result, DecimalType)
        assert isinstance(result.source, FloorDivOp)

    def test_rfloordiv(self):
        """Right floor division works."""
        dt = DecimalType.from_str("3.00")
        result = Decimal("10.00") // dt
        assert isinstance(result, DecimalType)

    def test_mod_returns_decimaltype(self):
        """Modulo returns DecimalType."""
        dt = DecimalType.from_str("10.00")
        result = dt % Decimal("3.00")
        assert isinstance(result, DecimalType)
        assert isinstance(result.source, ModOp)

    def test_rmod(self):
        """Right modulo works."""
        dt = DecimalType.from_str("3.00")
        result = Decimal("10.00") % dt
        assert isinstance(result, DecimalType)

    def test_pow_returns_decimaltype(self):
        """Power returns DecimalType."""
        dt = DecimalType.from_str("2.00")
        result = dt**3
        assert isinstance(result, DecimalType)
        assert isinstance(result.source, PowOp)

    def test_neg(self):
        """Negation returns DecimalType."""
        dt = DecimalType.from_str("10.00")
        result = -dt
        assert isinstance(result, DecimalType)

    def test_pos(self):
        """Positive returns DecimalType."""
        dt = DecimalType.from_str("10.00")
        result = +dt
        assert isinstance(result, DecimalType)


# =============================================================================
# DECIMALTYPE ROUNDING AND QUANTIZATION TESTS
# =============================================================================


class TestDecimalTypeRounding:
    """DecimalType rounding and quantization tests."""

    def test_quantize_returns_decimaltype(self):
        """quantize() returns DecimalType."""
        dt = DecimalType.from_str("123.456")
        result = dt.quantize("0.01")
        assert isinstance(result, DecimalType)
        assert isinstance(result.source, MethodCallOp)

    def test_quantize_with_rounding(self):
        """quantize() with rounding mode returns DecimalType."""
        dt = DecimalType.from_str("123.456")
        result = dt.quantize("0.01", "ROUND_HALF_UP")
        assert isinstance(result, DecimalType)

    def test_normalize_returns_decimaltype(self):
        """normalize() returns DecimalType."""
        dt = DecimalType.from_str("123.4500")
        result = dt.normalize()
        assert isinstance(result, DecimalType)


# =============================================================================
# DECIMALTYPE MATHEMATICAL FUNCTION TESTS
# =============================================================================


class TestDecimalTypeMathFunctions:
    """DecimalType mathematical function tests."""

    def test_sqrt_returns_decimaltype(self):
        """sqrt() returns DecimalType."""
        dt = DecimalType.from_str("16.00")
        result = dt.sqrt()
        assert isinstance(result, DecimalType)

    def test_exp_returns_decimaltype(self):
        """exp() returns DecimalType."""
        dt = DecimalType.from_str("1.00")
        result = dt.exp()
        assert isinstance(result, DecimalType)

    def test_ln_returns_decimaltype(self):
        """ln() returns DecimalType."""
        dt = DecimalType.from_str("10.00")
        result = dt.ln()
        assert isinstance(result, DecimalType)

    def test_log10_returns_decimaltype(self):
        """log10() returns DecimalType."""
        dt = DecimalType.from_str("100.00")
        result = dt.log10()
        assert isinstance(result, DecimalType)


# =============================================================================
# DECIMALTYPE INSPECTION TESTS
# =============================================================================


class TestDecimalTypeInspection:
    """DecimalType inspection tests."""

    def test_is_finite_returns_booltype(self):
        """is_finite() returns BoolType."""
        dt = DecimalType.from_str("123.456")
        result = dt.is_finite()
        assert isinstance(result, BoolType)

    def test_is_infinite_returns_booltype(self):
        """is_infinite() returns BoolType."""
        dt = DecimalType.from_str("123.456")
        result = dt.is_infinite()
        assert isinstance(result, BoolType)

    def test_is_signed_returns_booltype(self):
        """is_signed() returns BoolType."""
        dt = DecimalType.from_str("-123.456")
        result = dt.is_signed()
        assert isinstance(result, BoolType)

    def test_is_zero_returns_booltype(self):
        """is_zero() returns BoolType."""
        dt = DecimalType.from_str("0")
        result = dt.is_zero()
        assert isinstance(result, BoolType)


# =============================================================================
# DECIMALTYPE CONVERSION TESTS
# =============================================================================


class TestDecimalTypeConversions:
    """DecimalType conversion tests."""

    def test_to_int_returns_inttype(self):
        """to_int() returns IntType."""
        dt = DecimalType.from_str("123.456")
        result = dt.to_int()
        assert isinstance(result, IntType)
