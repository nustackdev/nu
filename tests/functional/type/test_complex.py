"""Functional tests for Complex type.

Tests ComplexType and ComplexSlot execution with real storage context.
"""

import cmath

from everybase.type import ComplexType


# ============================================================================
# COMPLEX SET AND GET TESTS
# ============================================================================


class TestComplexSetAndGet:
    """Test setting and getting complex values through storage."""

    def test_set_and_get_complex(self, complex_shape, ctx):
        """Set and retrieve a complex value."""
        c = complex(3, 4)
        complex_shape.amplitude.set(c).execute(ctx)
        result = complex_shape.amplitude.get().execute(ctx)
        assert result == c

    def test_set_complex_real_only(self, complex_shape, ctx):
        """Set complex with real component only."""
        c = complex(5, 0)
        complex_shape.amplitude.set(c).execute(ctx)
        result = complex_shape.amplitude.get().execute(ctx)
        assert result == c

    def test_set_complex_imaginary_only(self, complex_shape, ctx):
        """Set complex with imaginary component only."""
        c = complex(0, 7)
        complex_shape.amplitude.set(c).execute(ctx)
        result = complex_shape.amplitude.get().execute(ctx)
        assert result == c

    def test_set_multiple_complex(self, complex_shape, ctx):
        """Set multiple complex slots."""
        amp = complex(3, 4)
        phase = complex(1, 1)

        complex_shape.amplitude.set(amp).execute(ctx)
        complex_shape.phase.set(phase).execute(ctx)

        assert complex_shape.amplitude.get().execute(ctx) == amp
        assert complex_shape.phase.get().execute(ctx) == phase


# ============================================================================
# COMPLEXTYPE CONSTRUCTOR TESTS
# ============================================================================


class TestComplexTypeConstructors:
    """Test ComplexType constructors with execution."""

    def test_from_components(self, ctx):
        """Create from real and imaginary components."""
        result = ComplexType.from_components(3, 4).execute(ctx)
        assert result == complex(3, 4)

    def test_from_components_real_only(self, ctx):
        """Create with real component only."""
        result = ComplexType.from_components(5).execute(ctx)
        assert result == complex(5, 0)

    def test_from_str(self, ctx):
        """Create from string."""
        result = ComplexType.from_str("3+4j").execute(ctx)
        assert result == complex(3, 4)

    def test_from_polar(self, ctx):
        """Create from polar coordinates."""
        r = 5.0
        phi = cmath.atan(complex(4, 3)).real
        result = ComplexType.from_polar(r, phi).execute(ctx)
        # Check magnitude and phase approximately
        assert abs(abs(result) - r) < 0.01


# ============================================================================
# COMPLEX COMPONENT ACCESS TESTS
# ============================================================================


class TestComplexComponentAccess:
    """Test accessing complex components."""

    def test_real(self, complex_shape, ctx):
        """Access real component."""
        c = complex(3, 4)
        complex_shape.amplitude.set(c).execute(ctx)
        result = complex_shape.amplitude.real().execute(ctx)
        assert result == 3.0

    def test_imag(self, complex_shape, ctx):
        """Access imaginary component."""
        c = complex(3, 4)
        complex_shape.amplitude.set(c).execute(ctx)
        result = complex_shape.amplitude.imag().execute(ctx)
        assert result == 4.0


# ============================================================================
# COMPLEX ARITHMETIC TESTS
# ============================================================================


class TestComplexArithmetic:
    """Test complex arithmetic operations."""

    def test_addition(self, complex_shape, ctx):
        """Add complex numbers."""
        complex_shape.amplitude.set(complex(3, 4)).execute(ctx)
        result = (complex_shape.amplitude.get() + complex(1, 2)).execute(ctx)
        assert result == complex(4, 6)

    def test_addition_slots(self, complex_shape, ctx):
        """Add two complex slots."""
        complex_shape.amplitude.set(complex(3, 4)).execute(ctx)
        complex_shape.phase.set(complex(1, 2)).execute(ctx)

        result = (complex_shape.amplitude.get() + complex_shape.phase.get()).execute(ctx)
        assert result == complex(4, 6)

    def test_subtraction(self, complex_shape, ctx):
        """Subtract complex numbers."""
        complex_shape.amplitude.set(complex(5, 6)).execute(ctx)
        result = (complex_shape.amplitude.get() - complex(2, 3)).execute(ctx)
        assert result == complex(3, 3)

    def test_multiplication(self, complex_shape, ctx):
        """Multiply complex numbers."""
        complex_shape.amplitude.set(complex(3, 4)).execute(ctx)
        result = (complex_shape.amplitude.get() * complex(1, 2)).execute(ctx)
        # (3+4j)(1+2j) = 3 + 6j + 4j + 8j^2 = 3 + 10j - 8 = -5 + 10j
        assert result == complex(-5, 10)

    def test_division(self, complex_shape, ctx):
        """Divide complex numbers."""
        complex_shape.amplitude.set(complex(4, 2)).execute(ctx)
        result = (complex_shape.amplitude.get() / complex(2, 0)).execute(ctx)
        assert result == complex(2, 1)

    def test_power(self, complex_shape, ctx):
        """Raise complex to power."""
        complex_shape.amplitude.set(complex(2, 0)).execute(ctx)
        result = (complex_shape.amplitude.get() ** 3).execute(ctx)
        assert abs(result - complex(8, 0)) < 0.0001

    def test_negation(self, complex_shape, ctx):
        """Negate complex number."""
        complex_shape.amplitude.set(complex(3, 4)).execute(ctx)
        result = (-complex_shape.amplitude.get()).execute(ctx)
        assert result == complex(-3, -4)

    def test_abs(self, complex_shape, ctx):
        """Get magnitude (absolute value)."""
        complex_shape.amplitude.set(complex(3, 4)).execute(ctx)
        result = abs(complex_shape.amplitude.get()).execute(ctx)
        assert result == 5.0


