"""Functional tests for Datetime type.

Tests DatetimeType and DatetimeSlot execution with real storage context.
"""

from datetime import UTC, datetime, timedelta

from everybase.type import DatetimeType


# ============================================================================
# DATETIME SET AND GET TESTS
# ============================================================================


class TestDatetimeSetAndGet:
    """Test setting and getting datetime values through storage."""

    def test_set_and_get_datetime(self, datetime_shape, ctx):
        """Set and retrieve a datetime value."""
        dt = datetime(2024, 6, 15, 10, 30, 45)
        datetime_shape.created_at.set(dt).execute(ctx)
        result = datetime_shape.created_at.get().execute(ctx)
        # Compare without microseconds for precision
        assert result.replace(microsecond=0) == dt.replace(microsecond=0)

    def test_set_datetime_with_timezone(self, datetime_shape, ctx):
        """Set datetime with UTC timezone."""
        dt = datetime(2024, 6, 15, 10, 30, 45, tzinfo=UTC)
        datetime_shape.created_at.set(dt).execute(ctx)
        result = datetime_shape.created_at.get().execute(ctx)
        assert result.tzinfo == UTC

    def test_set_multiple_datetimes(self, datetime_shape, ctx):
        """Set multiple datetime slots."""
        created = datetime(2024, 1, 1, 8, 0, 0)
        updated = datetime(2024, 6, 15, 14, 30, 0)

        datetime_shape.created_at.set(created).execute(ctx)
        datetime_shape.updated_at.set(updated).execute(ctx)

        assert datetime_shape.created_at.get().execute(ctx).date() == created.date()
        assert datetime_shape.updated_at.get().execute(ctx).date() == updated.date()


# ============================================================================
# DATETIME COMPONENT ACCESS TESTS
# ============================================================================


class TestDatetimeComponentAccess:
    """Test accessing datetime components."""

    def test_year_component(self, datetime_shape, ctx):
        """Access year component."""
        dt = datetime(2024, 6, 15, 10, 30, 45)
        datetime_shape.created_at.set(dt).execute(ctx)
        assert datetime_shape.created_at.get().year().execute(ctx) == 2024

    def test_month_component(self, datetime_shape, ctx):
        """Access month component."""
        dt = datetime(2024, 6, 15, 10, 30, 45)
        datetime_shape.created_at.set(dt).execute(ctx)
        assert datetime_shape.created_at.get().month().execute(ctx) == 6

    def test_day_component(self, datetime_shape, ctx):
        """Access day component."""
        dt = datetime(2024, 6, 15, 10, 30, 45)
        datetime_shape.created_at.set(dt).execute(ctx)
        assert datetime_shape.created_at.get().day().execute(ctx) == 15

    def test_hour_component(self, datetime_shape, ctx):
        """Access hour component."""
        dt = datetime(2024, 6, 15, 10, 30, 45)
        datetime_shape.created_at.set(dt).execute(ctx)
        assert datetime_shape.created_at.get().hour().execute(ctx) == 10

    def test_minute_component(self, datetime_shape, ctx):
        """Access minute component."""
        dt = datetime(2024, 6, 15, 10, 30, 45)
        datetime_shape.created_at.set(dt).execute(ctx)
        assert datetime_shape.created_at.get().minute().execute(ctx) == 30

    def test_second_component(self, datetime_shape, ctx):
        """Access second component."""
        dt = datetime(2024, 6, 15, 10, 30, 45)
        datetime_shape.created_at.set(dt).execute(ctx)
        assert datetime_shape.created_at.get().second().execute(ctx) == 45

    def test_weekday(self, datetime_shape, ctx):
        """Access weekday (Monday=0, Sunday=6)."""
        # June 15, 2024 is a Saturday = 5
        dt = datetime(2024, 6, 15, 10, 30, 45)
        datetime_shape.created_at.set(dt).execute(ctx)
        assert datetime_shape.created_at.get().weekday().execute(ctx) == 5


# ============================================================================
# DATETIME CONVERSION TESTS
# ============================================================================


