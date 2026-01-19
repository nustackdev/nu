"""Functional tests for Date type.

Tests DateType and DateSlot execution with real storage context.
"""

from datetime import date, timedelta

from everybase.type import DateType


# ============================================================================
# DATE SET AND GET TESTS
# ============================================================================


class TestDateSetAndGet:
    """Test setting and getting date values through storage."""

    def test_set_and_get_date(self, date_shape, ctx):
        """Set and retrieve a date value."""
        d = date(2024, 6, 15)
        date_shape.event_date.set(d).execute(ctx)
        result = date_shape.event_date.get().execute(ctx)
        assert result == d

    def test_set_date_from_iso_string(self, date_shape, ctx):
        """Set date from ISO format string via DateType."""
        date_shape.event_date.set(DateType.from_iso("2024-03-15")).execute(ctx)
        result = date_shape.event_date.get().execute(ctx)
        assert result == date(2024, 3, 15)

    def test_set_multiple_dates(self, date_shape, ctx):
        """Set multiple date slots."""
        start = date(2024, 1, 1)
        end = date(2024, 12, 31)

        date_shape.start_date.set(start).execute(ctx)
        date_shape.end_date.set(end).execute(ctx)

        assert date_shape.start_date.get().execute(ctx) == start
        assert date_shape.end_date.get().execute(ctx) == end


# ============================================================================
# DATE COMPONENT ACCESS TESTS
# ============================================================================


class TestDateComponentAccess:
    """Test accessing date components."""

    def test_year_component(self, date_shape, ctx):
        """Access year component."""
        d = date(2024, 6, 15)
        date_shape.event_date.set(d).execute(ctx)
        assert date_shape.event_date.year().execute(ctx) == 2024

    def test_month_component(self, date_shape, ctx):
        """Access month component."""
        d = date(2024, 6, 15)
        date_shape.event_date.set(d).execute(ctx)
        assert date_shape.event_date.month().execute(ctx) == 6

    def test_day_component(self, date_shape, ctx):
        """Access day component."""
        d = date(2024, 6, 15)
        date_shape.event_date.set(d).execute(ctx)
        assert date_shape.event_date.day().execute(ctx) == 15

    def test_weekday(self, date_shape, ctx):
        """Access weekday (Monday=0, Sunday=6)."""
        # June 15, 2024 is a Saturday = 5
        d = date(2024, 6, 15)
        date_shape.event_date.set(d).execute(ctx)
        assert date_shape.event_date.weekday().execute(ctx) == 5

    def test_isoweekday(self, date_shape, ctx):
        """Access ISO weekday (Monday=1, Sunday=7)."""
        # June 15, 2024 is a Saturday = 6
        d = date(2024, 6, 15)
        date_shape.event_date.set(d).execute(ctx)
        assert date_shape.event_date.isoweekday().execute(ctx) == 6

    def test_toordinal(self, date_shape, ctx):
        """Access Gregorian ordinal."""
        d = date(2024, 1, 1)
        date_shape.event_date.set(d).execute(ctx)
        # Day 1 of year 2024
        result = date_shape.event_date.toordinal().execute(ctx)
        assert result == d.toordinal()


# ============================================================================
# DATE CONVERSION TESTS
# ============================================================================


class TestDateConversions:
    """Test date conversions."""

    def test_isoformat(self, date_shape, ctx):
        """Convert to ISO format string."""
        d = date(2024, 6, 15)
        date_shape.event_date.set(d).execute(ctx)
        result = date_shape.event_date.isoformat().execute(ctx)
        assert result == "2024-06-15"

    def test_strftime(self, date_shape, ctx):
        """Format date with custom format."""
        d = date(2024, 6, 15)
        date_shape.event_date.set(d).execute(ctx)
        result = date_shape.event_date.strftime("%Y/%m/%d").execute(ctx)
        assert result == "2024/06/15"


# ============================================================================
# DATETYPE CONSTRUCTOR TESTS
# ============================================================================


class TestDateTypeConstructors:
    """Test DateType constructors with execution."""

    def test_today(self, ctx):
        """Create and execute DateType.today()."""
        result = DateType.today().execute(ctx)
        assert result == date.today()

    def test_from_iso(self, ctx):
        """Create from ISO string."""
        result = DateType.from_iso("2024-06-15").execute(ctx)
        assert result == date(2024, 6, 15)

    def test_from_ordinal(self, ctx):
        """Create from Gregorian ordinal."""
        ordinal = date(2024, 1, 1).toordinal()
        result = DateType.from_ordinal(ordinal).execute(ctx)
        assert result == date(2024, 1, 1)

    def test_from_timestamp(self, ctx):
        """Create from POSIX timestamp."""
        # Timestamp for 2024-01-15 00:00:00 UTC
        ts = 1705276800.0
        result = DateType.from_timestamp(ts).execute(ctx)
        assert result.year == 2024
        assert result.month == 1


# ============================================================================
# DATE ARITHMETIC TESTS
# ============================================================================


class TestDateArithmetic:
    """Test date arithmetic operations."""

    def test_add_timedelta(self, date_shape, ctx):
        """Add timedelta to date."""
        d = date(2024, 1, 1)
        date_shape.event_date.set(d).execute(ctx)

        result = (date_shape.event_date.get() + timedelta(days=10)).execute(ctx)
        assert result == date(2024, 1, 11)

    def test_subtract_timedelta(self, date_shape, ctx):
        """Subtract timedelta from date."""
        d = date(2024, 1, 15)
        date_shape.event_date.set(d).execute(ctx)

        result = (date_shape.event_date.get() - timedelta(days=5)).execute(ctx)
        assert result == date(2024, 1, 10)

    def test_subtract_dates(self, date_shape, ctx):
        """Subtract two dates to get timedelta."""
        date_shape.start_date.set(date(2024, 1, 1)).execute(ctx)
        date_shape.end_date.set(date(2024, 1, 11)).execute(ctx)

        result = (date_shape.end_date.get() - date_shape.start_date.get()).execute(ctx)
        assert result == timedelta(days=10)


# ============================================================================
# DATE MANIPULATION TESTS
# ============================================================================


class TestDateManipulation:
    """Test date manipulation operations."""

    def test_replace_year(self, date_shape, ctx):
        """Replace year component."""
        d = date(2024, 6, 15)
        date_shape.event_date.set(d).execute(ctx)

        result = date_shape.event_date.get().replace(year=2025).execute(ctx)
        assert result == date(2025, 6, 15)

    def test_replace_month(self, date_shape, ctx):
        """Replace month component."""
        d = date(2024, 6, 15)
        date_shape.event_date.set(d).execute(ctx)

        result = date_shape.event_date.get().replace(month=12).execute(ctx)
        assert result == date(2024, 12, 15)

    def test_replace_day(self, date_shape, ctx):
        """Replace day component."""
        d = date(2024, 6, 15)
        date_shape.event_date.set(d).execute(ctx)

        result = date_shape.event_date.get().replace(day=1).execute(ctx)
        assert result == date(2024, 6, 1)

    def test_replace_multiple(self, date_shape, ctx):
        """Replace multiple components."""
        d = date(2024, 6, 15)
        date_shape.event_date.set(d).execute(ctx)

        result = date_shape.event_date.get().replace(year=2025, month=12, day=25).execute(ctx)
        assert result == date(2025, 12, 25)
