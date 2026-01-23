"""Unit tests for Timedelta ref.

Tests for:
- TimedeltaRef (constructors, operations, methods)
"""

from datetime import timedelta

from every_type import TimedeltaRef
from everybase.morphisms import AddOp, DivOp, FloorDivOp, FuncCallOp, ModOp, MulOp, SubOp
from everybase.py import FloatRef, IntRef


# =============================================================================
# TIMEDELTAREF CONSTRUCTION TESTS
# =============================================================================


class TestTimedeltaRefConstruction:
    """TimedeltaRef construction tests."""

    def test_from_seconds(self):
        """Create from seconds."""
        td = TimedeltaRef.from_seconds(3600)
        assert isinstance(td, TimedeltaRef)
        assert isinstance(td.source, FuncCallOp)

    def test_from_components(self):
        """Create from time components."""
        td = TimedeltaRef.from_components(days=1, hours=2, minutes=30)
        assert isinstance(td, TimedeltaRef)

    def test_from_components_all(self):
        """Create from all time components."""
        td = TimedeltaRef.from_components(
            days=1,
            seconds=30,
            microseconds=500,
            milliseconds=100,
            minutes=15,
            hours=2,
            weeks=1,
        )
        assert isinstance(td, TimedeltaRef)


# =============================================================================
# TIMEDELTAREF COMPONENT ACCESSOR TESTS
# =============================================================================


class TestTimedeltaRefAccessors:
    """TimedeltaRef component accessor tests."""

    def test_days_returns_intref(self):
        """days() returns IntRef."""
        td = TimedeltaRef.from_seconds(86400 * 2 + 3600)
        result = td.days()
        assert isinstance(result, IntRef)

    def test_seconds_returns_intref(self):
        """seconds() returns IntRef."""
        td = TimedeltaRef.from_seconds(3661)
        result = td.seconds()
        assert isinstance(result, IntRef)

    def test_microseconds_returns_intref(self):
        """microseconds() returns IntRef."""
        td = TimedeltaRef.from_components(microseconds=123456)
        result = td.microseconds()
        assert isinstance(result, IntRef)


# =============================================================================
# TIMEDELTAREF CONVERSION TESTS
# =============================================================================


class TestTimedeltaRefConversions:
    """TimedeltaRef conversion tests."""

    def test_total_seconds_returns_floatref(self):
        """total_seconds() returns FloatRef."""
        td = TimedeltaRef.from_components(hours=1)
        result = td.total_seconds()
        assert isinstance(result, FloatRef)

    def test_total_minutes_returns_floatref(self):
        """total_minutes() returns FloatRef."""
        td = TimedeltaRef.from_components(hours=2)
        result = td.total_minutes()
        assert isinstance(result, FloatRef)

    def test_total_hours_returns_floatref(self):
        """total_hours() returns FloatRef."""
        td = TimedeltaRef.from_components(days=1)
        result = td.total_hours()
        assert isinstance(result, FloatRef)

    def test_total_days_returns_floatref(self):
        """total_days() returns FloatRef."""
        td = TimedeltaRef.from_components(weeks=2)
        result = td.total_days()
        assert isinstance(result, FloatRef)


# =============================================================================
# TIMEDELTAREF ARITHMETIC TESTS
# =============================================================================


class TestTimedeltaRefArithmetic:
    """TimedeltaRef arithmetic tests."""

    def test_add_returns_timedeltaref(self):
        """Addition returns TimedeltaRef."""
        td = TimedeltaRef.from_seconds(3600)
        result = td + timedelta(hours=1)
        assert isinstance(result, TimedeltaRef)
        assert isinstance(result.source, AddOp)

    def test_radd(self):
        """Right addition works."""
        td = TimedeltaRef.from_seconds(3600)
        result = timedelta(hours=1) + td
        assert isinstance(result, TimedeltaRef)

    def test_sub_returns_timedeltaref(self):
        """Subtraction returns TimedeltaRef."""
        td = TimedeltaRef.from_seconds(3600)
        result = td - timedelta(minutes=30)
        assert isinstance(result, TimedeltaRef)
        assert isinstance(result.source, SubOp)

    def test_rsub(self):
        """Right subtraction works."""
        td = TimedeltaRef.from_seconds(1800)
        result = timedelta(hours=1) - td
        assert isinstance(result, TimedeltaRef)

    def test_mul_int_returns_timedeltaref(self):
        """Multiplication by int returns TimedeltaRef."""
        td = TimedeltaRef.from_seconds(3600)
        result = td * 2
        assert isinstance(result, TimedeltaRef)
        assert isinstance(result.source, MulOp)

    def test_mul_float_returns_timedeltaref(self):
        """Multiplication by float returns TimedeltaRef."""
        td = TimedeltaRef.from_seconds(3600)
        result = td * 1.5
        assert isinstance(result, TimedeltaRef)

    def test_rmul(self):
        """Right multiplication works."""
        td = TimedeltaRef.from_seconds(3600)
        result = 3 * td
        assert isinstance(result, TimedeltaRef)

    def test_truediv_scalar_returns_timedeltaref(self):
        """Division by scalar returns TimedeltaRef."""
        td = TimedeltaRef.from_seconds(3600)
        result = td / 2
        assert isinstance(result, TimedeltaRef)
        assert isinstance(result.source, DivOp)

    def test_truediv_timedelta_returns_floatref(self):
        """Division by timedelta returns FloatRef."""
        td = TimedeltaRef.from_seconds(7200)
        result = td / timedelta(hours=1)
        assert isinstance(result, FloatRef)

    def test_floordiv_returns_timedeltaref(self):
        """Floor division returns TimedeltaRef."""
        td = TimedeltaRef.from_seconds(3600)
        result = td // 2
        assert isinstance(result, TimedeltaRef)
        assert isinstance(result.source, FloorDivOp)

    def test_mod_returns_timedeltaref(self):
        """Modulo returns TimedeltaRef."""
        td = TimedeltaRef.from_seconds(5000)
        result = td % timedelta(hours=1)
        assert isinstance(result, TimedeltaRef)
        assert isinstance(result.source, ModOp)

    def test_neg(self):
        """Negation returns TimedeltaRef."""
        td = TimedeltaRef.from_seconds(3600)
        result = -td
        assert isinstance(result, TimedeltaRef)

    def test_pos(self):
        """Positive returns TimedeltaRef."""
        td = TimedeltaRef.from_seconds(3600)
        result = +td
        assert isinstance(result, TimedeltaRef)
