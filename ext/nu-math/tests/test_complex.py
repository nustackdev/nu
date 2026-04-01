"""Unit tests for Complex ref.

Tests for:
- ComplexRef (constructors, operations, methods)
"""

import cmath

from nu_math import ComplexValue as ComplexRef
from nu import AddOp, DivOp, FuncCallOp, MulOp, PowOp, SubOp
from nu import FloatValue as FloatRef
from nu import TupleValue as TupleRef


# =============================================================================
# COMPLEXREF CONSTRUCTION TESTS
# =============================================================================


class TestComplexRefConstruction:
    """ComplexRef construction tests."""

    def test_from_components(self):
        """Create from real and imaginary components."""
        ct = ComplexRef.from_components(3, 4)
        assert isinstance(ct, ComplexRef)
        assert isinstance(ct.source, FuncCallOp)

    def test_from_components_real_only(self):
        """Create with real component only."""
        ct = ComplexRef.from_components(5)
        assert isinstance(ct, ComplexRef)

    def test_from_str(self):
        """Create from string."""
        ct = ComplexRef.from_str("3+4j")
        assert isinstance(ct, ComplexRef)

    def test_from_polar(self):
        """Create from polar coordinates."""
        ct = ComplexRef.from_polar(5, cmath.atan(complex(4, 3)).real)
        assert isinstance(ct, ComplexRef)


# =============================================================================
# COMPLEXREF COMPONENT ACCESSOR TESTS
# =============================================================================


class TestComplexRefAccessors:
    """ComplexRef component accessor tests."""

    def test_real_returns_floatref(self):
        """real() returns FloatRef."""
        ct = ComplexRef.from_components(3, 4)
        result = ct.real()
        assert isinstance(result, FloatRef)

    def test_imag_returns_floatref(self):
        """imag() returns FloatRef."""
        ct = ComplexRef.from_components(3, 4)
        result = ct.imag()
        assert isinstance(result, FloatRef)


# =============================================================================
# COMPLEXREF ARITHMETIC TESTS
# =============================================================================


class TestComplexRefArithmetic:
    """ComplexRef arithmetic tests."""

    def test_add_returns_complexref(self):
        """Addition returns ComplexRef."""
        ct = ComplexRef.from_components(3, 4)
        result = ct + complex(1, 2)
        assert isinstance(result, ComplexRef)
        assert isinstance(result.source, AddOp)

    def test_radd(self):
        """Right addition works."""
        ct = ComplexRef.from_components(3, 4)
        result = complex(1, 2) + ct
        assert isinstance(result, ComplexRef)

    def test_sub_returns_complexref(self):
        """Subtraction returns ComplexRef."""
        ct = ComplexRef.from_components(3, 4)
        result = ct - complex(1, 2)
        assert isinstance(result, ComplexRef)
        assert isinstance(result.source, SubOp)

    def test_rsub(self):
        """Right subtraction works."""
        ct = ComplexRef.from_components(3, 4)
        result = complex(5, 6) - ct
        assert isinstance(result, ComplexRef)

    def test_mul_returns_complexref(self):
        """Multiplication returns ComplexRef."""
        ct = ComplexRef.from_components(3, 4)
        result = ct * complex(1, 2)
        assert isinstance(result, ComplexRef)
        assert isinstance(result.source, MulOp)

    def test_rmul(self):
        """Right multiplication works."""
        ct = ComplexRef.from_components(3, 4)
        result = 2 * ct
        assert isinstance(result, ComplexRef)

    def test_truediv_returns_complexref(self):
        """Division returns ComplexRef."""
        ct = ComplexRef.from_components(3, 4)
        result = ct / complex(1, 2)
        assert isinstance(result, ComplexRef)
        assert isinstance(result.source, DivOp)

    def test_rtruediv(self):
        """Right division works."""
        ct = ComplexRef.from_components(1, 2)
        result = complex(3, 4) / ct
        assert isinstance(result, ComplexRef)

    def test_pow_returns_complexref(self):
        """Power returns ComplexRef."""
        ct = ComplexRef.from_components(2, 0)
        result = ct**3
        assert isinstance(result, ComplexRef)
        assert isinstance(result.source, PowOp)

    def test_rpow(self):
        """Right power works."""
        ct = ComplexRef.from_components(2, 0)
        result = 2**ct
        assert isinstance(result, ComplexRef)

    def test_abs_returns_floatref(self):
        """abs() returns FloatRef (magnitude)."""
        ct = ComplexRef.from_components(3, 4)
        result = abs(ct)
        assert isinstance(result, FloatRef)


# =============================================================================
# COMPLEXREF COMPLEX OPERATIONS TESTS
# =============================================================================


class TestComplexRefOperations:
    """ComplexRef complex operation tests."""

    def test_conjugate_returns_complexref(self):
        """conjugate() returns ComplexRef."""
        ct = ComplexRef.from_components(3, 4)
        result = ct.conjugate()
        assert isinstance(result, ComplexRef)

    def test_phase_returns_floatref(self):
        """phase() returns FloatRef."""
        ct = ComplexRef.from_components(3, 4)
        result = ct.phase()
        assert isinstance(result, FloatRef)

    def test_polar_returns_tupleref(self):
        """polar() returns TupleRef."""
        ct = ComplexRef.from_components(3, 4)
        result = ct.polar()
        assert isinstance(result, TupleRef)


# =============================================================================
# COMPLEXREF MATHEMATICAL FUNCTION TESTS
# =============================================================================


class TestComplexRefMathFunctions:
    """ComplexRef mathematical function tests."""

    def test_sqrt_returns_complexref(self):
        """sqrt() returns ComplexRef."""
        ct = ComplexRef.from_components(3, 4)
        result = ct.sqrt()
        assert isinstance(result, ComplexRef)

    def test_exp_returns_complexref(self):
        """exp() returns ComplexRef."""
        ct = ComplexRef.from_components(1, 0)
        result = ct.exp()
        assert isinstance(result, ComplexRef)

    def test_log_returns_complexref(self):
        """log() returns ComplexRef."""
        ct = ComplexRef.from_components(3, 4)
        result = ct.log()
        assert isinstance(result, ComplexRef)

    def test_log_with_base_returns_complexref(self):
        """log(base) returns ComplexRef."""
        ct = ComplexRef.from_components(8, 0)
        result = ct.log(2)
        assert isinstance(result, ComplexRef)

    def test_sin_returns_complexref(self):
        """sin() returns ComplexRef."""
        ct = ComplexRef.from_components(1, 0)
        result = ct.sin()
        assert isinstance(result, ComplexRef)

    def test_cos_returns_complexref(self):
        """cos() returns ComplexRef."""
        ct = ComplexRef.from_components(1, 0)
        result = ct.cos()
        assert isinstance(result, ComplexRef)

    def test_tan_returns_complexref(self):
        """tan() returns ComplexRef."""
        ct = ComplexRef.from_components(1, 0)
        result = ct.tan()
        assert isinstance(result, ComplexRef)
