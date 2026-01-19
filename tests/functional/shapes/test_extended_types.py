"""Functional tests for extended Shape types.

Tests for: datetime, timedelta, date, time, Decimal, Fraction, UUID, Path, complex.
"""

from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal
from fractions import Fraction
from pathlib import Path
from uuid import UUID, uuid4

import pytest

from everybase.type import (
    ComplexSlot,
    DateSlot,
    DatetimeSlot,
    DecimalSlot,
    FractionSlot,
    PathSlot,
    TimedeltaSlot,
    TimeSlot,
    UUIDSlot,
)
from everyterm import Shape


# ============================================================================
# SHAPE FIXTURES
# ============================================================================


@pytest.fixture
def extended_type_shapes() -> dict[str, type[Shape]]:
    """Shape definitions using extended types."""

    class Event(Shape):
        """Event with datetime tracking."""

        created_at = DatetimeSlot()
        updated_at = DatetimeSlot()
        duration = TimedeltaSlot()
        event_date = DateSlot()
        start_time = TimeSlot()

    class Account(Shape):
        """Financial account with precise decimals."""

        id = UUIDSlot()
        balance = DecimalSlot()
        interest_rate = FractionSlot()

    class Config(Shape):
        """Configuration with paths."""

        config_path = PathSlot()
        data_dir = PathSlot()

    class Signal(Shape):
        """Signal with complex numbers."""

        amplitude = ComplexSlot()
        phase = ComplexSlot()

    return {
        "Event": Event,
        "Account": Account,
        "Config": Config,
        "Signal": Signal,
    }


# ============================================================================
# DATETIME TESTS
# ============================================================================


def test_datetime_set_and_get(extended_type_shapes, ctx):
    """Test setting and getting datetime values."""
    Event = extended_type_shapes["Event"]

    now = datetime.now()
    Event.created_at.set(now).execute(ctx)
    result = Event.created_at.get().execute(ctx)

    # Compare as ISO strings since datetime precision may vary
    assert result.isoformat()[:19] == now.isoformat()[:19]


def test_datetime_with_timezone(extended_type_shapes, ctx):
    """Test datetime with timezone."""
    Event = extended_type_shapes["Event"]

    utc_now = datetime.now(UTC)
    Event.created_at.set(utc_now).execute(ctx)
    result = Event.created_at.get().execute(ctx)

    assert result.tzinfo == UTC


def test_datetime_component_access(extended_type_shapes, ctx):
    """Test accessing datetime components."""
    Event = extended_type_shapes["Event"]

    dt = datetime(2024, 6, 15, 10, 30, 45)
    Event.created_at.set(dt).execute(ctx)

    # Access components through DSL
    year_op = Event.created_at.get().year()
    month_op = Event.created_at.get().month()
    day_op = Event.created_at.get().day()

    assert year_op.execute(ctx) == 2024
    assert month_op.execute(ctx) == 6
    assert day_op.execute(ctx) == 15


# ============================================================================
# TIMEDELTA TESTS
# ============================================================================


def test_timedelta_set_and_get(extended_type_shapes, ctx):
    """Test setting and getting timedelta values."""
    Event = extended_type_shapes["Event"]

    delta = timedelta(hours=2, minutes=30)
    Event.duration.set(delta).execute(ctx)
    result = Event.duration.get().execute(ctx)

    assert result.total_seconds() == delta.total_seconds()


def test_timedelta_components(extended_type_shapes, ctx):
    """Test timedelta component access."""
    Event = extended_type_shapes["Event"]

    delta = timedelta(days=5, hours=3, minutes=30)
    Event.duration.set(delta).execute(ctx)

    days_op = Event.duration.get().days()
    total_seconds_op = Event.duration.get().total_seconds()

    assert days_op.execute(ctx) == 5
    assert total_seconds_op.execute(ctx) == delta.total_seconds()


# ============================================================================
# DATE TESTS
# ============================================================================


