"""Unit tests for BasisPoint ref.

Tests for:
- BasisPoint native Python class (constructors, conversions, arithmetic)
- BasisPointRef (constructors, operations)
"""

import pytest

from nu_fin import BasisPoint
from nu_fin import BasisPointValue as BasisPointRef
from nu import AddOp, DivOp, FuncCallOp, MulOp, SubOp
from nu import FloatI as FloatRef
from nu import IntI as IntRef


# =============================================================================
# BASISPOINT NATIVE CLASS TESTS
# =============================================================================


class TestBasisPointConstruction:
    """BasisPoint construction tests."""

    def test_direct_construction(self):
        """Create BasisPoint with direct value."""
        bp = BasisPoint(500)
        assert bp.value == 500

    def test_from_pct(self):
        """Create from percentage."""
        bp = BasisPoint.from_pct(5.0)
        assert bp.value == 500

    def test_from_dec(self):
        """Create from decimal."""
        bp = BasisPoint.from_dec(0.05)
        assert bp.value == 500

    def test_frozen_immutable(self):
        """BasisPoint is immutable (frozen dataclass)."""
        bp = BasisPoint(500)
        with pytest.raises(AttributeError):
            bp.value = 600  # type: ignore


class TestBasisPointConversions:
    """BasisPoint conversion tests."""

    def test_to_pct(self):
        """Convert to percentage."""
        bp = BasisPoint(500)
        assert bp.to_pct() == 5.0

    def test_to_dec(self):
        """Convert to decimal."""
        bp = BasisPoint(500)
        assert bp.to_dec() == 0.05

    def test_to_int(self):
        """Get raw value."""
        bp = BasisPoint(500)
        assert bp.to_int() == 500


class TestBasisPointApplication:
    """BasisPoint application tests."""

    def test_apply(self):
        """Apply basis points to amount."""
        bp = BasisPoint(500)  # 5%
        result = bp.apply(1000)
        assert result == 50.0

    def test_add_to(self):
        """Add basis points to amount."""
        bp = BasisPoint(500)  # 5%
        result = bp.add_to(1000)
        assert result == 1050.0

    def test_sub_from(self):
        """Subtract basis points from amount."""
        bp = BasisPoint(500)  # 5%
        result = bp.sub_from(1000)
        assert result == 950.0


class TestBasisPointArithmetic:
    """BasisPoint arithmetic tests."""

    def test_add_basispoint(self):
        """Add two BasisPoints."""
        bp1 = BasisPoint(300)
        bp2 = BasisPoint(200)
        result = bp1 + bp2
        assert isinstance(result, BasisPoint)
        assert result.value == 500

    def test_add_int(self):
        """Add BasisPoint and int."""
        bp = BasisPoint(300)
        result = bp + 200
        assert result.value == 500

    def test_radd(self):
        """Right add."""
        bp = BasisPoint(300)
        result = 200 + bp
        assert result.value == 500

    def test_sub_basispoint(self):
        """Subtract BasisPoints."""
        bp1 = BasisPoint(500)
        bp2 = BasisPoint(200)
        result = bp1 - bp2
        assert result.value == 300

    def test_sub_int(self):
        """Subtract int from BasisPoint."""
        bp = BasisPoint(500)
        result = bp - 200
        assert result.value == 300

    def test_rsub(self):
        """Right subtract."""
        bp = BasisPoint(200)
        result = 500 - bp
        assert result.value == 300

    def test_mul(self):
        """Multiply by factor."""
        bp = BasisPoint(100)
        result = bp * 3
        assert result.value == 300

    def test_rmul(self):
        """Right multiply."""
        bp = BasisPoint(100)
        result = 3 * bp
        assert result.value == 300

    def test_truediv(self):
        """Divide by factor."""
        bp = BasisPoint(300)
        result = bp / 3
        assert result.value == 100

    def test_floordiv(self):
        """Floor divide."""
        bp = BasisPoint(350)
        result = bp // 3
        assert result.value == 116


class TestBasisPointComparison:
    """BasisPoint comparison tests."""

    def test_lt_basispoint(self):
        """Less than with BasisPoint."""
        bp1 = BasisPoint(300)
        bp2 = BasisPoint(500)
        assert bp1 < bp2
        assert not bp2 < bp1

    def test_lt_int(self):
        """Less than with int."""
        bp = BasisPoint(300)
        assert bp < 500
        assert not bp < 200

    def test_le_basispoint(self):
        """Less than or equal with BasisPoint."""
        bp1 = BasisPoint(300)
        bp2 = BasisPoint(300)
        assert bp1 <= bp2

    def test_gt_basispoint(self):
        """Greater than with BasisPoint."""
        bp1 = BasisPoint(500)
        bp2 = BasisPoint(300)
        assert bp1 > bp2

    def test_ge_basispoint(self):
        """Greater than or equal with BasisPoint."""
        bp1 = BasisPoint(500)
        bp2 = BasisPoint(500)
        assert bp1 >= bp2


