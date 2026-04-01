"""Unit tests for Fraction ref.

Tests for:
- FractionRef (constructors, operations, methods)
"""

from fractions import Fraction

from nu_math import FractionValue as FractionRef
from nu import AddOp, DivOp, FloorDivOp, FuncCallOp, ModOp, MulOp, PowOp, SubOp
from nu import FloatI as FloatRef
from nu import IntI as IntRef
from nu import TupleI as TupleRef


# =============================================================================
# FRACTIONREF CONSTRUCTION TESTS
# =============================================================================


class TestFractionRefConstruction:
    """FractionRef construction tests."""

    def test_from_components(self):
        """Create from numerator and denominator."""
        ft = FractionRef.from_components(3, 4)
        assert isinstance(ft, FractionRef)
        assert isinstance(ft.source, FuncCallOp)

    def test_from_components_integer(self):
        """Create from integer (denominator defaults to 1)."""
        ft = FractionRef.from_components(5)
        assert isinstance(ft, FractionRef)

    def test_from_str(self):
        """Create from string."""
        ft = FractionRef.from_str("3/4")
        assert isinstance(ft, FractionRef)

    def test_from_float(self):
        """Create from float."""
        ft = FractionRef.from_float(0.5)
        assert isinstance(ft, FractionRef)

    def test_from_decimal(self):
        """Create from Decimal."""
        from decimal import Decimal

        ft = FractionRef.from_decimal(Decimal("0.75"))
        assert isinstance(ft, FractionRef)


# =============================================================================
# FRACTIONREF COMPONENT ACCESSOR TESTS
# =============================================================================


class TestFractionRefAccessors:
    """FractionRef component accessor tests."""

    def test_numerator_returns_intref(self):
        """numerator() returns IntRef."""
        ft = FractionRef.from_components(3, 4)
        result = ft.numerator()
        assert isinstance(result, IntRef)

    def test_denominator_returns_intref(self):
        """denominator() returns IntRef."""
        ft = FractionRef.from_components(3, 4)
        result = ft.denominator()
        assert isinstance(result, IntRef)


# =============================================================================
# FRACTIONREF ARITHMETIC TESTS
# =============================================================================


class TestFractionRefArithmetic:
    """FractionRef arithmetic tests."""

    def test_add_returns_fractionref(self):
        """Addition returns FractionRef."""
        ft = FractionRef.from_components(1, 4)
        result = ft + Fraction(1, 2)
        assert isinstance(result, FractionRef)
        assert isinstance(result.source, AddOp)

    def test_add_int(self):
        """Add integer."""
        ft = FractionRef.from_components(1, 4)
        result = ft + 1
        assert isinstance(result, FractionRef)

    def test_radd(self):
        """Right addition works."""
        ft = FractionRef.from_components(1, 4)
        result = Fraction(1, 2) + ft
        assert isinstance(result, FractionRef)

    def test_sub_returns_fractionref(self):
        """Subtraction returns FractionRef."""
        ft = FractionRef.from_components(3, 4)
        result = ft - Fraction(1, 4)
        assert isinstance(result, FractionRef)
        assert isinstance(result.source, SubOp)

    def test_rsub(self):
        """Right subtraction works."""
        ft = FractionRef.from_components(1, 4)
        result = Fraction(3, 4) - ft
        assert isinstance(result, FractionRef)

    def test_mul_returns_fractionref(self):
        """Multiplication returns FractionRef."""
        ft = FractionRef.from_components(1, 2)
        result = ft * Fraction(2, 3)
        assert isinstance(result, FractionRef)
        assert isinstance(result.source, MulOp)

    def test_rmul(self):
        """Right multiplication works."""
        ft = FractionRef.from_components(1, 2)
        result = 2 * ft
        assert isinstance(result, FractionRef)

    def test_truediv_returns_fractionref(self):
        """Division returns FractionRef."""
        ft = FractionRef.from_components(1, 2)
        result = ft / Fraction(1, 4)
        assert isinstance(result, FractionRef)
        assert isinstance(result.source, DivOp)

    def test_rtruediv(self):
        """Right division works."""
        ft = FractionRef.from_components(1, 2)
        result = Fraction(1, 4) / ft
        assert isinstance(result, FractionRef)

    def test_floordiv_returns_intref(self):
        """Floor division returns IntRef."""
        ft = FractionRef.from_components(7, 2)
        result = ft // Fraction(3, 2)
        assert isinstance(result, IntRef)
        assert isinstance(result.source, FloorDivOp)

    def test_rfloordiv(self):
        """Right floor division works."""
        ft = FractionRef.from_components(3, 2)
        result = Fraction(7, 2) // ft
        assert isinstance(result, IntRef)

    def test_mod_returns_fractionref(self):
        """Modulo returns FractionRef."""
        ft = FractionRef.from_components(7, 2)
        result = ft % Fraction(3, 2)
        assert isinstance(result, FractionRef)
        assert isinstance(result.source, ModOp)

    def test_rmod(self):
        """Right modulo works."""
        ft = FractionRef.from_components(3, 2)
        result = Fraction(7, 2) % ft
        assert isinstance(result, FractionRef)

    def test_pow_returns_fractionref(self):
        """Power returns FractionRef."""
        ft = FractionRef.from_components(2, 3)
        result = ft**2
        assert isinstance(result, FractionRef)
        assert isinstance(result.source, PowOp)


# =============================================================================
# FRACTIONREF CONVERSION TESTS
# =============================================================================


class TestFractionRefConversions:
    """FractionRef conversion method tests."""

    def test_limit_denominator_returns_fractionref(self):
        """limit_denominator() returns FractionRef."""
        ft = FractionRef.from_float(3.141592653589793)
        result = ft.limit_denominator(100)
        assert isinstance(result, FractionRef)

    def test_as_float_returns_floatref(self):
        """as_float() returns FloatRef."""
        ft = FractionRef.from_components(1, 2)
        result = ft.as_float()
        assert isinstance(result, FloatRef)

    def test_as_integer_ratio_returns_tupleref(self):
        """as_integer_ratio() returns TupleRef."""
        ft = FractionRef.from_components(3, 4)
        result = ft.as_integer_ratio()
        assert isinstance(result, TupleRef)
