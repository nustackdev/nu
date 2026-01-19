"""Functional test configuration for type tests."""

import pytest

from everybase.type import (
    ComplexSlot,
    DateSlot,
    DatetimeSlot,
    DecimalSlot,
    FractionSlot,
    PathSlot,
    PercentageSlot,
    SeriesSlot,
    TimedeltaSlot,
    TimeSlot,
    TimezoneSlot,
    UUIDSlot,
)
from everyterm import Shape


# ============================================================================
# SHAPE FIXTURES
# ============================================================================


@pytest.fixture
def date_shape() -> type[Shape]:
    """Shape with DateSlot."""

    class Event(Shape):
        event_date = DateSlot()
        start_date = DateSlot()
        end_date = DateSlot()

    return Event


@pytest.fixture
def datetime_shape() -> type[Shape]:
    """Shape with DatetimeSlot."""

    class Event(Shape):
        created_at = DatetimeSlot()
        updated_at = DatetimeSlot()
        scheduled_at = DatetimeSlot()

    return Event


@pytest.fixture
def decimal_shape() -> type[Shape]:
    """Shape with DecimalSlot."""

    class Account(Shape):
        balance = DecimalSlot()
        credit = DecimalSlot()
        debit = DecimalSlot()

    return Account


@pytest.fixture
def path_shape() -> type[Shape]:
    """Shape with PathSlot."""

    class Config(Shape):
        config_path = PathSlot()
        data_dir = PathSlot()
        log_file = PathSlot()

    return Config


@pytest.fixture
def time_shape() -> type[Shape]:
    """Shape with TimeSlot."""

    class Schedule(Shape):
        start_time = TimeSlot()
        end_time = TimeSlot()
        break_time = TimeSlot()

    return Schedule


@pytest.fixture
def timedelta_shape() -> type[Shape]:
    """Shape with TimedeltaSlot."""

    class Task(Shape):
        duration = TimedeltaSlot()
        timeout = TimedeltaSlot()
        interval = TimedeltaSlot()

    return Task


@pytest.fixture
def timezone_shape() -> type[Shape]:
    """Shape with TimezoneSlot."""

    class Location(Shape):
        local_tz = TimezoneSlot()
        display_tz = TimezoneSlot()

    return Location


@pytest.fixture
def uuid_shape() -> type[Shape]:
    """Shape with UUIDSlot."""

    class Entity(Shape):
        id = UUIDSlot()
        parent_id = UUIDSlot()
        correlation_id = UUIDSlot()

    return Entity


@pytest.fixture
def complex_shape() -> type[Shape]:
    """Shape with ComplexSlot."""

    class Signal(Shape):
        amplitude = ComplexSlot()
        phase = ComplexSlot()
        coefficient = ComplexSlot()

    return Signal


@pytest.fixture
def fraction_shape() -> type[Shape]:
    """Shape with FractionSlot."""

    class Ratio(Shape):
        portion = FractionSlot()
        scale = FractionSlot()
        multiplier = FractionSlot()

    return Ratio


@pytest.fixture
def percentage_shape() -> type[Shape]:
    """Shape with PercentageSlot."""

    class Metrics(Shape):
        completion = PercentageSlot()
        discount = PercentageSlot()
        tax_rate = PercentageSlot()

    return Metrics


@pytest.fixture
def series_shape() -> type[Shape]:
    """Shape with SeriesSlot."""

    class Stock(Shape):
        prices = SeriesSlot()
        volumes = SeriesSlot()
        returns = SeriesSlot()

    return Stock
