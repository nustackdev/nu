"""Unit tests for Datetime ref.

Tests for:
- DatetimeRef (constructors, operations, methods)
"""

from datetime import UTC, datetime, timedelta

from every_datetime import DatetimeValue as DatetimeRef
from every_datetime import DateValue as DateRef
from every_datetime import TimedeltaValue as TimedeltaRef
from every_datetime import TimeValue as TimeRef
from everybase.abc import AddOp, FuncCallOp, SubOp
from everybase.abc import FloatValue as FloatRef
from everybase.abc import IntValue as IntRef
from everybase.abc import StrValue as StrRef


# =============================================================================
# DATETIMEREF CONSTRUCTION TESTS
# =============================================================================


class TestDatetimeRefConstruction:
    """DatetimeRef construction tests."""

    def test_now(self):
        """Create DatetimeRef for now."""
        dt = DatetimeRef.now()
        assert isinstance(dt, DatetimeRef)
        assert isinstance(dt._source, FuncCallOp)

    def test_now_with_timezone(self):
        """Create DatetimeRef with timezone."""
        dt = DatetimeRef.now(tz=UTC)
        assert isinstance(dt, DatetimeRef)

    def test_utcnow(self):
        """Create DatetimeRef for UTC now."""
        dt = DatetimeRef.utcnow()
        assert isinstance(dt, DatetimeRef)

    def test_from_timestamp(self):
        """Create from POSIX timestamp."""
        dt = DatetimeRef.from_timestamp(1705312800.0)
        assert isinstance(dt, DatetimeRef)

    def test_from_timestamp_with_tz(self):
        """Create from timestamp with timezone."""
        dt = DatetimeRef.from_timestamp(1705312800.0, tz=UTC)
        assert isinstance(dt, DatetimeRef)

    def test_from_iso(self):
        """Create from ISO format string."""
        dt = DatetimeRef.from_iso("2024-01-15T10:30:00")
        assert isinstance(dt, DatetimeRef)


# =============================================================================
# DATETIMEREF COMPONENT ACCESSOR TESTS
# =============================================================================


class TestDatetimeRefAccessors:
    """DatetimeRef component accessor tests."""

    def test_year_returns_intref(self):
        """year() returns IntRef."""
        dt = DatetimeRef.from_iso("2024-03-15T10:30:00")
        result = dt.year()
        assert isinstance(result, IntRef)

    def test_month_returns_intref(self):
        """month() returns IntRef."""
        dt = DatetimeRef.from_iso("2024-03-15T10:30:00")
        result = dt.month()
        assert isinstance(result, IntRef)

    def test_day_returns_intref(self):
        """day() returns IntRef."""
        dt = DatetimeRef.from_iso("2024-03-15T10:30:00")
        result = dt.day()
        assert isinstance(result, IntRef)

    def test_hour_returns_intref(self):
        """hour() returns IntRef."""
        dt = DatetimeRef.from_iso("2024-03-15T10:30:00")
        result = dt.hour()
        assert isinstance(result, IntRef)

    def test_minute_returns_intref(self):
        """minute() returns IntRef."""
        dt = DatetimeRef.from_iso("2024-03-15T10:30:00")
        result = dt.minute()
        assert isinstance(result, IntRef)

    def test_second_returns_intref(self):
        """second() returns IntRef."""
        dt = DatetimeRef.from_iso("2024-03-15T10:30:00")
        result = dt.second()
        assert isinstance(result, IntRef)

    def test_microsecond_returns_intref(self):
        """microsecond() returns IntRef."""
        dt = DatetimeRef.from_iso("2024-03-15T10:30:00.123456")
        result = dt.microsecond()
        assert isinstance(result, IntRef)

    def test_weekday_returns_intref(self):
        """weekday() returns IntRef."""
        dt = DatetimeRef.from_iso("2024-03-15T10:30:00")
        result = dt.weekday()
        assert isinstance(result, IntRef)

    def test_isoweekday_returns_intref(self):
        """isoweekday() returns IntRef."""
        dt = DatetimeRef.from_iso("2024-03-15T10:30:00")
        result = dt.isoweekday()
        assert isinstance(result, IntRef)


