"""Unit tests for Fraction type.

Tests for:
- FractionType (constructors, operations, methods)
"""

from fractions import Fraction

from everybase.type.fraction import FractionType
from everyterm.ops import AddOp, DivOp, FloorDivOp, FuncCallOp, ModOp, MulOp, PowOp, SubOp
from everyterm.types import FloatType, IntType, TupleType


# =============================================================================
# FRACTIONTYPE CONSTRUCTION TESTS
# =============================================================================


class TestFractionTypeConstruction:
    """FractionType construction tests."""

    def test_from_components(self):
        """Create from numerator and denominator."""
        ft = FractionType.from_components(3, 4)
        assert isinstance(ft, FractionType)
        assert isinstance(ft.source, FuncCallOp)

    def test_from_components_integer(self):
        """Create from integer (denominator defaults to 1)."""
        ft = FractionType.from_components(5)
        assert isinstance(ft, FractionType)

    def test_from_str(self):
        """Create from string."""
        ft = FractionType.from_str("3/4")
        assert isinstance(ft, FractionType)

    def test_from_float(self):
        """Create from float."""
        ft = FractionType.from_float(0.5)
        assert isinstance(ft, FractionType)

    def test_from_decimal(self):
        """Create from Decimal."""
        from decimal import Decimal

        # Using AnyType to wrap Decimal
        ft = FractionType.from_decimal(Decimal("0.75"))
        assert isinstance(ft, FractionType)


# =============================================================================
# FRACTIONTYPE COMPONENT ACCESSOR TESTS
# =============================================================================


class TestFractionTypeAccessors:
    """FractionType component accessor tests."""

    def test_numerator_returns_inttype(self):
        """numerator() returns IntType."""
        ft = FractionType.from_components(3, 4)
        result = ft.numerator()
        assert isinstance(result, IntType)

    def test_denominator_returns_inttype(self):
        """denominator() returns IntType."""
        ft = FractionType.from_components(3, 4)
        result = ft.denominator()
        assert isinstance(result, IntType)


# =============================================================================
# FRACTIONTYPE ARITHMETIC TESTS
# =============================================================================


class TestFractionTypeArithmetic:
    """FractionType arithmetic tests."""

    def test_add_returns_fractiontype(self):
        """Addition returns FractionType."""
        ft = FractionType.from_components(1, 4)
        result = ft + Fraction(1, 2)
        assert isinstance(result, FractionType)
        assert isinstance(result.source, AddOp)

    def test_add_int(self):
        """Add integer."""
        ft = FractionType.from_components(1, 4)
        result = ft + 1
        assert isinstance(result, FractionType)

    def test_radd(self):
        """Right addition works."""
        ft = FractionType.from_components(1, 4)
        result = Fraction(1, 2) + ft
        assert isinstance(result, FractionType)

    def test_sub_returns_fractiontype(self):
        """Subtraction returns FractionType."""
        ft = FractionType.from_components(3, 4)
        result = ft - Fraction(1, 4)
        assert isinstance(result, FractionType)
        assert isinstance(result.source, SubOp)

    def test_rsub(self):
        """Right subtraction works."""
        ft = FractionType.from_components(1, 4)
        result = Fraction(3, 4) - ft
        assert isinstance(result, FractionType)

    def test_mul_returns_fractiontype(self):
        """Multiplication returns FractionType."""
        ft = FractionType.from_components(1, 2)
        result = ft * Fraction(2, 3)
        assert isinstance(result, FractionType)
        assert isinstance(result.source, MulOp)

    def test_rmul(self):
        """Right multiplication works."""
        ft = FractionType.from_components(1, 2)
        result = 2 * ft
        assert isinstance(result, FractionType)

    def test_truediv_returns_fractiontype(self):
        """Division returns FractionType."""
        ft = FractionType.from_components(1, 2)
        result = ft / Fraction(1, 4)
        assert isinstance(result, FractionType)
        assert isinstance(result.source, DivOp)

    def test_rtruediv(self):
        """Right division works."""
        ft = FractionType.from_components(1, 2)
        result = Fraction(1, 4) / ft
        assert isinstance(result, FractionType)

    def test_floordiv_returns_inttype(self):
        """Floor division returns IntType."""
        ft = FractionType.from_components(7, 2)
        result = ft // Fraction(3, 2)
        assert isinstance(result, IntType)
        assert isinstance(result.source, FloorDivOp)

    def test_rfloordiv(self):
        """Right floor division works."""
        ft = FractionType.from_components(3, 2)
        result = Fraction(7, 2) // ft
        assert isinstance(result, IntType)

    def test_mod_returns_fractiontype(self):
        """Modulo returns FractionType."""
        ft = FractionType.from_components(7, 2)
        result = ft % Fraction(3, 2)
        assert isinstance(result, FractionType)
        assert isinstance(result.source, ModOp)

    def test_rmod(self):
        """Right modulo works."""
        ft = FractionType.from_components(3, 2)
        result = Fraction(7, 2) % ft
        assert isinstance(result, FractionType)

    def test_pow_returns_fractiontype(self):
        """Power returns FractionType."""
        ft = FractionType.from_components(2, 3)
        result = ft**2
        assert isinstance(result, FractionType)
        assert isinstance(result.source, PowOp)


# =============================================================================
# FRACTIONTYPE CONVERSION TESTS
# =============================================================================


class TestFractionTypeConversions:
    """FractionType conversion method tests."""

    def test_limit_denominator_returns_fractiontype(self):
        """limit_denominator() returns FractionType."""
        ft = FractionType.from_float(3.141592653589793)
        result = ft.limit_denominator(100)
        assert isinstance(result, FractionType)

    def test_as_float_returns_floattype(self):
        """as_float() returns FloatType."""
        ft = FractionType.from_components(1, 2)
        result = ft.as_float()
        assert isinstance(result, FloatType)

    def test_as_integer_ratio_returns_tupletype(self):
        """as_integer_ratio() returns TupleType."""
        ft = FractionType.from_components(3, 4)
        result = ft.as_integer_ratio()
        assert isinstance(result, TupleType)
