"""Unit tests for Timedelta type.

Tests for:
- TimedeltaType (constructors, operations, methods)
"""

from datetime import timedelta

from everybase.type.timedelta import TimedeltaType
from everyterm.ops import AddOp, DivOp, FloorDivOp, FuncCallOp, ModOp, MulOp, SubOp
from everyterm.types import FloatType, IntType


# =============================================================================
# TIMEDELTATYPE CONSTRUCTION TESTS
# =============================================================================


class TestTimedeltaTypeConstruction:
    """TimedeltaType construction tests."""

    def test_from_seconds(self):
        """Create from seconds."""
        td = TimedeltaType.from_seconds(3600)
        assert isinstance(td, TimedeltaType)
        assert isinstance(td.source, FuncCallOp)

    def test_from_components(self):
        """Create from time components."""
        td = TimedeltaType.from_components(days=1, hours=2, minutes=30)
        assert isinstance(td, TimedeltaType)

    def test_from_components_all(self):
        """Create from all time components."""
        td = TimedeltaType.from_components(
            days=1,
            seconds=30,
            microseconds=500,
            milliseconds=100,
            minutes=15,
            hours=2,
            weeks=1,
        )
        assert isinstance(td, TimedeltaType)


# =============================================================================
# TIMEDELTATYPE COMPONENT ACCESSOR TESTS
# =============================================================================


class TestTimedeltaTypeAccessors:
    """TimedeltaType component accessor tests."""

    def test_days_returns_inttype(self):
        """days() returns IntType."""
        td = TimedeltaType.from_seconds(86400 * 2 + 3600)
        result = td.days()
        assert isinstance(result, IntType)

    def test_seconds_returns_inttype(self):
        """seconds() returns IntType."""
        td = TimedeltaType.from_seconds(3661)
        result = td.seconds()
        assert isinstance(result, IntType)

    def test_microseconds_returns_inttype(self):
        """microseconds() returns IntType."""
        td = TimedeltaType.from_components(microseconds=123456)
        result = td.microseconds()
        assert isinstance(result, IntType)


# =============================================================================
# TIMEDELTATYPE CONVERSION TESTS
# =============================================================================


class TestTimedeltaTypeConversions:
    """TimedeltaType conversion tests."""

    def test_total_seconds_returns_floattype(self):
        """total_seconds() returns FloatType."""
        td = TimedeltaType.from_components(hours=1)
        result = td.total_seconds()
        assert isinstance(result, FloatType)

    def test_total_minutes_returns_floattype(self):
        """total_minutes() returns FloatType."""
        td = TimedeltaType.from_components(hours=2)
        result = td.total_minutes()
        assert isinstance(result, FloatType)

    def test_total_hours_returns_floattype(self):
        """total_hours() returns FloatType."""
        td = TimedeltaType.from_components(days=1)
        result = td.total_hours()
        assert isinstance(result, FloatType)

    def test_total_days_returns_floattype(self):
        """total_days() returns FloatType."""
        td = TimedeltaType.from_components(weeks=2)
        result = td.total_days()
        assert isinstance(result, FloatType)


# =============================================================================
# TIMEDELTATYPE ARITHMETIC TESTS
# =============================================================================


class TestTimedeltaTypeArithmetic:
    """TimedeltaType arithmetic tests."""

    def test_add_returns_timedeltatype(self):
        """Addition returns TimedeltaType."""
        td = TimedeltaType.from_seconds(3600)
        result = td + timedelta(hours=1)
        assert isinstance(result, TimedeltaType)
        assert isinstance(result.source, AddOp)

    def test_radd(self):
        """Right addition works."""
        td = TimedeltaType.from_seconds(3600)
        result = timedelta(hours=1) + td
        assert isinstance(result, TimedeltaType)

    def test_sub_returns_timedeltatype(self):
        """Subtraction returns TimedeltaType."""
        td = TimedeltaType.from_seconds(3600)
        result = td - timedelta(minutes=30)
        assert isinstance(result, TimedeltaType)
        assert isinstance(result.source, SubOp)

    def test_rsub(self):
        """Right subtraction works."""
        td = TimedeltaType.from_seconds(1800)
        result = timedelta(hours=1) - td
        assert isinstance(result, TimedeltaType)

    def test_mul_int_returns_timedeltatype(self):
        """Multiplication by int returns TimedeltaType."""
        td = TimedeltaType.from_seconds(3600)
        result = td * 2
        assert isinstance(result, TimedeltaType)
        assert isinstance(result.source, MulOp)

    def test_mul_float_returns_timedeltatype(self):
        """Multiplication by float returns TimedeltaType."""
        td = TimedeltaType.from_seconds(3600)
        result = td * 1.5
        assert isinstance(result, TimedeltaType)

    def test_rmul(self):
        """Right multiplication works."""
        td = TimedeltaType.from_seconds(3600)
        result = 3 * td
        assert isinstance(result, TimedeltaType)

    def test_truediv_scalar_returns_timedeltatype(self):
        """Division by scalar returns TimedeltaType."""
        td = TimedeltaType.from_seconds(3600)
        result = td / 2
        assert isinstance(result, TimedeltaType)
        assert isinstance(result.source, DivOp)

    def test_truediv_timedelta_returns_floattype(self):
        """Division by timedelta returns FloatType."""
        td = TimedeltaType.from_seconds(7200)
        result = td / timedelta(hours=1)
        assert isinstance(result, FloatType)

    def test_floordiv_returns_timedeltatype(self):
        """Floor division returns TimedeltaType."""
        td = TimedeltaType.from_seconds(3600)
        result = td // 2
        assert isinstance(result, TimedeltaType)
        assert isinstance(result.source, FloorDivOp)

    def test_mod_returns_timedeltatype(self):
        """Modulo returns TimedeltaType."""
        td = TimedeltaType.from_seconds(5000)
        result = td % timedelta(hours=1)
        assert isinstance(result, TimedeltaType)
        assert isinstance(result.source, ModOp)

    def test_neg(self):
        """Negation returns TimedeltaType."""
        td = TimedeltaType.from_seconds(3600)
        result = -td
        assert isinstance(result, TimedeltaType)

    def test_pos(self):
        """Positive returns TimedeltaType."""
        td = TimedeltaType.from_seconds(3600)
        result = +td
        assert isinstance(result, TimedeltaType)