# =============================================================================
# DATETIMEREF CONVERSION TESTS
# =============================================================================


class TestDatetimeRefConversions:
    """DatetimeRef conversion tests."""

    def test_timestamp_returns_floatref(self):
        """timestamp() returns FloatRef."""
        dt = DatetimeRef.from_iso("2024-03-15T10:30:00")
        result = dt.timestamp()
        assert isinstance(result, FloatRef)

    def test_isoformat_returns_strref(self):
        """isoformat() returns StrRef."""
        dt = DatetimeRef.from_iso("2024-03-15T10:30:00")
        result = dt.isoformat()
        assert isinstance(result, StrRef)

    def test_isoformat_with_sep(self):
        """isoformat() with separator returns StrRef."""
        dt = DatetimeRef.from_iso("2024-03-15T10:30:00")
        result = dt.isoformat(sep=" ")
        assert isinstance(result, StrRef)

    def test_date_returns_dateref(self):
        """date() returns DateRef."""
        dt = DatetimeRef.from_iso("2024-03-15T10:30:00")
        result = dt.date()
        assert isinstance(result, DateRef)

    def test_time_returns_timeref(self):
        """time() returns TimeRef."""
        dt = DatetimeRef.from_iso("2024-03-15T10:30:00")
        result = dt.time()
        assert isinstance(result, TimeRef)

    def test_strftime_returns_strref(self):
        """strftime() returns StrRef."""
        dt = DatetimeRef.from_iso("2024-03-15T10:30:00")
        result = dt.strftime("%Y-%m-%d %H:%M:%S")
        assert isinstance(result, StrRef)


# =============================================================================
# DATETIMEREF MANIPULATION TESTS
# =============================================================================


class TestDatetimeRefManipulation:
    """DatetimeRef manipulation tests."""

    def test_replace_year(self):
        """replace() with year returns DatetimeRef."""
        dt = DatetimeRef.from_iso("2024-03-15T10:30:00")
        result = dt.replace(year=2025)
        assert isinstance(result, DatetimeRef)

    def test_replace_hour(self):
        """replace() with hour returns DatetimeRef."""
        dt = DatetimeRef.from_iso("2024-03-15T10:30:00")
        result = dt.replace(hour=15)
        assert isinstance(result, DatetimeRef)

    def test_replace_multiple(self):
        """replace() with multiple components returns DatetimeRef."""
        dt = DatetimeRef.from_iso("2024-03-15T10:30:00")
        result = dt.replace(year=2025, month=12, day=25, hour=18, minute=0)
        assert isinstance(result, DatetimeRef)


# =============================================================================
# DATETIMEREF ARITHMETIC TESTS
# =============================================================================


class TestDatetimeRefArithmetic:
    """DatetimeRef arithmetic tests."""

    def test_add_timedelta(self):
        """Adding timedelta returns DatetimeRef."""
        dt = DatetimeRef.from_iso("2024-03-15T10:30:00")
        result = dt + timedelta(hours=5)
        assert isinstance(result, DatetimeRef)
        assert isinstance(result._source, AddOp)

    def test_sub_timedelta(self):
        """Subtracting timedelta returns DatetimeRef."""
        dt = DatetimeRef.from_iso("2024-03-15T10:30:00")
        result = dt - timedelta(days=1)
        assert isinstance(result, DatetimeRef)
        assert isinstance(result._source, SubOp)

    def test_sub_datetime(self):
        """Subtracting datetime returns TimedeltaRef."""
        dt = DatetimeRef.from_iso("2024-03-15T10:30:00")
        result = dt - datetime(2024, 3, 14, 10, 30, 0)
        assert isinstance(result, TimedeltaRef)

    def test_sub_datetimeref(self):
        """Subtracting DatetimeRef returns TimedeltaRef."""
        dt1 = DatetimeRef.from_iso("2024-03-15T10:30:00")
        dt2 = DatetimeRef.from_iso("2024-03-14T10:30:00")
        result = dt1 - dt2
        assert isinstance(result, TimedeltaRef)
