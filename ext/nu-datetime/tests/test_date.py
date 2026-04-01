"""Unit tests for Date ref.

Tests for:
- DateRef (constructors, operations, methods)
"""

from datetime import date, timedelta

from nu_datetime import DateValue as DateRef
from nu_datetime import TimedeltaValue as TimedeltaRef
from nu import AddOp, FuncCallOp, MethodCallOp, SubOp
from nu import IntValue as IntRef
from nu import StrValue as StrRef


# =============================================================================
# DATEREF CONSTRUCTION TESTS
# =============================================================================


class TestDateRefConstruction:
    """DateRef construction tests."""

    def test_today(self):
        """Create DateRef for today."""
        dt = DateRef.today()
        assert isinstance(dt, DateRef)
        assert isinstance(dt.source, FuncCallOp)

    def test_from_iso(self):
        """Create from ISO format string."""
        dt = DateRef.from_iso("2024-01-15")
        assert isinstance(dt, DateRef)
        assert isinstance(dt.source, FuncCallOp)

    def test_from_ordinal(self):
        """Create from Gregorian ordinal."""
        dt = DateRef.from_ordinal(738886)
        assert isinstance(dt, DateRef)

    def test_from_timestamp(self):
        """Create from POSIX timestamp."""
        dt = DateRef.from_timestamp(1705312800.0)
        assert isinstance(dt, DateRef)


# =============================================================================
# DATEREF COMPONENT ACCESSOR TESTS
# =============================================================================


class TestDateRefAccessors:
    """DateRef component accessor tests."""

    def test_year_returns_intref(self):
        """year() returns IntRef."""
        dt = DateRef.from_iso("2024-03-15")
        result = dt.year()
        assert isinstance(result, IntRef)

    def test_month_returns_intref(self):
        """month() returns IntRef."""
        dt = DateRef.from_iso("2024-03-15")
        result = dt.month()
        assert isinstance(result, IntRef)

    def test_day_returns_intref(self):
        """day() returns IntRef."""
        dt = DateRef.from_iso("2024-03-15")
        result = dt.day()
        assert isinstance(result, IntRef)

    def test_weekday_returns_intref(self):
        """weekday() returns IntRef."""
        dt = DateRef.from_iso("2024-03-15")
        result = dt.weekday()
        assert isinstance(result, IntRef)
        assert isinstance(result.source, MethodCallOp)

    def test_isoweekday_returns_intref(self):
        """isoweekday() returns IntRef."""
        dt = DateRef.from_iso("2024-03-15")
        result = dt.isoweekday()
        assert isinstance(result, IntRef)

    def test_toordinal_returns_intref(self):
        """toordinal() returns IntRef."""
        dt = DateRef.from_iso("2024-03-15")
        result = dt.toordinal()
        assert isinstance(result, IntRef)


# =============================================================================
# DATEREF CONVERSION TESTS
# =============================================================================


class TestDateRefConversions:
    """DateRef conversion tests."""

    def test_isoformat_returns_strref(self):
        """isoformat() returns StrRef."""
        dt = DateRef.from_iso("2024-03-15")
        result = dt.isoformat()
        assert isinstance(result, StrRef)

    def test_strftime_returns_strref(self):
        """strftime() returns StrRef."""
        dt = DateRef.from_iso("2024-03-15")
        result = dt.strftime("%Y/%m/%d")
        assert isinstance(result, StrRef)

    def test_ctime_returns_strref(self):
        """ctime() returns StrRef."""
        dt = DateRef.from_iso("2024-03-15")
        result = dt.ctime()
        assert isinstance(result, StrRef)


# =============================================================================
# DATEREF MANIPULATION TESTS
# =============================================================================


class TestDateRefManipulation:
    """DateRef manipulation tests."""

    def test_replace_year(self):
        """replace() with year returns DateRef."""
        dt = DateRef.from_iso("2024-03-15")
        result = dt.replace(year=2025)
        assert isinstance(result, DateRef)

    def test_replace_month(self):
        """replace() with month returns DateRef."""
        dt = DateRef.from_iso("2024-03-15")
        result = dt.replace(month=6)
        assert isinstance(result, DateRef)

    def test_replace_day(self):
        """replace() with day returns DateRef."""
        dt = DateRef.from_iso("2024-03-15")
        result = dt.replace(day=1)
        assert isinstance(result, DateRef)

    def test_replace_multiple(self):
        """replace() with multiple components returns DateRef."""
        dt = DateRef.from_iso("2024-03-15")
        result = dt.replace(year=2025, month=12, day=25)
        assert isinstance(result, DateRef)


# =============================================================================
# DATEREF ARITHMETIC TESTS
# =============================================================================


class TestDateRefArithmetic:
    """DateRef arithmetic tests."""

    def test_add_timedelta(self):
        """Adding timedelta returns DateRef."""
        dt = DateRef.from_iso("2024-03-15")
        result = dt + timedelta(days=10)
        assert isinstance(result, DateRef)
        assert isinstance(result.source, AddOp)

    def test_sub_timedelta(self):
        """Subtracting timedelta returns DateRef."""
        dt = DateRef.from_iso("2024-03-15")
        result = dt - timedelta(days=5)
        assert isinstance(result, DateRef)
        assert isinstance(result.source, SubOp)

    def test_sub_date(self):
        """Subtracting date returns TimedeltaRef."""
        dt = DateRef.from_iso("2024-03-15")
        result = dt - date(2024, 3, 10)
        assert isinstance(result, TimedeltaRef)

    def test_sub_dateref(self):
        """Subtracting DateRef returns TimedeltaRef."""
        dt1 = DateRef.from_iso("2024-03-15")
        dt2 = DateRef.from_iso("2024-03-10")
        result = dt1 - dt2
        assert isinstance(result, TimedeltaRef)
