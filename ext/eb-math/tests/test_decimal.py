"""Unit tests for Decimal ref.

Tests for:
- DecimalRef (constructors, operations, methods)
"""

from decimal import Decimal

from eb_math import DecimalValue as DecimalRef
from everybase.abc import (
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
from everybase.abc import BoolValue as BoolRef
from everybase.abc import IntValue as IntRef


# =============================================================================
# DECIMALREF CONSTRUCTION TESTS
# =============================================================================


class TestDecimalRefConstruction:
    """DecimalRef construction tests."""

    def test_from_str(self):
        """Create from string."""
        dt = DecimalRef.from_str("123.456")
        assert isinstance(dt, DecimalRef)
        assert isinstance(dt.source, FuncCallOp)

    def test_from_int(self):
        """Create from integer."""
        dt = DecimalRef.from_int(42)
        assert isinstance(dt, DecimalRef)

    def test_from_float(self):
        """Create from float."""
        dt = DecimalRef.from_float(3.14)
        assert isinstance(dt, DecimalRef)


# =============================================================================
# DECIMALREF ARITHMETIC TESTS
# =============================================================================


class TestDecimalRefArithmetic:
    """DecimalRef arithmetic tests."""

    def test_add_returns_decimalref(self):
        """Addition returns DecimalRef."""
        dt = DecimalRef.from_str("10.00")
        result = dt + Decimal("5.00")
        assert isinstance(result, DecimalRef)
        assert isinstance(result.source, AddOp)

    def test_radd(self):
        """Right addition works."""
        dt = DecimalRef.from_str("10.00")
        result = Decimal("5.00") + dt
        assert isinstance(result, DecimalRef)

    def test_sub_returns_decimalref(self):
        """Subtraction returns DecimalRef."""
        dt = DecimalRef.from_str("10.00")
        result = dt - Decimal("3.00")
        assert isinstance(result, DecimalRef)
        assert isinstance(result.source, SubOp)

    def test_rsub(self):
        """Right subtraction works."""
        dt = DecimalRef.from_str("10.00")
        result = Decimal("15.00") - dt
        assert isinstance(result, DecimalRef)

    def test_mul_returns_decimalref(self):
        """Multiplication returns DecimalRef."""
        dt = DecimalRef.from_str("10.00")
        result = dt * Decimal("2.00")
        assert isinstance(result, DecimalRef)
        assert isinstance(result.source, MulOp)

    def test_rmul(self):
        """Right multiplication works."""
        dt = DecimalRef.from_str("10.00")
        result = 3 * dt
        assert isinstance(result, DecimalRef)

    def test_truediv_returns_decimalref(self):
        """Division returns DecimalRef."""
        dt = DecimalRef.from_str("10.00")
        result = dt / Decimal("2.00")
        assert isinstance(result, DecimalRef)
        assert isinstance(result.source, DivOp)

    def test_rtruediv(self):
        """Right division works."""
        dt = DecimalRef.from_str("2.00")
        result = Decimal("10.00") / dt
        assert isinstance(result, DecimalRef)

    def test_floordiv_returns_decimalref(self):
        """Floor division returns DecimalRef."""
        dt = DecimalRef.from_str("10.00")
        result = dt // Decimal("3.00")
        assert isinstance(result, DecimalRef)
        assert isinstance(result.source, FloorDivOp)

    def test_mod_returns_decimalref(self):
        """Modulo returns DecimalRef."""
        dt = DecimalRef.from_str("10.00")
        result = dt % Decimal("3.00")
        assert isinstance(result, DecimalRef)
        assert isinstance(result.source, ModOp)

    def test_pow_returns_decimalref(self):
        """Power returns DecimalRef."""
        dt = DecimalRef.from_str("2.00")
        result = dt**3
        assert isinstance(result, DecimalRef)
        assert isinstance(result.source, PowOp)

    def test_neg(self):
        """Negation returns DecimalRef."""
        dt = DecimalRef.from_str("10.00")
        result = -dt
        assert isinstance(result, DecimalRef)


# =============================================================================
# DECIMALREF ROUNDING AND QUANTIZATION TESTS
# =============================================================================


class TestDecimalRefRounding:
    """DecimalRef rounding and quantization tests."""

    def test_quantize_returns_decimalref(self):
        """quantize() returns DecimalRef."""
        dt = DecimalRef.from_str("123.456")
        result = dt.quantize("0.01")
        assert isinstance(result, DecimalRef)
        assert isinstance(result.source, MethodCallOp)

    def test_quantize_with_rounding(self):
        """quantize() with rounding mode returns DecimalRef."""
        dt = DecimalRef.from_str("123.456")
        result = dt.quantize("0.01", "ROUND_HALF_UP")
        assert isinstance(result, DecimalRef)

    def test_normalize_returns_decimalref(self):
        """normalize() returns DecimalRef."""
        dt = DecimalRef.from_str("123.4500")
        result = dt.normalize()
        assert isinstance(result, DecimalRef)


# =============================================================================
# DECIMALREF MATHEMATICAL FUNCTION TESTS
# =============================================================================


class TestDecimalRefMathFunctions:
    """DecimalRef mathematical function tests."""

    def test_sqrt_returns_decimalref(self):
        """sqrt() returns DecimalRef."""
        dt = DecimalRef.from_str("16.00")
        result = dt.sqrt()
        assert isinstance(result, DecimalRef)

    def test_exp_returns_decimalref(self):
        """exp() returns DecimalRef."""
        dt = DecimalRef.from_str("1.00")
        result = dt.exp()
        assert isinstance(result, DecimalRef)

    def test_ln_returns_decimalref(self):
        """ln() returns DecimalRef."""
        dt = DecimalRef.from_str("10.00")
        result = dt.ln()
        assert isinstance(result, DecimalRef)

    def test_log10_returns_decimalref(self):
        """log10() returns DecimalRef."""
        dt = DecimalRef.from_str("100.00")
        result = dt.log10()
        assert isinstance(result, DecimalRef)


# =============================================================================
# DECIMALREF INSPECTION TESTS
# =============================================================================


class TestDecimalRefInspection:
    """DecimalRef inspection tests."""

    def test_is_finite_returns_boolref(self):
        """is_finite() returns BoolRef."""
        dt = DecimalRef.from_str("123.456")
        result = dt.is_finite()
        assert isinstance(result, BoolRef)

    def test_is_infinite_returns_boolref(self):
        """is_infinite() returns BoolRef."""
        dt = DecimalRef.from_str("123.456")
        result = dt.is_infinite()
        assert isinstance(result, BoolRef)

    def test_is_signed_returns_boolref(self):
        """is_signed() returns BoolRef."""
        dt = DecimalRef.from_str("-123.456")
        result = dt.is_signed()
        assert isinstance(result, BoolRef)

    def test_is_zero_returns_boolref(self):
        """is_zero() returns BoolRef."""
        dt = DecimalRef.from_str("0")
        result = dt.is_zero()
        assert isinstance(result, BoolRef)


# =============================================================================
# DECIMALREF CONVERSION TESTS
# =============================================================================


class TestDecimalRefConversions:
    """DecimalRef conversion tests."""

    def test_to_int_returns_intref(self):
        """to_int() returns IntRef."""
        dt = DecimalRef.from_str("123.456")
        result = dt.to_int()
        assert isinstance(result, IntRef)
