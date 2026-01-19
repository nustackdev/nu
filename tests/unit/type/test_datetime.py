"""Unit tests for Datetime type.

Tests for:
- DatetimeType (constructors, operations, methods)
"""

from datetime import UTC, datetime, timedelta

from everybase.type.datetime import DatetimeType
from everyterm.ops import AddOp, FuncCallOp, SubOp
from everyterm.types import FloatType, IntType, StrType


# =============================================================================
# DATETIMETYPE CONSTRUCTION TESTS
# =============================================================================


class TestDatetimeTypeConstruction:
    """DatetimeType construction tests."""

    def test_now(self):
        """Create DatetimeType for now."""
        dt = DatetimeType.now()
        assert isinstance(dt, DatetimeType)
        assert isinstance(dt.source, FuncCallOp)

    def test_now_with_timezone(self):
        """Create DatetimeType with timezone."""
        dt = DatetimeType.now(tz=UTC)
        assert isinstance(dt, DatetimeType)

    def test_utcnow(self):
        """Create DatetimeType for UTC now."""
        dt = DatetimeType.utcnow()
        assert isinstance(dt, DatetimeType)

    def test_from_timestamp(self):
        """Create from POSIX timestamp."""
        dt = DatetimeType.from_timestamp(1705312800.0)
        assert isinstance(dt, DatetimeType)

    def test_from_timestamp_with_tz(self):
        """Create from timestamp with timezone."""
        dt = DatetimeType.from_timestamp(1705312800.0, tz=UTC)
        assert isinstance(dt, DatetimeType)

    def test_from_iso(self):
        """Create from ISO format string."""
        dt = DatetimeType.from_iso("2024-01-15T10:30:00")
        assert isinstance(dt, DatetimeType)


# =============================================================================
# DATETIMETYPE COMPONENT ACCESSOR TESTS
# =============================================================================


class TestDatetimeTypeAccessors:
    """DatetimeType component accessor tests."""

    def test_year_returns_inttype(self):
        """year() returns IntType."""
        dt = DatetimeType.from_iso("2024-03-15T10:30:00")
        result = dt.year()
        assert isinstance(result, IntType)

    def test_month_returns_inttype(self):
        """month() returns IntType."""
        dt = DatetimeType.from_iso("2024-03-15T10:30:00")
        result = dt.month()
        assert isinstance(result, IntType)

    def test_day_returns_inttype(self):
        """day() returns IntType."""
        dt = DatetimeType.from_iso("2024-03-15T10:30:00")
        result = dt.day()
        assert isinstance(result, IntType)

    def test_hour_returns_inttype(self):
        """hour() returns IntType."""
        dt = DatetimeType.from_iso("2024-03-15T10:30:00")
        result = dt.hour()
        assert isinstance(result, IntType)

    def test_minute_returns_inttype(self):
        """minute() returns IntType."""
        dt = DatetimeType.from_iso("2024-03-15T10:30:00")
        result = dt.minute()
        assert isinstance(result, IntType)

    def test_second_returns_inttype(self):
        """second() returns IntType."""
        dt = DatetimeType.from_iso("2024-03-15T10:30:00")
        result = dt.second()
        assert isinstance(result, IntType)

    def test_microsecond_returns_inttype(self):
        """microsecond() returns IntType."""
        dt = DatetimeType.from_iso("2024-03-15T10:30:00.123456")
        result = dt.microsecond()
        assert isinstance(result, IntType)

    def test_weekday_returns_inttype(self):
        """weekday() returns IntType."""
        dt = DatetimeType.from_iso("2024-03-15T10:30:00")
        result = dt.weekday()
        assert isinstance(result, IntType)

    def test_isoweekday_returns_inttype(self):
        """isoweekday() returns IntType."""
        dt = DatetimeType.from_iso("2024-03-15T10:30:00")
        result = dt.isoweekday()
        assert isinstance(result, IntType)


# =============================================================================
# DATETIMETYPE CONVERSION TESTS
# =============================================================================


