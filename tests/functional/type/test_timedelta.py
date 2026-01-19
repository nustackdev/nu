"""Functional tests for Timedelta type.

Tests TimedeltaType and TimedeltaSlot execution with real storage context.
"""

from datetime import timedelta

from everybase.type import TimedeltaType


# ============================================================================
# TIMEDELTA SET AND GET TESTS
# ============================================================================


class TestTimedeltaSetAndGet:
    """Test setting and getting timedelta values through storage."""

    def test_set_and_get_timedelta(self, timedelta_shape, ctx):
        """Set and retrieve a timedelta value."""
        td = timedelta(hours=2, minutes=30)
        timedelta_shape.duration.set(td).execute(ctx)
        result = timedelta_shape.duration.get().execute(ctx)
        assert result == td

    def test_set_timedelta_days(self, timedelta_shape, ctx):
        """Set timedelta with days."""
        td = timedelta(days=5)
        timedelta_shape.duration.set(td).execute(ctx)
        result = timedelta_shape.duration.get().execute(ctx)
        assert result == td

    def test_set_timedelta_negative(self, timedelta_shape, ctx):
        """Set negative timedelta."""
        td = timedelta(days=-1)
        timedelta_shape.duration.set(td).execute(ctx)
        result = timedelta_shape.duration.get().execute(ctx)
        assert result == td

    def test_set_multiple_timedeltas(self, timedelta_shape, ctx):
        """Set multiple timedelta slots."""
        duration = timedelta(hours=2)
        timeout = timedelta(seconds=30)

        timedelta_shape.duration.set(duration).execute(ctx)
        timedelta_shape.timeout.set(timeout).execute(ctx)

        assert timedelta_shape.duration.get().execute(ctx) == duration
        assert timedelta_shape.timeout.get().execute(ctx) == timeout


# ============================================================================
# TIMEDELTA COMPONENT ACCESS TESTS
# ============================================================================


class TestTimedeltaComponentAccess:
    """Test accessing timedelta components."""

    def test_days_component(self, timedelta_shape, ctx):
        """Access days component."""
        td = timedelta(days=5, hours=3)
        timedelta_shape.duration.set(td).execute(ctx)
        assert timedelta_shape.duration.days().execute(ctx) == 5

    def test_seconds_component(self, timedelta_shape, ctx):
        """Access seconds component (remainder after days)."""
        td = timedelta(hours=1, seconds=45)
        timedelta_shape.duration.set(td).execute(ctx)
        # 1 hour = 3600 seconds, plus 45
        assert timedelta_shape.duration.seconds().execute(ctx) == 3645

    def test_microseconds_component(self, timedelta_shape, ctx):
        """Access microseconds component."""
        td = timedelta(microseconds=123456)
        timedelta_shape.duration.set(td).execute(ctx)
        assert timedelta_shape.duration.microseconds().execute(ctx) == 123456


# ============================================================================
# TIMEDELTA CONVERSION TESTS
# ============================================================================


class TestTimedeltaConversions:
    """Test timedelta conversions."""

    def test_total_seconds(self, timedelta_shape, ctx):
        """Convert to total seconds."""
        td = timedelta(hours=1, minutes=30)
        timedelta_shape.duration.set(td).execute(ctx)
        result = timedelta_shape.duration.total_seconds().execute(ctx)
        assert result == 5400.0

    def test_total_minutes(self, timedelta_shape, ctx):
        """Convert to total minutes."""
        td = timedelta(hours=2)
        timedelta_shape.duration.set(td).execute(ctx)
        result = timedelta_shape.duration.total_minutes().execute(ctx)
        assert result == 120.0

    def test_total_hours(self, timedelta_shape, ctx):
        """Convert to total hours."""
        td = timedelta(days=1)
        timedelta_shape.duration.set(td).execute(ctx)
        result = timedelta_shape.duration.total_hours().execute(ctx)
        assert result == 24.0

    def test_total_days(self, timedelta_shape, ctx):
        """Convert to total days."""
        td = timedelta(weeks=2)
        timedelta_shape.duration.set(td).execute(ctx)
        result = timedelta_shape.duration.total_days().execute(ctx)
        assert result == 14.0


# ============================================================================
# TIMEDELTATYPE CONSTRUCTOR TESTS
# ============================================================================


class TestTimedeltaTypeConstructors:
    """Test TimedeltaType constructors with execution."""

    def test_from_seconds(self, ctx):
        """Create from seconds."""
        result = TimedeltaType.from_seconds(3600).execute(ctx)
        assert result == timedelta(hours=1)

    def test_from_components(self, ctx):
        """Create from time components."""
        result = TimedeltaType.from_components(days=1, hours=2, minutes=30).execute(ctx)
        assert result == timedelta(days=1, hours=2, minutes=30)

    def test_from_components_all(self, ctx):
        """Create from all time components."""
        result = TimedeltaType.from_components(
            days=1,
            seconds=30,
            microseconds=500,
            milliseconds=100,
            minutes=15,
            hours=2,
            weeks=1,
        ).execute(ctx)
        expected = timedelta(
            days=1,
            seconds=30,
            microseconds=500,
            milliseconds=100,
            minutes=15,
            hours=2,
            weeks=1,
        )
        assert result == expected