def test_date_set_and_get(extended_type_shapes, ctx):
    """Test setting and getting date values."""
    Event = extended_type_shapes["Event"]

    d = date(2024, 6, 15)
    Event.event_date.set(d).execute(ctx)
    result = Event.event_date.get().execute(ctx)

    assert result == d


def test_date_components(extended_type_shapes, ctx):
    """Test date component access."""
    Event = extended_type_shapes["Event"]

    d = date(2024, 6, 15)
    Event.event_date.set(d).execute(ctx)

    year_op = Event.event_date.get().year()
    month_op = Event.event_date.get().month()
    weekday_op = Event.event_date.get().weekday()

    assert year_op.execute(ctx) == 2024
    assert month_op.execute(ctx) == 6
    # June 15, 2024 is a Saturday = 5
    assert weekday_op.execute(ctx) == 5


# ============================================================================
# TIME TESTS
# ============================================================================


def test_time_set_and_get(extended_type_shapes, ctx):
    """Test setting and getting time values."""
    Event = extended_type_shapes["Event"]

    t = time(10, 30, 45)
    Event.start_time.set(t).execute(ctx)
    result = Event.start_time.get().execute(ctx)

    assert result == t


def test_time_components(extended_type_shapes, ctx):
    """Test time component access."""
    Event = extended_type_shapes["Event"]

    t = time(14, 30, 15)
    Event.start_time.set(t).execute(ctx)

    hour_op = Event.start_time.get().hour()
    minute_op = Event.start_time.get().minute()
    second_op = Event.start_time.get().second()

    assert hour_op.execute(ctx) == 14
    assert minute_op.execute(ctx) == 30
    assert second_op.execute(ctx) == 15


# ============================================================================
# DECIMAL TESTS
# ============================================================================


def test_decimal_set_and_get(extended_type_shapes, ctx):
    """Test setting and getting Decimal values."""
    Account = extended_type_shapes["Account"]

    balance = Decimal("1000.50")
    Account.balance.set(balance).execute(ctx)
    result = Account.balance.get().execute(ctx)

    assert result == balance


def test_decimal_from_string(extended_type_shapes, ctx):
    """Test setting Decimal from string."""
    Account = extended_type_shapes["Account"]

    Account.balance.set("123.456").execute(ctx)
    result = Account.balance.get().execute(ctx)

    assert result == Decimal("123.456")


def test_decimal_precision(extended_type_shapes, ctx):
    """Test Decimal preserves exact precision."""
    Account = extended_type_shapes["Account"]

    # This value can't be represented exactly as float
    balance = Decimal("0.1") + Decimal("0.2")
    Account.balance.set(balance).execute(ctx)
    result = Account.balance.get().execute(ctx)

    assert result == Decimal("0.3")


# ============================================================================
# FRACTION TESTS
# ============================================================================


def test_fraction_set_and_get(extended_type_shapes, ctx):
    """Test setting and getting Fraction values."""
    Account = extended_type_shapes["Account"]

    rate = Fraction(3, 4)
    Account.interest_rate.set(rate).execute(ctx)
    result = Account.interest_rate.get().execute(ctx)

    assert result == rate
    assert result.numerator == 3
    assert result.denominator == 4


def test_fraction_from_string(extended_type_shapes, ctx):
    """Test setting Fraction from string."""
    Account = extended_type_shapes["Account"]

    Account.interest_rate.set("5/8").execute(ctx)
    result = Account.interest_rate.get().execute(ctx)

    assert result == Fraction(5, 8)


def test_fraction_normalization(extended_type_shapes, ctx):
    """Test Fraction auto-normalization."""
    Account = extended_type_shapes["Account"]

    # 6/8 should normalize to 3/4
    rate = Fraction(6, 8)
    Account.interest_rate.set(rate).execute(ctx)
    result = Account.interest_rate.get().execute(ctx)

    assert result == Fraction(3, 4)
    assert result.numerator == 3
    assert result.denominator == 4


