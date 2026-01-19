"""Unit tests for Timezone type.

Tests for:
- TimezoneType (constructors, operations, methods)
"""

from datetime import UTC, timedelta, timezone

from everybase.type.timezone import TimezoneType
from everyterm.ops import FuncCallOp
from everyterm.types import StrType


# =============================================================================
# TIMEZONETYPE CONSTRUCTION TESTS
# =============================================================================


class TestTimezoneTypeConstruction:
    """TimezoneType construction tests."""

    def test_utc(self):
        """Create TimezoneType for UTC."""
        tz = TimezoneType.utc()
        assert isinstance(tz, TimezoneType)

    def test_from_offset_hours(self):
        """Create TimezoneType from hour offset."""
        tz = TimezoneType.from_offset(hours=5)
        assert isinstance(tz, TimezoneType)
        assert isinstance(tz.source, FuncCallOp)

    def test_from_offset_hours_and_minutes(self):
        """Create TimezoneType from hours and minutes offset."""
        tz = TimezoneType.from_offset(hours=5, minutes=30)
        assert isinstance(tz, TimezoneType)

    def test_from_offset_negative(self):
        """Create TimezoneType from negative offset."""
        tz = TimezoneType.from_offset(hours=-5)
        assert isinstance(tz, TimezoneType)

    def test_from_offset_with_name(self):
        """Create TimezoneType with a name."""
        tz = TimezoneType.from_offset(hours=-5, name="EST")
        assert isinstance(tz, TimezoneType)

    def test_from_timedelta(self):
        """Create TimezoneType from timedelta."""
        from everybase.type.timedelta import TimedeltaType

        td = TimedeltaType.from_components(hours=5)
        tz = TimezoneType.from_timedelta(td)
        assert isinstance(tz, TimezoneType)

    def test_from_raw_timezone(self):
        """Create TimezoneType from raw timezone object."""
        tz = TimezoneType(UTC)
        assert isinstance(tz, TimezoneType)

    def test_from_raw_timezone_with_offset(self):
        """Create TimezoneType from raw timezone with offset."""
        raw_tz = timezone(timedelta(hours=5))
        tz = TimezoneType(raw_tz)
        assert isinstance(tz, TimezoneType)


# =============================================================================
# TIMEZONETYPE METHOD TESTS
# =============================================================================


class TestTimezoneTypeMethods:
    """TimezoneType method tests."""

    def test_tzname_returns_strtype(self):
        """tzname() returns StrType."""
        tz = TimezoneType.utc()
        result = tz.tzname(None)
        assert isinstance(result, StrType)

    def test_utcoffset_returns_timedeltaype(self):
        """utcoffset() returns TimedeltaType."""
        from everybase.type.timedelta import TimedeltaType

        tz = TimezoneType.from_offset(hours=5)
        result = tz.utcoffset(None)
        assert isinstance(result, TimedeltaType)

    def test_dst(self):
        """dst() returns NoneType."""
        from everyterm.types import NoneType

        tz = TimezoneType.utc()
        result = tz.dst(None)
        # dst returns NoneType for fixed-offset timezones
        assert isinstance(result, NoneType)


# =============================================================================
# TIMEZONETYPE EQUALITY TESTS
# =============================================================================


class TestTimezoneTypeEquality:
    """TimezoneType equality tests."""

    def test_eq_with_raw_timezone(self):
        """Test equality with raw timezone."""
        tz = TimezoneType.utc()
        result = tz == UTC
        # Returns a BoolType
        assert result is not None

    def test_eq_with_timezonetype(self):
        """Test equality with another TimezoneType."""
        tz1 = TimezoneType.utc()
        tz2 = TimezoneType.utc()
        result = tz1 == tz2
        assert result is not None

    def test_ne_with_raw_timezone(self):
        """Test inequality with raw timezone."""
        tz = TimezoneType.from_offset(hours=5)
        result = tz != UTC
        assert result is not None
