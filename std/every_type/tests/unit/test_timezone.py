"""Unit tests for Timezone ref.

Tests for:
- TimezoneRef (constructors, operations, methods)
"""

from datetime import UTC, timedelta, timezone

from every_type import TimedeltaRef, TimezoneRef
from everybase.morphisms import FuncCallOp
from everybase.py import BoolRef, NoneRef, StrRef


# =============================================================================
# TIMEZONEREF CONSTRUCTION TESTS
# =============================================================================


class TestTimezoneRefConstruction:
    """TimezoneRef construction tests."""

    def test_utc(self):
        """Create TimezoneRef for UTC."""
        tz = TimezoneRef.utc()
        assert isinstance(tz, TimezoneRef)

    def test_from_offset_hours(self):
        """Create TimezoneRef from hour offset."""
        tz = TimezoneRef.from_offset(hours=5)
        assert isinstance(tz, TimezoneRef)
        assert isinstance(tz.source, FuncCallOp)

    def test_from_offset_hours_and_minutes(self):
        """Create TimezoneRef from hours and minutes offset."""
        tz = TimezoneRef.from_offset(hours=5, minutes=30)
        assert isinstance(tz, TimezoneRef)

    def test_from_offset_negative(self):
        """Create TimezoneRef from negative offset."""
        tz = TimezoneRef.from_offset(hours=-5)
        assert isinstance(tz, TimezoneRef)

    def test_from_offset_with_name(self):
        """Create TimezoneRef with a name."""
        tz = TimezoneRef.from_offset(hours=-5, name="EST")
        assert isinstance(tz, TimezoneRef)

    def test_from_timedelta(self):
        """Create TimezoneRef from timedelta."""
        td = TimedeltaRef.from_components(hours=5)
        tz = TimezoneRef.from_timedelta(td)
        assert isinstance(tz, TimezoneRef)

    def test_from_raw_timezone(self):
        """Create TimezoneRef from raw timezone object."""
        tz = TimezoneRef(UTC)
        assert isinstance(tz, TimezoneRef)

    def test_from_raw_timezone_with_offset(self):
        """Create TimezoneRef from raw timezone with offset."""
        raw_tz = timezone(timedelta(hours=5))
        tz = TimezoneRef(raw_tz)
        assert isinstance(tz, TimezoneRef)


# =============================================================================
# TIMEZONEREF METHOD TESTS
# =============================================================================


class TestTimezoneRefMethods:
    """TimezoneRef method tests."""

    def test_tzname_returns_strref(self):
        """tzname() returns StrRef."""
        tz = TimezoneRef.utc()
        result = tz.tzname(None)
        assert isinstance(result, StrRef)

    def test_utcoffset_returns_timedeltaref(self):
        """utcoffset() returns TimedeltaRef."""
        tz = TimezoneRef.from_offset(hours=5)
        result = tz.utcoffset(None)
        assert isinstance(result, TimedeltaRef)

    def test_dst(self):
        """dst() returns NoneRef."""
        tz = TimezoneRef.utc()
        result = tz.dst(None)
        # dst returns NoneRef for fixed-offset timezones
        assert isinstance(result, NoneRef)


# =============================================================================
# TIMEZONEREF EQUALITY TESTS
# =============================================================================


class TestTimezoneRefEquality:
    """TimezoneRef equality tests."""

    def test_eq_with_raw_timezone(self):
        """Test equality with raw timezone."""
        tz = TimezoneRef.utc()
        result = tz.eq(UTC)
        # Returns a BoolRef
        assert isinstance(result, BoolRef)

    def test_eq_with_timezoneref(self):
        """Test equality with another TimezoneRef."""
        tz1 = TimezoneRef.utc()
        tz2 = TimezoneRef.utc()
        result = tz1.eq(tz2)
        assert isinstance(result, BoolRef)

    def test_ne_with_raw_timezone(self):
        """Test inequality with raw timezone."""
        tz = TimezoneRef.from_offset(hours=5)
        result = tz.ne(UTC)
        assert isinstance(result, BoolRef)
