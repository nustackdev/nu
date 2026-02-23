"""Unit tests for Time ref.

Tests for:
- TimeRef (constructors, operations, methods)
"""

from eb_datetime import TimeValue as TimeRef
from everybase.abc import FuncCallOp, MethodCallOp
from everybase.abc import IntValue as IntRef
from everybase.abc import StrValue as StrRef


# =============================================================================
# TIMEREF CONSTRUCTION TESTS
# =============================================================================


class TestTimeRefConstruction:
    """TimeRef construction tests."""

    def test_from_iso(self):
        """Create from ISO format string."""
        tt = TimeRef.from_iso("10:30:00")
        assert isinstance(tt, TimeRef)
        assert isinstance(tt.source, FuncCallOp)

    def test_from_components(self):
        """Create from hour, minute, second components."""
        tt = TimeRef.from_components(10, 30, 45)
        assert isinstance(tt, TimeRef)

    def test_from_components_with_microsecond(self):
        """Create from components with microseconds."""
        tt = TimeRef.from_components(10, 30, 45, 123456)
        assert isinstance(tt, TimeRef)

    def test_midnight(self):
        """Create midnight time."""
        tt = TimeRef.midnight()
        assert isinstance(tt, TimeRef)

    def test_noon(self):
        """Create noon time."""
        tt = TimeRef.noon()
        assert isinstance(tt, TimeRef)


# =============================================================================
# TIMEREF COMPONENT ACCESSOR TESTS
# =============================================================================


class TestTimeRefAccessors:
    """TimeRef component accessor tests."""

    def test_hour_returns_intref(self):
        """hour() returns IntRef."""
        tt = TimeRef.from_iso("10:30:45")
        result = tt.hour()
        assert isinstance(result, IntRef)

    def test_minute_returns_intref(self):
        """minute() returns IntRef."""
        tt = TimeRef.from_iso("10:30:45")
        result = tt.minute()
        assert isinstance(result, IntRef)

    def test_second_returns_intref(self):
        """second() returns IntRef."""
        tt = TimeRef.from_iso("10:30:45")
        result = tt.second()
        assert isinstance(result, IntRef)

    def test_microsecond_returns_intref(self):
        """microsecond() returns IntRef."""
        tt = TimeRef.from_iso("10:30:45.123456")
        result = tt.microsecond()
        assert isinstance(result, IntRef)


# =============================================================================
# TIMEREF CONVERSION TESTS
# =============================================================================


class TestTimeRefConversions:
    """TimeRef conversion tests."""

    def test_isoformat_returns_strref(self):
        """isoformat() returns StrRef."""
        tt = TimeRef.from_iso("10:30:45")
        result = tt.isoformat()
        assert isinstance(result, StrRef)

    def test_isoformat_with_timespec(self):
        """isoformat() with timespec returns StrRef."""
        tt = TimeRef.from_iso("10:30:45.123456")
        result = tt.isoformat(timespec="seconds")
        assert isinstance(result, StrRef)

    def test_strftime_returns_strref(self):
        """strftime() returns StrRef."""
        tt = TimeRef.from_iso("10:30:45")
        result = tt.strftime("%H:%M:%S")
        assert isinstance(result, StrRef)


# =============================================================================
# TIMEREF MANIPULATION TESTS
# =============================================================================


class TestTimeRefManipulation:
    """TimeRef manipulation tests."""

    def test_replace_hour(self):
        """replace() with hour returns TimeRef."""
        tt = TimeRef.from_iso("10:30:45")
        result = tt.replace(hour=15)
        assert isinstance(result, TimeRef)
        assert isinstance(result.source, MethodCallOp)

    def test_replace_minute(self):
        """replace() with minute returns TimeRef."""
        tt = TimeRef.from_iso("10:30:45")
        result = tt.replace(minute=0)
        assert isinstance(result, TimeRef)

    def test_replace_second(self):
        """replace() with second returns TimeRef."""
        tt = TimeRef.from_iso("10:30:45")
        result = tt.replace(second=0)
        assert isinstance(result, TimeRef)

    def test_replace_microsecond(self):
        """replace() with microsecond returns TimeRef."""
        tt = TimeRef.from_iso("10:30:45")
        result = tt.replace(microsecond=500000)
        assert isinstance(result, TimeRef)

    def test_replace_multiple(self):
        """replace() with multiple components returns TimeRef."""
        tt = TimeRef.from_iso("10:30:45")
        result = tt.replace(hour=12, minute=0, second=0)
        assert isinstance(result, TimeRef)