class TestDatetimeConversions:
    """Test datetime conversions."""

    def test_timestamp(self, datetime_shape, ctx):
        """Convert to POSIX timestamp."""
        dt = datetime(2024, 6, 15, 10, 30, 45, tzinfo=UTC)
        datetime_shape.created_at.set(dt).execute(ctx)
        result = datetime_shape.created_at.get().timestamp().execute(ctx)
        assert abs(result - dt.timestamp()) < 1.0

    def test_isoformat(self, datetime_shape, ctx):
        """Convert to ISO format string."""
        dt = datetime(2024, 6, 15, 10, 30, 45)
        datetime_shape.created_at.set(dt).execute(ctx)
        result = datetime_shape.created_at.get().isoformat().execute(ctx)
        assert "2024-06-15" in result
        assert "10:30:45" in result

    def test_strftime(self, datetime_shape, ctx):
        """Format datetime with custom format."""
        dt = datetime(2024, 6, 15, 10, 30, 45)
        datetime_shape.created_at.set(dt).execute(ctx)
        result = datetime_shape.created_at.get().strftime("%Y-%m-%d %H:%M").execute(ctx)
        assert result == "2024-06-15 10:30"

    def test_date_extraction(self, datetime_shape, ctx):
        """Extract date component."""
        from datetime import date

        dt = datetime(2024, 6, 15, 10, 30, 45)
        datetime_shape.created_at.set(dt).execute(ctx)
        result = datetime_shape.created_at.get().date().execute(ctx)
        assert result == date(2024, 6, 15)

    def test_time_extraction(self, datetime_shape, ctx):
        """Extract time component."""

        dt = datetime(2024, 6, 15, 10, 30, 45)
        datetime_shape.created_at.set(dt).execute(ctx)
        result = datetime_shape.created_at.get().time().execute(ctx)
        assert result.hour == 10
        assert result.minute == 30


# ============================================================================
# DATETIMETYPE CONSTRUCTOR TESTS
# ============================================================================


class TestDatetimeTypeConstructors:
    """Test DatetimeType constructors with execution."""

    def test_now(self, ctx):
        """Create and execute DatetimeType.now()."""
        before = datetime.now()
        result = DatetimeType.now().execute(ctx)
        after = datetime.now()
        assert before <= result <= after

    def test_utcnow(self, ctx):
        """Create UTC datetime."""
        result = DatetimeType.utcnow().execute(ctx)
        assert result.tzinfo == UTC

    def test_from_iso(self, ctx):
        """Create from ISO string."""
        result = DatetimeType.from_iso("2024-06-15T10:30:45").execute(ctx)
        assert result.year == 2024
        assert result.month == 6
        assert result.hour == 10

    def test_from_timestamp(self, ctx):
        """Create from POSIX timestamp."""
        ts = 1718444445.0  # June 15, 2024 approximate
        result = DatetimeType.from_timestamp(ts).execute(ctx)
        assert result.year == 2024


# ============================================================================
# DATETIME ARITHMETIC TESTS
# ============================================================================


class TestDatetimeArithmetic:
    """Test datetime arithmetic operations."""

    def test_add_timedelta(self, datetime_shape, ctx):
        """Add timedelta to datetime."""
        dt = datetime(2024, 1, 1, 10, 0, 0)
        datetime_shape.created_at.set(dt).execute(ctx)

        result = (datetime_shape.created_at.get() + timedelta(hours=5)).execute(ctx)
        assert result.hour == 15

    def test_subtract_timedelta(self, datetime_shape, ctx):
        """Subtract timedelta from datetime."""
        dt = datetime(2024, 1, 15, 10, 0, 0)
        datetime_shape.created_at.set(dt).execute(ctx)

        result = (datetime_shape.created_at.get() - timedelta(days=5)).execute(ctx)
        assert result.day == 10

    def test_subtract_datetimes(self, datetime_shape, ctx):
        """Subtract two datetimes to get timedelta."""
        datetime_shape.created_at.set(datetime(2024, 1, 1, 10, 0, 0)).execute(ctx)
        datetime_shape.updated_at.set(datetime(2024, 1, 1, 15, 0, 0)).execute(ctx)

        result = (datetime_shape.updated_at.get() - datetime_shape.created_at.get()).execute(ctx)
        assert result == timedelta(hours=5)


# ============================================================================
# DATETIME MANIPULATION TESTS
# ============================================================================


class TestDatetimeManipulation:
    """Test datetime manipulation operations."""

    def test_replace_year(self, datetime_shape, ctx):
        """Replace year component."""
        dt = datetime(2024, 6, 15, 10, 30, 45)
        datetime_shape.created_at.set(dt).execute(ctx)

        result = datetime_shape.created_at.get().replace(year=2025).execute(ctx)
        assert result.year == 2025

    def test_replace_hour(self, datetime_shape, ctx):
        """Replace hour component."""
        dt = datetime(2024, 6, 15, 10, 30, 45)
        datetime_shape.created_at.set(dt).execute(ctx)

        result = datetime_shape.created_at.get().replace(hour=18).execute(ctx)
        assert result.hour == 18

    def test_replace_multiple(self, datetime_shape, ctx):
        """Replace multiple components."""
        dt = datetime(2024, 6, 15, 10, 30, 45)
        datetime_shape.created_at.set(dt).execute(ctx)

        result = datetime_shape.created_at.get().replace(year=2025, month=12, hour=18).execute(ctx)
        assert result.year == 2025
        assert result.month == 12
        assert result.hour == 18
