"""Unit tests for Time type.

Tests for:
- TimeType (constructors, operations, methods)
"""

from everybase.type.time import TimeType
from everyterm.ops import FuncCallOp, MethodCallOp
from everyterm.types import IntType, StrType


# =============================================================================
# TIMETYPE CONSTRUCTION TESTS
# =============================================================================


class TestTimeTypeConstruction:
    """TimeType construction tests."""

    def test_from_iso(self):
        """Create from ISO format string."""
        tt = TimeType.from_iso("10:30:00")
        assert isinstance(tt, TimeType)
        assert isinstance(tt.source, FuncCallOp)

    def test_from_components(self):
        """Create from hour, minute, second components."""
        tt = TimeType.from_components(10, 30, 45)
        assert isinstance(tt, TimeType)

    def test_from_components_with_microsecond(self):
        """Create from components with microseconds."""
        tt = TimeType.from_components(10, 30, 45, 123456)
        assert isinstance(tt, TimeType)

    def test_midnight(self):
        """Create midnight time."""
        tt = TimeType.midnight()
        assert isinstance(tt, TimeType)

    def test_noon(self):
        """Create noon time."""
        tt = TimeType.noon()
        assert isinstance(tt, TimeType)


# =============================================================================
# TIMETYPE COMPONENT ACCESSOR TESTS
# =============================================================================


class TestTimeTypeAccessors:
    """TimeType component accessor tests."""

    def test_hour_returns_inttype(self):
        """hour() returns IntType."""
        tt = TimeType.from_iso("10:30:45")
        result = tt.hour()
        assert isinstance(result, IntType)

    def test_minute_returns_inttype(self):
        """minute() returns IntType."""
        tt = TimeType.from_iso("10:30:45")
        result = tt.minute()
        assert isinstance(result, IntType)

    def test_second_returns_inttype(self):
        """second() returns IntType."""
        tt = TimeType.from_iso("10:30:45")
        result = tt.second()
        assert isinstance(result, IntType)

    def test_microsecond_returns_inttype(self):
        """microsecond() returns IntType."""
        tt = TimeType.from_iso("10:30:45.123456")
        result = tt.microsecond()
        assert isinstance(result, IntType)


# =============================================================================
# TIMETYPE CONVERSION TESTS
# =============================================================================


class TestTimeTypeConversions:
    """TimeType conversion tests."""

    def test_isoformat_returns_strtype(self):
        """isoformat() returns StrType."""
        tt = TimeType.from_iso("10:30:45")
        result = tt.isoformat()
        assert isinstance(result, StrType)

    def test_isoformat_with_timespec(self):
        """isoformat() with timespec returns StrType."""
        tt = TimeType.from_iso("10:30:45.123456")
        result = tt.isoformat(timespec="seconds")
        assert isinstance(result, StrType)

    def test_strftime_returns_strtype(self):
        """strftime() returns StrType."""
        tt = TimeType.from_iso("10:30:45")
        result = tt.strftime("%H:%M:%S")
        assert isinstance(result, StrType)


# =============================================================================
# TIMETYPE MANIPULATION TESTS
# =============================================================================


class TestTimeTypeManipulation:
    """TimeType manipulation tests."""

    def test_replace_hour(self):
        """replace() with hour returns TimeType."""
        tt = TimeType.from_iso("10:30:45")
        result = tt.replace(hour=15)
        assert isinstance(result, TimeType)
        assert isinstance(result.source, MethodCallOp)

    def test_replace_minute(self):
        """replace() with minute returns TimeType."""
        tt = TimeType.from_iso("10:30:45")
        result = tt.replace(minute=0)
        assert isinstance(result, TimeType)

    def test_replace_second(self):
        """replace() with second returns TimeType."""
        tt = TimeType.from_iso("10:30:45")
        result = tt.replace(second=0)
        assert isinstance(result, TimeType)

    def test_replace_microsecond(self):
        """replace() with microsecond returns TimeType."""
        tt = TimeType.from_iso("10:30:45")
        result = tt.replace(microsecond=500000)
        assert isinstance(result, TimeType)

    def test_replace_multiple(self):
        """replace() with multiple components returns TimeType."""
        tt = TimeType.from_iso("10:30:45")
        result = tt.replace(hour=12, minute=0, second=0)
        assert isinstance(result, TimeType)
