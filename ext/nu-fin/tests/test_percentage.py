"""Unit tests for Percentage ref.

Tests for:
- Percentage native Python class (constructors, conversions, arithmetic)
- PercentageRef (constructors, operations)
"""

import pytest

from nu_fin import Percentage
from nu_fin import PercentageValue as PercentageRef
from nu import AddOp, DivOp, FuncCallOp, MulOp, SubOp
from nu import BoolValue as BoolRef
from nu import FloatValue as FloatRef
from nu import IntValue as IntRef


# =============================================================================
# PERCENTAGE NATIVE CLASS TESTS
# =============================================================================


class TestPercentageConstruction:
    """Percentage construction tests."""

    def test_direct_construction(self):
        """Create Percentage with direct value."""
        pct = Percentage(75.5)
        assert pct.value == 75.5

    def test_from_dec(self):
        """Create from decimal."""
        pct = Percentage.from_dec(0.755)
        assert pct.value == 75.5

    def test_from_bps(self):
        """Create from basis points."""
        pct = Percentage.from_bps(7550)
        assert pct.value == 75.5

    def test_from_ratio(self):
        """Create from ratio."""
        pct = Percentage.from_ratio(3, 4)
        assert pct.value == 75.0

    def test_from_ratio_zero_denominator(self):
        """Create from ratio with zero denominator."""
        pct = Percentage.from_ratio(3, 0)
        assert pct.value == 0.0

    def test_frozen_immutable(self):
        """Percentage is immutable (frozen dataclass)."""
        pct = Percentage(75.5)
        with pytest.raises(AttributeError):
            pct.value = 80.0  # type: ignore


class TestPercentageConversions:
    """Percentage conversion tests."""

    def test_to_dec(self):
        """Convert to decimal."""
        pct = Percentage(75.5)
        assert pct.to_dec() == 0.755

    def test_to_bps(self):
        """Convert to basis points."""
        pct = Percentage(75.5)
        assert pct.to_bps() == 7550

    def test_to_float(self):
        """Get raw percentage."""
        pct = Percentage(75.5)
        assert pct.to_float() == 75.5


class TestPercentageApplication:
    """Percentage application tests."""

    def test_apply(self):
        """Apply percentage to amount."""
        pct = Percentage(50.0)
        result = pct.apply(200)
        assert result == 100.0

    def test_of(self):
        """'of' alias for apply."""
        pct = Percentage(50.0)
        result = pct.of(200)
        assert result == 100.0

    def test_add_to(self):
        """Add percentage to amount."""
        pct = Percentage(10.0)
        result = pct.add_to(100)
        assert pytest.approx(result) == 110.0

    def test_sub_from(self):
        """Subtract percentage from amount."""
        pct = Percentage(10.0)
        result = pct.sub_from(100)
        assert result == 90.0


class TestPercentageValidation:
    """Percentage validation tests."""

    def test_is_valid_default_range(self):
        """Check validity with default range."""
        pct = Percentage(50.0)
        assert pct.is_valid() is True

    def test_is_valid_out_of_range(self):
        """Check validity when out of range."""
        pct = Percentage(150.0)
        assert pct.is_valid() is False

    def test_is_valid_custom_range(self):
        """Check validity with custom range."""
        pct = Percentage(150.0)
        assert pct.is_valid(0, 200) is True

    def test_clamp_within_range(self):
        """Clamp value within range."""
        pct = Percentage(50.0)
        result = pct.clamp()
        assert result.value == 50.0

    def test_clamp_above_range(self):
        """Clamp value above range."""
        pct = Percentage(150.0)
        result = pct.clamp()
        assert result.value == 100.0

    def test_clamp_below_range(self):
        """Clamp value below range."""
        pct = Percentage(-10.0)
        result = pct.clamp()
        assert result.value == 0.0


class TestPercentageArithmetic:
    """Percentage arithmetic tests."""

    def test_add_percentage(self):
        """Add two Percentages."""
        pct1 = Percentage(30.0)
        pct2 = Percentage(20.0)
        result = pct1 + pct2
        assert isinstance(result, Percentage)
        assert result.value == 50.0

    def test_add_float(self):
        """Add Percentage and float."""
        pct = Percentage(30.0)
        result = pct + 20.0
        assert result.value == 50.0

    def test_radd(self):
        """Right add."""
        pct = Percentage(30.0)
        result = 20.0 + pct
        assert result.value == 50.0

    def test_sub_percentage(self):
        """Subtract Percentages."""
        pct1 = Percentage(50.0)
        pct2 = Percentage(20.0)
        result = pct1 - pct2
        assert result.value == 30.0

    def test_sub_float(self):
        """Subtract float from Percentage."""
        pct = Percentage(50.0)
        result = pct - 20.0
        assert result.value == 30.0

    def test_rsub(self):
        """Right subtract."""
        pct = Percentage(20.0)
        result = 50.0 - pct
        assert result.value == 30.0

    def test_mul(self):
        """Multiply by factor."""
        pct = Percentage(25.0)
        result = pct * 2
        assert result.value == 50.0

    def test_rmul(self):
        """Right multiply."""
        pct = Percentage(25.0)
        result = 2 * pct
        assert result.value == 50.0

    def test_truediv(self):
        """Divide by factor."""
        pct = Percentage(50.0)
        result = pct / 2
        assert result.value == 25.0

    def test_neg(self):
        """Negate."""
        pct = Percentage(50.0)
        result = -pct
        assert result.value == -50.0