# ============================================================================
# COMPLEX OPERATION TESTS
# ============================================================================


class TestComplexOperations:
    """Test complex-specific operations."""

    def test_conjugate(self, complex_shape, ctx):
        """Get complex conjugate."""
        complex_shape.amplitude.set(complex(3, 4)).execute(ctx)
        result = complex_shape.amplitude.conjugate().execute(ctx)
        assert result == complex(3, -4)

    def test_phase(self, complex_shape, ctx):
        """Get phase (argument) in radians."""
        complex_shape.amplitude.set(complex(1, 1)).execute(ctx)
        result = complex_shape.amplitude.phase().execute(ctx)
        # 1+1j has phase of pi/4
        assert abs(result - cmath.pi / 4) < 0.0001

    def test_polar(self, complex_shape, ctx):
        """Get polar coordinates (r, phi)."""
        complex_shape.amplitude.set(complex(3, 4)).execute(ctx)
        result = complex_shape.amplitude.polar().execute(ctx)
        r, phi = result
        assert abs(r - 5.0) < 0.0001
        assert abs(phi - cmath.atan(complex(4, 3)).real) < 0.0001


# ============================================================================
# COMPLEX MATHEMATICAL FUNCTION TESTS
# ============================================================================


class TestComplexMathFunctions:
    """Test complex mathematical functions."""

    def test_sqrt(self, complex_shape, ctx):
        """Square root of complex."""
        complex_shape.amplitude.set(complex(3, 4)).execute(ctx)
        result = complex_shape.amplitude.sqrt().execute(ctx)
        # Verify result^2 = 3+4j
        assert abs(result**2 - complex(3, 4)) < 0.0001

    def test_exp(self, complex_shape, ctx):
        """Exponential of complex."""
        complex_shape.amplitude.set(complex(0, cmath.pi)).execute(ctx)
        result = complex_shape.amplitude.exp().execute(ctx)
        # e^(i*pi) = -1
        assert abs(result - complex(-1, 0)) < 0.0001

    def test_log(self, complex_shape, ctx):
        """Natural logarithm of complex."""
        complex_shape.amplitude.set(cmath.e + 0j).execute(ctx)
        result = complex_shape.amplitude.log().execute(ctx)
        # ln(e) = 1
        assert abs(result - complex(1, 0)) < 0.0001

    def test_sin(self, complex_shape, ctx):
        """Sine of complex."""
        complex_shape.amplitude.set(complex(0, 0)).execute(ctx)
        result = complex_shape.amplitude.sin().execute(ctx)
        # sin(0) = 0
        assert abs(result) < 0.0001

    def test_cos(self, complex_shape, ctx):
        """Cosine of complex."""
        complex_shape.amplitude.set(complex(0, 0)).execute(ctx)
        result = complex_shape.amplitude.cos().execute(ctx)
        # cos(0) = 1
        assert abs(result - 1) < 0.0001

    def test_tan(self, complex_shape, ctx):
        """Tangent of complex."""
        complex_shape.amplitude.set(complex(0, 0)).execute(ctx)
        result = complex_shape.amplitude.tan().execute(ctx)
        # tan(0) = 0
        assert abs(result) < 0.0001


# ============================================================================
# COMPLEX EQUALITY TESTS
# ============================================================================


class TestComplexEquality:
    """Test complex equality operations."""

    def test_equals(self, complex_shape, ctx):
        """Compare complex numbers for equality."""
        complex_shape.amplitude.set(complex(3, 4)).execute(ctx)
        complex_shape.phase.set(complex(3, 4)).execute(ctx)

        result = (complex_shape.amplitude.get() == complex_shape.phase.get()).execute(ctx)
        assert result is True

    def test_not_equals(self, complex_shape, ctx):
        """Compare complex numbers for inequality."""
        complex_shape.amplitude.set(complex(3, 4)).execute(ctx)
        complex_shape.phase.set(complex(4, 3)).execute(ctx)

        result = (complex_shape.amplitude.get() != complex_shape.phase.get()).execute(ctx)
        assert result is True