class TestBasisPointString:
    """BasisPoint string representation tests."""

    def test_str(self):
        """String representation."""
        bp = BasisPoint(500)
        assert str(bp) == "500bps"

    def test_repr(self):
        """Debug representation."""
        bp = BasisPoint(500)
        assert repr(bp) == "BasisPoint(500)"

    def test_format_bps(self):
        """Format as basis points."""
        bp = BasisPoint(500)
        assert bp.format("bps") == "500bps"

    def test_format_pct(self):
        """Format as percentage."""
        bp = BasisPoint(500)
        assert bp.format("pct") == "5.00%"

    def test_format_dec(self):
        """Format as decimal."""
        bp = BasisPoint(500)
        assert bp.format("dec") == "0.0500"


# =============================================================================
# BASISPOINTREF TESTS
# =============================================================================


class TestBasisPointRefConstruction:
    """BasisPointRef construction tests."""

    def test_from_int(self):
        """Create from int literal."""
        bpt = BasisPointRef.from_int(500)
        assert isinstance(bpt, BasisPointRef)
        assert isinstance(bpt.source, FuncCallOp)

    def test_from_pct(self):
        """Create from percentage."""
        bpt = BasisPointRef.from_pct(5.0)
        assert isinstance(bpt, BasisPointRef)

    def test_from_dec(self):
        """Create from decimal."""
        bpt = BasisPointRef.from_dec(0.05)
        assert isinstance(bpt, BasisPointRef)


class TestBasisPointRefConversions:
    """BasisPointRef conversion method tests."""

    def test_to_pct_returns_floatref(self):
        """to_pct() returns FloatRef."""
        bpt = BasisPointRef.from_int(500)
        result = bpt.to_pct()
        assert isinstance(result, FloatRef)

    def test_to_dec_returns_floatref(self):
        """to_dec() returns FloatRef."""
        bpt = BasisPointRef.from_int(500)
        result = bpt.to_dec()
        assert isinstance(result, FloatRef)

    def test_to_int_returns_intref(self):
        """to_int() returns IntRef."""
        bpt = BasisPointRef.from_int(500)
        result = bpt.to_int()
        assert isinstance(result, IntRef)


class TestBasisPointRefApplication:
    """BasisPointRef application method tests."""

    def test_apply_returns_floatref(self):
        """apply() returns FloatRef."""
        bpt = BasisPointRef.from_int(500)
        result = bpt.apply(1000)
        assert isinstance(result, FloatRef)

    def test_add_to_returns_floatref(self):
        """add_to() returns FloatRef."""
        bpt = BasisPointRef.from_int(500)
        result = bpt.add_to(1000)
        assert isinstance(result, FloatRef)

    def test_sub_from_returns_floatref(self):
        """sub_from() returns FloatRef."""
        bpt = BasisPointRef.from_int(500)
        result = bpt.sub_from(1000)
        assert isinstance(result, FloatRef)


class TestBasisPointRefArithmetic:
    """BasisPointRef arithmetic operation tests."""

    def test_add_returns_basispointref(self):
        """Addition returns BasisPointRef."""
        bpt = BasisPointRef.from_int(300)
        result = bpt + 200
        assert isinstance(result, BasisPointRef)
        assert isinstance(result.source, AddOp)

    def test_sub_returns_basispointref(self):
        """Subtraction returns BasisPointRef."""
        bpt = BasisPointRef.from_int(500)
        result = bpt - 200
        assert isinstance(result, BasisPointRef)
        assert isinstance(result.source, SubOp)

    def test_mul_returns_basispointref(self):
        """Multiplication returns BasisPointRef."""
        bpt = BasisPointRef.from_int(100)
        result = bpt * 3
        assert isinstance(result, BasisPointRef)
        assert isinstance(result.source, MulOp)

    def test_truediv_returns_basispointref(self):
        """Division returns BasisPointRef."""
        bpt = BasisPointRef.from_int(300)
        result = bpt / 3
        assert isinstance(result, BasisPointRef)
        assert isinstance(result.source, DivOp)