# ============================================================================
# UUID TESTS
# ============================================================================


def test_uuid_set_and_get(extended_type_shapes, ctx):
    """Test setting and getting UUID values."""
    Account = extended_type_shapes["Account"]

    uid = uuid4()
    Account.id.set(uid).execute(ctx)
    result = Account.id.get().execute(ctx)

    assert result == uid


def test_uuid_from_string(extended_type_shapes, ctx):
    """Test setting UUID from string."""
    Account = extended_type_shapes["Account"]

    uid_str = "12345678-1234-5678-1234-567812345678"
    Account.id.set(uid_str).execute(ctx)
    result = Account.id.get().execute(ctx)

    assert result == UUID(uid_str)


def test_uuid_version(extended_type_shapes, ctx):
    """Test UUID version access."""
    Account = extended_type_shapes["Account"]

    # UUID4 is version 4
    uid = uuid4()
    Account.id.set(uid).execute(ctx)

    version_op = Account.id.get().version()
    assert version_op.execute(ctx) == 4


# ============================================================================
# PATH TESTS
# ============================================================================


def test_path_set_and_get(extended_type_shapes, ctx):
    """Test setting and getting Path values."""
    Config = extended_type_shapes["Config"]

    p = Path("/home/user/config.json")
    Config.config_path.set(p).execute(ctx)
    result = Config.config_path.get().execute(ctx)

    assert result == p


def test_path_from_string(extended_type_shapes, ctx):
    """Test setting Path from string."""
    Config = extended_type_shapes["Config"]

    Config.config_path.set("/etc/app/config.json").execute(ctx)
    result = Config.config_path.get().execute(ctx)

    assert result == Path("/etc/app/config.json")


def test_path_components(extended_type_shapes, ctx):
    """Test path component access."""
    Config = extended_type_shapes["Config"]

    p = Path("/home/user/data/file.txt")
    Config.config_path.set(p).execute(ctx)

    name_op = Config.config_path.get().name()
    stem_op = Config.config_path.get().stem()
    suffix_op = Config.config_path.get().suffix()
    parent_op = Config.config_path.get().parent()

    assert name_op.execute(ctx) == "file.txt"
    assert stem_op.execute(ctx) == "file"
    assert suffix_op.execute(ctx) == ".txt"
    assert parent_op.execute(ctx) == Path("/home/user/data")


# ============================================================================
# COMPLEX TESTS
# ============================================================================


def test_complex_set_and_get(extended_type_shapes, ctx):
    """Test setting and getting complex values."""
    Signal = extended_type_shapes["Signal"]

    c = complex(3, 4)
    Signal.amplitude.set(c).execute(ctx)
    result = Signal.amplitude.get().execute(ctx)

    assert result == c


def test_complex_components(extended_type_shapes, ctx):
    """Test complex component access."""
    Signal = extended_type_shapes["Signal"]

    c = complex(3, 4)
    Signal.amplitude.set(c).execute(ctx)

    real_op = Signal.amplitude.get().real()
    imag_op = Signal.amplitude.get().imag()

    assert real_op.execute(ctx) == 3.0
    assert imag_op.execute(ctx) == 4.0


def test_complex_magnitude(extended_type_shapes, ctx):
    """Test complex magnitude (abs)."""
    Signal = extended_type_shapes["Signal"]

    # 3-4-5 triangle
    c = complex(3, 4)
    Signal.amplitude.set(c).execute(ctx)

    # abs(3+4j) = 5
    result = Signal.amplitude.get().execute(ctx)
    assert abs(result) == 5.0


def test_complex_conjugate(extended_type_shapes, ctx):
    """Test complex conjugate."""
    Signal = extended_type_shapes["Signal"]

    c = complex(3, 4)
    Signal.amplitude.set(c).execute(ctx)

    conjugate_op = Signal.amplitude.get().conjugate()
    result = conjugate_op.execute(ctx)

    assert result == complex(3, -4)