# ============================================================================
# TIMEDELTA ARITHMETIC TESTS
# ============================================================================


class TestTimedeltaArithmetic:
    """Test timedelta arithmetic operations."""

    def test_add_timedeltas(self, timedelta_shape, ctx):
        """Add two timedeltas."""
        timedelta_shape.duration.set(timedelta(hours=1)).execute(ctx)
        result = (timedelta_shape.duration.get() + timedelta(hours=2)).execute(ctx)
        assert result == timedelta(hours=3)

    def test_add_timedelta_types(self, timedelta_shape, ctx):
        """Add two timedelta slots."""
        timedelta_shape.duration.set(timedelta(hours=1)).execute(ctx)
        timedelta_shape.timeout.set(timedelta(minutes=30)).execute(ctx)

        result = (timedelta_shape.duration.get() + timedelta_shape.timeout.get()).execute(ctx)
        assert result == timedelta(hours=1, minutes=30)

    def test_subtract_timedeltas(self, timedelta_shape, ctx):
        """Subtract timedeltas."""
        timedelta_shape.duration.set(timedelta(hours=2)).execute(ctx)
        result = (timedelta_shape.duration.get() - timedelta(hours=1)).execute(ctx)
        assert result == timedelta(hours=1)

    def test_multiply_by_int(self, timedelta_shape, ctx):
        """Multiply timedelta by integer."""
        timedelta_shape.duration.set(timedelta(hours=1)).execute(ctx)
        result = (timedelta_shape.duration.get() * 3).execute(ctx)
        assert result == timedelta(hours=3)

    def test_multiply_by_float(self, timedelta_shape, ctx):
        """Multiply timedelta by float."""
        timedelta_shape.duration.set(timedelta(hours=2)).execute(ctx)
        result = (timedelta_shape.duration.get() * 1.5).execute(ctx)
        assert result == timedelta(hours=3)

    def test_divide_by_scalar(self, timedelta_shape, ctx):
        """Divide timedelta by scalar."""
        timedelta_shape.duration.set(timedelta(hours=4)).execute(ctx)
        result = (timedelta_shape.duration.get() / 2).execute(ctx)
        assert result == timedelta(hours=2)

    def test_divide_by_timedelta(self, timedelta_shape, ctx):
        """Divide timedelta by timedelta to get ratio."""
        timedelta_shape.duration.set(timedelta(hours=6)).execute(ctx)
        timedelta_shape.timeout.set(timedelta(hours=2)).execute(ctx)

        result = (timedelta_shape.duration.get() / timedelta_shape.timeout.get()).execute(ctx)
        assert result == 3.0

    def test_floor_divide(self, timedelta_shape, ctx):
        """Floor division."""
        timedelta_shape.duration.set(timedelta(hours=5)).execute(ctx)
        result = (timedelta_shape.duration.get() // 2).execute(ctx)
        assert result == timedelta(hours=2, minutes=30)

    def test_modulo(self, timedelta_shape, ctx):
        """Modulo operation."""
        timedelta_shape.duration.set(timedelta(hours=5)).execute(ctx)
        result = (timedelta_shape.duration.get() % timedelta(hours=2)).execute(ctx)
        assert result == timedelta(hours=1)

    def test_negation(self, timedelta_shape, ctx):
        """Negation."""
        timedelta_shape.duration.set(timedelta(hours=1)).execute(ctx)
        result = (-timedelta_shape.duration.get()).execute(ctx)
        assert result == timedelta(hours=-1)

    def test_absolute(self, timedelta_shape, ctx):
        """Absolute value."""
        timedelta_shape.duration.set(timedelta(hours=-1)).execute(ctx)
        result = abs(timedelta_shape.duration.get()).execute(ctx)
        assert result == timedelta(hours=1)


# ============================================================================
# TIMEDELTA COMPARISON TESTS
# ============================================================================


class TestTimedeltaComparison:
    """Test timedelta comparison operations."""

    def test_less_than(self, timedelta_shape, ctx):
        """Compare timedeltas with less than."""
        timedelta_shape.duration.set(timedelta(hours=1)).execute(ctx)
        timedelta_shape.timeout.set(timedelta(hours=2)).execute(ctx)

        result = (timedelta_shape.duration.get() < timedelta_shape.timeout.get()).execute(ctx)
        assert result is True

    def test_greater_than(self, timedelta_shape, ctx):
        """Compare timedeltas with greater than."""
        timedelta_shape.duration.set(timedelta(hours=3)).execute(ctx)
        timedelta_shape.timeout.set(timedelta(hours=1)).execute(ctx)

        result = (timedelta_shape.duration.get() > timedelta_shape.timeout.get()).execute(ctx)
        assert result is True

    def test_equals(self, timedelta_shape, ctx):
        """Compare timedeltas for equality."""
        timedelta_shape.duration.set(timedelta(hours=1)).execute(ctx)
        timedelta_shape.timeout.set(timedelta(minutes=60)).execute(ctx)

        result = (timedelta_shape.duration.get() == timedelta_shape.timeout.get()).execute(ctx)
        assert result is True
