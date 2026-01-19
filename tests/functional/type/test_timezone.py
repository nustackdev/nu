"""Functional tests for Timezone type.

Tests TimezoneType and TimezoneSlot execution with real storage context.
"""

from datetime import UTC, timedelta, timezone

from everybase.type import TimezoneType


# ============================================================================
# TIMEZONE SET AND GET TESTS
# ============================================================================


class TestTimezoneSetAndGet:
    """Test setting and getting timezone values through storage."""

    def test_set_and_get_utc(self, timezone_shape, ctx):
        """Set and retrieve UTC timezone."""
        timezone_shape.local_tz.set(UTC).execute(ctx)
        result = timezone_shape.local_tz.get().execute(ctx)
        # UTC offset should be 0
        assert result.utcoffset(None) == timedelta(0)

    def test_set_and_get_positive_offset(self, timezone_shape, ctx):
        """Set and retrieve timezone with positive offset."""
        tz = timezone(timedelta(hours=5, minutes=30))
        timezone_shape.local_tz.set(tz).execute(ctx)
        result = timezone_shape.local_tz.get().execute(ctx)
        assert result.utcoffset(None) == timedelta(hours=5, minutes=30)

    def test_set_and_get_negative_offset(self, timezone_shape, ctx):
        """Set and retrieve timezone with negative offset."""
        tz = timezone(timedelta(hours=-5))
        timezone_shape.local_tz.set(tz).execute(ctx)
        result = timezone_shape.local_tz.get().execute(ctx)
        assert result.utcoffset(None) == timedelta(hours=-5)

    def test_set_multiple_timezones(self, timezone_shape, ctx):
        """Set multiple timezone slots."""
        local = timezone(timedelta(hours=5))
        display = timezone(timedelta(hours=-8))

        timezone_shape.local_tz.set(local).execute(ctx)
        timezone_shape.display_tz.set(display).execute(ctx)

        local_result = timezone_shape.local_tz.get().execute(ctx)
        display_result = timezone_shape.display_tz.get().execute(ctx)

        assert local_result.utcoffset(None) == timedelta(hours=5)
        assert display_result.utcoffset(None) == timedelta(hours=-8)


# ============================================================================
# TIMEZONETYPE CONSTRUCTOR TESTS
# ============================================================================


class TestTimezoneTypeConstructors:
    """Test TimezoneType constructors with execution."""

    def test_utc(self, ctx):
        """Create and execute TimezoneType.utc()."""
        result = TimezoneType.utc().execute(ctx)
        assert result == UTC

    def test_from_offset_hours(self, ctx):
        """Create timezone from hour offset."""
        result = TimezoneType.from_offset(hours=5).execute(ctx)
        assert result.utcoffset(None) == timedelta(hours=5)

    def test_from_offset_hours_and_minutes(self, ctx):
        """Create timezone from hours and minutes."""
        result = TimezoneType.from_offset(hours=5, minutes=30).execute(ctx)
        assert result.utcoffset(None) == timedelta(hours=5, minutes=30)

    def test_from_offset_negative(self, ctx):
        """Create timezone from negative offset."""
        result = TimezoneType.from_offset(hours=-8).execute(ctx)
        assert result.utcoffset(None) == timedelta(hours=-8)

    def test_from_offset_with_name(self, ctx):
        """Create timezone with a name."""
        result = TimezoneType.from_offset(hours=-5, name="EST").execute(ctx)
        assert result.tzname(None) == "EST"
        assert result.utcoffset(None) == timedelta(hours=-5)


# ============================================================================
# TIMEZONE METHOD TESTS
# ============================================================================


class TestTimezoneMethods:
    """Test timezone method operations."""

    def test_tzname_utc(self, ctx):
        """Get timezone name for UTC."""
        result = TimezoneType.utc().tzname(None).execute(ctx)
        assert result == "UTC"

    def test_tzname_offset(self, ctx):
        """Get timezone name for offset timezone."""
        tz = TimezoneType.from_offset(hours=5)
        result = tz.tzname(None).execute(ctx)
        # Offset-based timezones return UTC+HH:MM format
        assert "05:00" in result or "+05" in result

    def test_utcoffset(self, ctx):
        """Get UTC offset as timedelta."""
        tz = TimezoneType.from_offset(hours=5, minutes=30)
        result = tz.utcoffset(None).execute(ctx)
        assert result == timedelta(hours=5, minutes=30)

    def test_dst_returns_none(self, ctx):
        """DST returns None for fixed-offset timezones."""
        tz = TimezoneType.from_offset(hours=5)
        result = tz.dst(None).execute(ctx)
        assert result is None


# ============================================================================
# TIMEZONE WITH DATETIME TESTS
# ============================================================================


class TestTimezoneWithDatetime:
    """Test timezone integration with datetime operations."""

    def test_datetime_now_with_timezone(self, ctx):
        """Use TimezoneType with datetime.now()."""
        from everybase.type.datetime import DatetimeType

        tz = TimezoneType.utc()
        dt = DatetimeType.now(tz=tz).execute(ctx)
        assert dt.tzinfo is not None

    def test_datetime_from_timestamp_with_timezone(self, ctx):
        """Use TimezoneType with datetime.from_timestamp()."""
        from everybase.type.datetime import DatetimeType

        tz = TimezoneType.from_offset(hours=5)
        ts = 1718444445.0  # June 15, 2024 approximate
        dt = DatetimeType.from_timestamp(ts, tz=tz).execute(ctx)
        assert dt.tzinfo is not None


# ============================================================================
# TIMEZONE EQUALITY TESTS
# ============================================================================


class TestTimezoneEquality:
    """Test timezone equality operations."""

    def test_utc_equals_utc(self, ctx):
        """UTC equals UTC."""
        result = (TimezoneType.utc() == UTC).execute(ctx)
        assert result is True

    def test_same_offset_equals(self, ctx):
        """Same offset timezones are equal."""
        tz1 = TimezoneType.from_offset(hours=5)
        tz2 = TimezoneType.from_offset(hours=5)
        result = (tz1 == tz2).execute(ctx)
        assert result is True

    def test_different_offset_not_equals(self, ctx):
        """Different offset timezones are not equal."""
        tz1 = TimezoneType.from_offset(hours=5)
        tz2 = TimezoneType.from_offset(hours=-5)
        result = (tz1 != tz2).execute(ctx)
        assert result is True
