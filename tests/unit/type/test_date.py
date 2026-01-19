"""Unit tests for Date type.

Tests for:
- DateType (constructors, operations, methods)
"""

from datetime import date, timedelta

from everybase.type.date import DateType
from everyterm.ops import AddOp, FuncCallOp, MethodCallOp, SubOp
from everyterm.types import IntType, StrType


# =============================================================================
# DATETYPE CONSTRUCTION TESTS
# =============================================================================


class TestDateTypeConstruction:
    """DateType construction tests."""

    def test_today(self):
        """Create DateType for today."""
        dt = DateType.today()
        assert isinstance(dt, DateType)
        assert isinstance(dt.source, FuncCallOp)

    def test_from_iso(self):
        """Create from ISO format string."""
        dt = DateType.from_iso("2024-01-15")
        assert isinstance(dt, DateType)
        assert isinstance(dt.source, FuncCallOp)

    def test_from_ordinal(self):
        """Create from Gregorian ordinal."""
        dt = DateType.from_ordinal(738886)
        assert isinstance(dt, DateType)

    def test_from_timestamp(self):
        """Create from POSIX timestamp."""
        dt = DateType.from_timestamp(1705312800.0)
        assert isinstance(dt, DateType)


# =============================================================================
# DATETYPE COMPONENT ACCESSOR TESTS
# =============================================================================


class TestDateTypeAccessors:
    """DateType component accessor tests."""

    def test_year_returns_inttype(self):
        """year() returns IntType."""
        dt = DateType.from_iso("2024-03-15")
        result = dt.year()
        assert isinstance(result, IntType)

    def test_month_returns_inttype(self):
        """month() returns IntType."""
        dt = DateType.from_iso("2024-03-15")
        result = dt.month()
        assert isinstance(result, IntType)

    def test_day_returns_inttype(self):
        """day() returns IntType."""
        dt = DateType.from_iso("2024-03-15")
        result = dt.day()
        assert isinstance(result, IntType)

    def test_weekday_returns_inttype(self):
        """weekday() returns IntType."""
        dt = DateType.from_iso("2024-03-15")
        result = dt.weekday()
        assert isinstance(result, IntType)
        assert isinstance(result.source, MethodCallOp)

    def test_isoweekday_returns_inttype(self):
        """isoweekday() returns IntType."""
        dt = DateType.from_iso("2024-03-15")
        result = dt.isoweekday()
        assert isinstance(result, IntType)

    def test_toordinal_returns_inttype(self):
        """toordinal() returns IntType."""
        dt = DateType.from_iso("2024-03-15")
        result = dt.toordinal()
        assert isinstance(result, IntType)


# =============================================================================
# DATETYPE CONVERSION TESTS
# =============================================================================


class TestDateTypeConversions:
    """DateType conversion tests."""

    def test_isoformat_returns_strtype(self):
        """isoformat() returns StrType."""
        dt = DateType.from_iso("2024-03-15")
        result = dt.isoformat()
        assert isinstance(result, StrType)

    def test_strftime_returns_strtype(self):
        """strftime() returns StrType."""
        dt = DateType.from_iso("2024-03-15")
        result = dt.strftime("%Y/%m/%d")
        assert isinstance(result, StrType)

    def test_ctime_returns_strtype(self):
        """ctime() returns StrType."""
        dt = DateType.from_iso("2024-03-15")
        result = dt.ctime()
        assert isinstance(result, StrType)


# =============================================================================
# DATETYPE MANIPULATION TESTS
# =============================================================================


class TestDateTypeManipulation:
    """DateType manipulation tests."""

    def test_replace_year(self):
        """replace() with year returns DateType."""
        dt = DateType.from_iso("2024-03-15")
        result = dt.replace(year=2025)
        assert isinstance(result, DateType)

    def test_replace_month(self):
        """replace() with month returns DateType."""
        dt = DateType.from_iso("2024-03-15")
        result = dt.replace(month=6)
        assert isinstance(result, DateType)

    def test_replace_day(self):
        """replace() with day returns DateType."""
        dt = DateType.from_iso("2024-03-15")
        result = dt.replace(day=1)
        assert isinstance(result, DateType)

    def test_replace_multiple(self):
        """replace() with multiple components returns DateType."""
        dt = DateType.from_iso("2024-03-15")
        result = dt.replace(year=2025, month=12, day=25)
        assert isinstance(result, DateType)


# =============================================================================
# DATETYPE ARITHMETIC TESTS
# =============================================================================


class TestDateTypeArithmetic:
    """DateType arithmetic tests."""

    def test_add_timedelta(self):
        """Adding timedelta returns DateType."""
        dt = DateType.from_iso("2024-03-15")
        result = dt + timedelta(days=10)
        assert isinstance(result, DateType)
        assert isinstance(result.source, AddOp)

    def test_sub_timedelta(self):
        """Subtracting timedelta returns DateType."""
        dt = DateType.from_iso("2024-03-15")
        result = dt - timedelta(days=5)
        assert isinstance(result, DateType)
        assert isinstance(result.source, SubOp)

    def test_sub_date(self):
        """Subtracting date returns TimedeltaType."""
        from everybase.type.timedelta import TimedeltaType

        dt = DateType.from_iso("2024-03-15")
        result = dt - date(2024, 3, 10)
        assert isinstance(result, TimedeltaType)

    def test_sub_datetype(self):
        """Subtracting DateType returns TimedeltaType."""
        from everybase.type.timedelta import TimedeltaType

        dt1 = DateType.from_iso("2024-03-15")
        dt2 = DateType.from_iso("2024-03-10")
        result = dt1 - dt2
        assert isinstance(result, TimedeltaType)
