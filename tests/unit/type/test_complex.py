"""Unit tests for Complex type.

Tests for:
- ComplexType (constructors, operations, methods)
"""

import cmath

from everybase.type.complex import ComplexType
from everyterm.ops import AddOp, DivOp, FuncCallOp, MulOp, PowOp, SubOp
from everyterm.types import FloatType, TupleType


# =============================================================================
# COMPLEXTYPE CONSTRUCTION TESTS
# =============================================================================


class TestComplexTypeConstruction:
    """ComplexType construction tests."""

    def test_from_components(self):
        """Create from real and imaginary components."""
        ct = ComplexType.from_components(3, 4)
        assert isinstance(ct, ComplexType)
        assert isinstance(ct.source, FuncCallOp)

    def test_from_components_real_only(self):
        """Create with real component only."""
        ct = ComplexType.from_components(5)
        assert isinstance(ct, ComplexType)

    def test_from_str(self):
        """Create from string."""
        ct = ComplexType.from_str("3+4j")
        assert isinstance(ct, ComplexType)

    def test_from_polar(self):
        """Create from polar coordinates."""
        ct = ComplexType.from_polar(5, cmath.atan(complex(4, 3)).real)
        assert isinstance(ct, ComplexType)


# =============================================================================
# COMPLEXTYPE COMPONENT ACCESSOR TESTS
# =============================================================================


class TestComplexTypeAccessors:
    """ComplexType component accessor tests."""

    def test_real_returns_floattype(self):
        """real() returns FloatType."""
        ct = ComplexType.from_components(3, 4)
        result = ct.real()
        assert isinstance(result, FloatType)

    def test_imag_returns_floattype(self):
        """imag() returns FloatType."""
        ct = ComplexType.from_components(3, 4)
        result = ct.imag()
        assert isinstance(result, FloatType)


# =============================================================================
# COMPLEXTYPE ARITHMETIC TESTS
# =============================================================================


class TestComplexTypeArithmetic:
    """ComplexType arithmetic tests."""

    def test_add_returns_complextype(self):
        """Addition returns ComplexType."""
        ct = ComplexType.from_components(3, 4)
        result = ct + complex(1, 2)
        assert isinstance(result, ComplexType)
        assert isinstance(result.source, AddOp)

    def test_radd(self):
        """Right addition works."""
        ct = ComplexType.from_components(3, 4)
        result = complex(1, 2) + ct
        assert isinstance(result, ComplexType)

    def test_sub_returns_complextype(self):
        """Subtraction returns ComplexType."""
        ct = ComplexType.from_components(3, 4)
        result = ct - complex(1, 2)
        assert isinstance(result, ComplexType)
        assert isinstance(result.source, SubOp)

    def test_rsub(self):
        """Right subtraction works."""
        ct = ComplexType.from_components(3, 4)
        result = complex(5, 6) - ct
        assert isinstance(result, ComplexType)

    def test_mul_returns_complextype(self):
        """Multiplication returns ComplexType."""
        ct = ComplexType.from_components(3, 4)
        result = ct * complex(1, 2)
        assert isinstance(result, ComplexType)
        assert isinstance(result.source, MulOp)

    def test_rmul(self):
        """Right multiplication works."""
        ct = ComplexType.from_components(3, 4)
        result = 2 * ct
        assert isinstance(result, ComplexType)

    def test_truediv_returns_complextype(self):
        """Division returns ComplexType."""
        ct = ComplexType.from_components(3, 4)
        result = ct / complex(1, 2)
        assert isinstance(result, ComplexType)
        assert isinstance(result.source, DivOp)

    def test_rtruediv(self):
        """Right division works."""
        ct = ComplexType.from_components(1, 2)
        result = complex(3, 4) / ct
        assert isinstance(result, ComplexType)

    def test_pow_returns_complextype(self):
        """Power returns ComplexType."""
        ct = ComplexType.from_components(2, 0)
        result = ct**3
        assert isinstance(result, ComplexType)
        assert isinstance(result.source, PowOp)

    def test_rpow(self):
        """Right power works."""
        ct = ComplexType.from_components(2, 0)
        result = 2**ct
        assert isinstance(result, ComplexType)

    def test_abs_returns_floattype(self):
        """abs() returns FloatType (magnitude)."""
        ct = ComplexType.from_components(3, 4)
        result = abs(ct)
        assert isinstance(result, FloatType)


# =============================================================================
# COMPLEXTYPE COMPLEX OPERATIONS TESTS
# =============================================================================


class TestComplexTypeOperations:
    """ComplexType complex operation tests."""

    def test_conjugate_returns_complextype(self):
        """conjugate() returns ComplexType."""
        ct = ComplexType.from_components(3, 4)
        result = ct.conjugate()
        assert isinstance(result, ComplexType)

    def test_phase_returns_floattype(self):
        """phase() returns FloatType."""
        ct = ComplexType.from_components(3, 4)
        result = ct.phase()
        assert isinstance(result, FloatType)

    def test_polar_returns_tupletype(self):
        """polar() returns TupleType."""
        ct = ComplexType.from_components(3, 4)
        result = ct.polar()
        assert isinstance(result, TupleType)


# =============================================================================
# COMPLEXTYPE MATHEMATICAL FUNCTION TESTS
# =============================================================================


class TestComplexTypeMathFunctions:
    """ComplexType mathematical function tests."""

    def test_sqrt_returns_complextype(self):
        """sqrt() returns ComplexType."""
        ct = ComplexType.from_components(3, 4)
        result = ct.sqrt()
        assert isinstance(result, ComplexType)

    def test_exp_returns_complextype(self):
        """exp() returns ComplexType."""
        ct = ComplexType.from_components(1, 0)
        result = ct.exp()
        assert isinstance(result, ComplexType)

    def test_log_returns_complextype(self):
        """log() returns ComplexType."""
        ct = ComplexType.from_components(3, 4)
        result = ct.log()
        assert isinstance(result, ComplexType)

    def test_log_with_base_returns_complextype(self):
        """log(base) returns ComplexType."""
        ct = ComplexType.from_components(8, 0)
        result = ct.log(2)
        assert isinstance(result, ComplexType)

    def test_sin_returns_complextype(self):
        """sin() returns ComplexType."""
        ct = ComplexType.from_components(1, 0)
        result = ct.sin()
        assert isinstance(result, ComplexType)

    def test_cos_returns_complextype(self):
        """cos() returns ComplexType."""
        ct = ComplexType.from_components(1, 0)
        result = ct.cos()
        assert isinstance(result, ComplexType)

    def test_tan_returns_complextype(self):
        """tan() returns ComplexType."""
        ct = ComplexType.from_components(1, 0)
        result = ct.tan()
        assert isinstance(result, ComplexType)