class TestPercentageComparison:
    """Percentage comparison tests."""

    def test_lt_percentage(self):
        """Less than with Percentage."""
        pct1 = Percentage(30.0)
        pct2 = Percentage(50.0)
        assert pct1 < pct2
        assert not pct2 < pct1

    def test_lt_float(self):
        """Less than with float."""
        pct = Percentage(30.0)
        assert pct < 50.0
        assert not pct < 20.0

    def test_le_percentage(self):
        """Less than or equal with Percentage."""
        pct1 = Percentage(50.0)
        pct2 = Percentage(50.0)
        assert pct1 <= pct2

    def test_gt_percentage(self):
        """Greater than with Percentage."""
        pct1 = Percentage(50.0)
        pct2 = Percentage(30.0)
        assert pct1 > pct2

    def test_ge_percentage(self):
        """Greater than or equal with Percentage."""
        pct1 = Percentage(50.0)
        pct2 = Percentage(50.0)
        assert pct1 >= pct2


class TestPercentageString:
    """Percentage string representation tests."""

    def test_str(self):
        """String representation."""
        pct = Percentage(75.5)
        assert str(pct) == "75.50%"

    def test_repr(self):
        """Debug representation."""
        pct = Percentage(75.5)
        assert repr(pct) == "Percentage(75.5)"

    def test_format_default(self):
        """Format with default precision."""
        pct = Percentage(75.5)
        assert pct.format() == "75.50%"

    def test_format_custom_precision(self):
        """Format with custom precision."""
        pct = Percentage(75.555)
        assert pct.format(3) == "75.555%"


# =============================================================================
# PERCENTAGEREF TESTS
# =============================================================================


class TestPercentageRefConstruction:
    """PercentageRef construction tests."""

    def test_from_float(self):
        """Create from float."""
        pt = PercentageRef.from_float(75.5)
        assert isinstance(pt, PercentageRef)
        assert isinstance(pt.source, FuncCallOp)

    def test_from_dec(self):
        """Create from decimal."""
        pt = PercentageRef.from_dec(0.755)
        assert isinstance(pt, PercentageRef)

    def test_from_bps(self):
        """Create from basis points."""
        pt = PercentageRef.from_bps(7550)
        assert isinstance(pt, PercentageRef)


class TestPercentageRefConversions:
    """PercentageRef conversion method tests."""

    def test_to_dec_returns_floatref(self):
        """to_dec() returns FloatRef."""
        pt = PercentageRef.from_float(75.5)
        result = pt.to_dec()
        assert isinstance(result, FloatRef)

    def test_to_bps_returns_intref(self):
        """to_bps() returns IntRef."""
        pt = PercentageRef.from_float(75.5)
        result = pt.to_bps()
        assert isinstance(result, IntRef)

    def test_to_float_returns_floatref(self):
        """to_float() returns FloatRef."""
        pt = PercentageRef.from_float(75.5)
        result = pt.to_float()
        assert isinstance(result, FloatRef)


class TestPercentageRefApplication:
    """PercentageRef application method tests."""

    def test_apply_returns_floatref(self):
        """apply() returns FloatRef."""
        pt = PercentageRef.from_float(50.0)
        result = pt.apply(200)
        assert isinstance(result, FloatRef)

    def test_of_returns_floatref(self):
        """of() returns FloatRef."""
        pt = PercentageRef.from_float(50.0)
        result = pt.of(200)
        assert isinstance(result, FloatRef)

    def test_add_to_returns_floatref(self):
        """add_to() returns FloatRef."""
        pt = PercentageRef.from_float(10.0)
        result = pt.add_to(100)
        assert isinstance(result, FloatRef)

    def test_sub_from_returns_floatref(self):
        """sub_from() returns FloatRef."""
        pt = PercentageRef.from_float(10.0)
        result = pt.sub_from(100)
        assert isinstance(result, FloatRef)


class TestPercentageRefValidation:
    """PercentageRef validation method tests."""

    def test_is_valid_returns_boolref(self):
        """is_valid() returns BoolRef."""
        pt = PercentageRef.from_float(50.0)
        result = pt.is_valid()
        assert isinstance(result, BoolRef)

    def test_clamp_returns_percentageref(self):
        """clamp() returns PercentageRef."""
        pt = PercentageRef.from_float(150.0)
        result = pt.clamp()
        assert isinstance(result, PercentageRef)


class TestPercentageRefArithmetic:
    """PercentageRef arithmetic operation tests."""

    def test_add_returns_percentageref(self):
        """Addition returns PercentageRef."""
        pt = PercentageRef.from_float(30.0)
        result = pt + 20.0
        assert isinstance(result, PercentageRef)
        assert isinstance(result.source, AddOp)

    def test_sub_returns_percentageref(self):
        """Subtraction returns PercentageRef."""
        pt = PercentageRef.from_float(50.0)
        result = pt - 20.0
        assert isinstance(result, PercentageRef)
        assert isinstance(result.source, SubOp)

    def test_mul_returns_percentageref(self):
        """Multiplication returns PercentageRef."""
        pt = PercentageRef.from_float(25.0)
        result = pt * 2
        assert isinstance(result, PercentageRef)
        assert isinstance(result.source, MulOp)

    def test_truediv_returns_percentageref(self):
        """Division returns PercentageRef."""
        pt = PercentageRef.from_float(50.0)
        result = pt / 2
        assert isinstance(result, PercentageRef)
        assert isinstance(result.source, DivOp)
