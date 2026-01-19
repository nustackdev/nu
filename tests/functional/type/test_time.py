"""Functional tests for Time type.

Tests TimeType and TimeSlot execution with real storage context.
"""

from datetime import time

from everybase.type import TimeType


# ============================================================================
# TIME SET AND GET TESTS
# ============================================================================


class TestTimeSetAndGet:
    """Test setting and getting time values through storage."""

    def test_set_and_get_time(self, time_shape, ctx):
        """Set and retrieve a time value."""
        t = time(10, 30, 45)
        time_shape.start_time.set(t).execute(ctx)
        result = time_shape.start_time.get().execute(ctx)
        assert result == t

    def test_set_time_with_microsecond(self, time_shape, ctx):
        """Set time with microseconds."""
        t = time(10, 30, 45, 123456)
        time_shape.start_time.set(t).execute(ctx)
        result = time_shape.start_time.get().execute(ctx)
        assert result == t

    def test_set_multiple_times(self, time_shape, ctx):
        """Set multiple time slots."""
        start = time(8, 0, 0)
        end = time(17, 0, 0)

        time_shape.start_time.set(start).execute(ctx)
        time_shape.end_time.set(end).execute(ctx)

        assert time_shape.start_time.get().execute(ctx) == start
        assert time_shape.end_time.get().execute(ctx) == end


# ============================================================================
# TIME COMPONENT ACCESS TESTS
# ============================================================================


class TestTimeComponentAccess:
    """Test accessing time components."""

    def test_hour_component(self, time_shape, ctx):
        """Access hour component."""
        t = time(10, 30, 45)
        time_shape.start_time.set(t).execute(ctx)
        assert time_shape.start_time.hour().execute(ctx) == 10

    def test_minute_component(self, time_shape, ctx):
        """Access minute component."""
        t = time(10, 30, 45)
        time_shape.start_time.set(t).execute(ctx)
        assert time_shape.start_time.minute().execute(ctx) == 30

    def test_second_component(self, time_shape, ctx):
        """Access second component."""
        t = time(10, 30, 45)
        time_shape.start_time.set(t).execute(ctx)
        assert time_shape.start_time.second().execute(ctx) == 45

    def test_microsecond_component(self, time_shape, ctx):
        """Access microsecond component."""
        t = time(10, 30, 45, 123456)
        time_shape.start_time.set(t).execute(ctx)
        assert time_shape.start_time.microsecond().execute(ctx) == 123456


# ============================================================================
# TIME CONVERSION TESTS
# ============================================================================


class TestTimeConversions:
    """Test time conversions."""

    def test_isoformat(self, time_shape, ctx):
        """Convert to ISO format string."""
        t = time(10, 30, 45)
        time_shape.start_time.set(t).execute(ctx)
        result = time_shape.start_time.isoformat().execute(ctx)
        assert result == "10:30:45"

    def test_isoformat_with_timespec(self, time_shape, ctx):
        """Convert to ISO format with timespec."""
        t = time(10, 30, 45, 123456)
        time_shape.start_time.set(t).execute(ctx)
        result = time_shape.start_time.isoformat(timespec="seconds").execute(ctx)
        assert result == "10:30:45"

    def test_strftime(self, time_shape, ctx):
        """Format time with custom format."""
        t = time(10, 30, 45)
        time_shape.start_time.set(t).execute(ctx)
        result = time_shape.start_time.strftime("%H:%M").execute(ctx)
        assert result == "10:30"


# ============================================================================
# TIMETYPE CONSTRUCTOR TESTS
# ============================================================================


class TestTimeTypeConstructors:
    """Test TimeType constructors with execution."""

    def test_from_iso(self, ctx):
        """Create from ISO format string."""
        result = TimeType.from_iso("10:30:45").execute(ctx)
        assert result == time(10, 30, 45)

    def test_from_components(self, ctx):
        """Create from time components."""
        result = TimeType.from_components(10, 30, 45).execute(ctx)
        assert result == time(10, 30, 45)

    def test_from_components_with_microsecond(self, ctx):
        """Create from components with microseconds."""
        result = TimeType.from_components(10, 30, 45, 123456).execute(ctx)
        assert result == time(10, 30, 45, 123456)

    def test_midnight(self, ctx):
        """Create midnight time."""
        result = TimeType.midnight().execute(ctx)
        assert result == time(0, 0, 0)

    def test_noon(self, ctx):
        """Create noon time."""
        result = TimeType.noon().execute(ctx)
        assert result == time(12, 0, 0)


# ============================================================================
# TIME MANIPULATION TESTS
# ============================================================================


class TestTimeManipulation:
    """Test time manipulation operations."""

    def test_replace_hour(self, time_shape, ctx):
        """Replace hour component."""
        t = time(10, 30, 45)
        time_shape.start_time.set(t).execute(ctx)

        result = time_shape.start_time.get().replace(hour=15).execute(ctx)
        assert result == time(15, 30, 45)

    def test_replace_minute(self, time_shape, ctx):
        """Replace minute component."""
        t = time(10, 30, 45)
        time_shape.start_time.set(t).execute(ctx)

        result = time_shape.start_time.get().replace(minute=0).execute(ctx)
        assert result == time(10, 0, 45)

    def test_replace_second(self, time_shape, ctx):
        """Replace second component."""
        t = time(10, 30, 45)
        time_shape.start_time.set(t).execute(ctx)

        result = time_shape.start_time.get().replace(second=0).execute(ctx)
        assert result == time(10, 30, 0)

    def test_replace_multiple(self, time_shape, ctx):
        """Replace multiple components."""
        t = time(10, 30, 45)
        time_shape.start_time.set(t).execute(ctx)

        result = time_shape.start_time.get().replace(hour=12, minute=0, second=0).execute(ctx)
        assert result == time(12, 0, 0)


# ============================================================================
# TIME COMPARISON TESTS
# ============================================================================


class TestTimeComparison:
    """Test time comparison operations."""

    def test_less_than(self, time_shape, ctx):
        """Compare times with less than."""
        time_shape.start_time.set(time(8, 0, 0)).execute(ctx)
        time_shape.end_time.set(time(17, 0, 0)).execute(ctx)

        result = (time_shape.start_time.get() < time_shape.end_time.get()).execute(ctx)
        assert result is True

    def test_greater_than(self, time_shape, ctx):
        """Compare times with greater than."""
        time_shape.start_time.set(time(17, 0, 0)).execute(ctx)
        time_shape.end_time.set(time(8, 0, 0)).execute(ctx)

        result = (time_shape.start_time.get() > time_shape.end_time.get()).execute(ctx)
        assert result is True

    def test_equals(self, time_shape, ctx):
        """Compare times for equality."""
        time_shape.start_time.set(time(12, 0, 0)).execute(ctx)
        time_shape.end_time.set(time(12, 0, 0)).execute(ctx)

        result = (time_shape.start_time.get() == time_shape.end_time.get()).execute(ctx)
        assert result is True