class TestDatetimeTypeConversions:
    """DatetimeType conversion tests."""

    def test_timestamp_returns_floattype(self):
        """timestamp() returns FloatType."""
        dt = DatetimeType.from_iso("2024-03-15T10:30:00")
        result = dt.timestamp()
        assert isinstance(result, FloatType)

    def test_isoformat_returns_strtype(self):
        """isoformat() returns StrType."""
        dt = DatetimeType.from_iso("2024-03-15T10:30:00")
        result = dt.isoformat()
        assert isinstance(result, StrType)

    def test_isoformat_with_sep(self):
        """isoformat() with separator returns StrType."""
        dt = DatetimeType.from_iso("2024-03-15T10:30:00")
        result = dt.isoformat(sep=" ")
        assert isinstance(result, StrType)

    def test_date_returns_datetype(self):
        """date() returns DateType."""
        from everybase.type.date import DateType

        dt = DatetimeType.from_iso("2024-03-15T10:30:00")
        result = dt.date()
        assert isinstance(result, DateType)

    def test_time_returns_timetype(self):
        """time() returns TimeType."""
        from everybase.type.time import TimeType

        dt = DatetimeType.from_iso("2024-03-15T10:30:00")
        result = dt.time()
        assert isinstance(result, TimeType)

    def test_strftime_returns_strtype(self):
        """strftime() returns StrType."""
        dt = DatetimeType.from_iso("2024-03-15T10:30:00")
        result = dt.strftime("%Y-%m-%d %H:%M:%S")
        assert isinstance(result, StrType)


# =============================================================================
# DATETIMETYPE MANIPULATION TESTS
# =============================================================================


class TestDatetimeTypeManipulation:
    """DatetimeType manipulation tests."""

    def test_replace_year(self):
        """replace() with year returns DatetimeType."""
        dt = DatetimeType.from_iso("2024-03-15T10:30:00")
        result = dt.replace(year=2025)
        assert isinstance(result, DatetimeType)

    def test_replace_hour(self):
        """replace() with hour returns DatetimeType."""
        dt = DatetimeType.from_iso("2024-03-15T10:30:00")
        result = dt.replace(hour=15)
        assert isinstance(result, DatetimeType)

    def test_replace_multiple(self):
        """replace() with multiple components returns DatetimeType."""
        dt = DatetimeType.from_iso("2024-03-15T10:30:00")
        result = dt.replace(year=2025, month=12, day=25, hour=18, minute=0)
        assert isinstance(result, DatetimeType)


# =============================================================================
# DATETIMETYPE ARITHMETIC TESTS
# =============================================================================


class TestDatetimeTypeArithmetic:
    """DatetimeType arithmetic tests."""

    def test_add_timedelta(self):
        """Adding timedelta returns DatetimeType."""
        dt = DatetimeType.from_iso("2024-03-15T10:30:00")
        result = dt + timedelta(hours=5)
        assert isinstance(result, DatetimeType)
        assert isinstance(result.source, AddOp)

    def test_sub_timedelta(self):
        """Subtracting timedelta returns DatetimeType."""
        dt = DatetimeType.from_iso("2024-03-15T10:30:00")
        result = dt - timedelta(days=1)
        assert isinstance(result, DatetimeType)
        assert isinstance(result.source, SubOp)

    def test_sub_datetime(self):
        """Subtracting datetime returns TimedeltaType."""
        from everybase.type.timedelta import TimedeltaType

        dt = DatetimeType.from_iso("2024-03-15T10:30:00")
        result = dt - datetime(2024, 3, 14, 10, 30, 0)
        assert isinstance(result, TimedeltaType)

    def test_sub_datetimetype(self):
        """Subtracting DatetimeType returns TimedeltaType."""
        from everybase.type.timedelta import TimedeltaType

        dt1 = DatetimeType.from_iso("2024-03-15T10:30:00")
        dt2 = DatetimeType.from_iso("2024-03-14T10:30:00")
        result = dt1 - dt2
        assert isinstance(result, TimedeltaType)
