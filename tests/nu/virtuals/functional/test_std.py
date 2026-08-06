"""Functional tests for the virtuals stdlib-typed refs (``std``).

Each ref stores a serialized primitive and carries the matching ``nu.std`` Form.
These tests drive the store/read round-trip through a real virtuals transaction
(the ``ctx`` fixture), assert the value comes back as its true domain type, and
check that the Form interface flows through the ref. Constructor / method
coverage of the Forms themselves lives under ``tests/nu/std``.

Sync path throughout; one async test guards that ``coerce`` still runs on the
async read path (``acoerce``).
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from fractions import Fraction
from pathlib import PurePath
from uuid import UUID, uuid4

from nu import Shape, arun, run
from nu.std.fin import PyBasisPoint, PyPercentage
from nu.virtuals import (
    BasisPointRef,
    ComplexRef,
    DateRef,
    DatetimeRef,
    DecimalRef,
    FractionRef,
    PathRef,
    PercentageRef,
    TimedeltaRef,
    TimeRef,
    TimezoneRef,
    UUIDRef,
)


UTC = timezone.utc


class Bag(Shape):
    dec = DecimalRef.slot()
    frac = FractionRef.slot()
    cplx = ComplexRef.slot()
    bps = BasisPointRef.slot()
    pct = PercentageRef.slot()
    d = DateRef.slot()
    dt = DatetimeRef.slot()
    t = TimeRef.slot()
    td = TimedeltaRef.slot()
    tz = TimezoneRef.slot()
    p = PathRef.slot()
    uid = UUIDRef.slot()


def _roundtrip(ref, value, ctx):
    run(ref.set(value), ctx)
    return run(ref, ctx)[0]


# --- numeric ----------------------------------------------------------------


def test_decimal_roundtrip_is_exact(ctx) -> None:
    got = _roundtrip(Bag.dec, Decimal("0.1") + Decimal("0.2"), ctx)
    assert got == Decimal("0.3")
    assert isinstance(got, Decimal)


def test_decimal_from_string(ctx) -> None:
    assert _roundtrip(Bag.dec, "999.99", ctx) == Decimal("999.99")


def test_fraction_roundtrip(ctx) -> None:
    got = _roundtrip(Bag.frac, Fraction(3, 4), ctx)
    assert got == Fraction(3, 4)
    assert isinstance(got, Fraction)


def test_complex_roundtrip(ctx) -> None:
    got = _roundtrip(Bag.cplx, 3.5 + 2.25j, ctx)
    assert got == 3.5 + 2.25j
    assert isinstance(got, complex)


def test_basis_point_roundtrip(ctx) -> None:
    got = _roundtrip(Bag.bps, PyBasisPoint(500), ctx)
    assert got == PyBasisPoint(500)
    assert isinstance(got, PyBasisPoint)


def test_percentage_roundtrip(ctx) -> None:
    got = _roundtrip(Bag.pct, PyPercentage(2.5), ctx)
    assert got == PyPercentage(2.5)
    assert isinstance(got, PyPercentage)


# --- datetime family --------------------------------------------------------


def test_date_roundtrip(ctx) -> None:
    d = date(2026, 7, 2)
    assert _roundtrip(Bag.d, d, ctx) == d


def test_datetime_roundtrip(ctx) -> None:
    dt = datetime(2026, 7, 2, 12, 30, tzinfo=UTC)
    assert _roundtrip(Bag.dt, dt, ctx) == dt


def test_time_roundtrip(ctx) -> None:
    t = time(12, 30, 15)
    assert _roundtrip(Bag.t, t, ctx) == t


def test_timedelta_roundtrip(ctx) -> None:
    td = timedelta(seconds=3661.5)
    got = _roundtrip(Bag.td, td, ctx)
    assert got == td
    assert isinstance(got, timedelta)


def test_timezone_roundtrip_offset(ctx) -> None:
    tz = timezone(timedelta(hours=5, minutes=30))
    assert _roundtrip(Bag.tz, tz, ctx) == tz


def test_timezone_roundtrip_utc(ctx) -> None:
    assert _roundtrip(Bag.tz, UTC, ctx) == UTC


# --- path + uuid ------------------------------------------------------------


def test_path_roundtrip(ctx) -> None:
    got = _roundtrip(Bag.p, PurePath("/home/user/file.txt"), ctx)
    assert got == PurePath("/home/user/file.txt")


def test_path_from_string(ctx) -> None:
    assert _roundtrip(Bag.p, "/etc/config.json", ctx) == PurePath("/etc/config.json")


def test_uuid_roundtrip(ctx) -> None:
    u = uuid4()
    got = _roundtrip(Bag.uid, u, ctx)
    assert got == u
    assert isinstance(got, UUID)


def test_uuid_from_string(ctx) -> None:
    s = "12345678-1234-5678-1234-567812345678"
    assert _roundtrip(Bag.uid, s, ctx) == UUID(s)


# --- the Form interface flows through the ref -------------------------------


def test_decimal_form_op_through_ref(ctx) -> None:
    run(Bag.dec.set(Decimal("123.456789")), ctx)
    got = run(Bag.dec.quantize(Decimal("0.01")), ctx)[0]
    assert got == Decimal("123.46")


def test_basis_point_apply_through_ref(ctx) -> None:
    run(Bag.bps.set(PyBasisPoint(500)), ctx)
    assert run(Bag.bps.apply(1000), ctx)[0] == 50.0


def test_uuid_hex_through_ref(ctx) -> None:
    s = "12345678-1234-5678-1234-567812345678"
    run(Bag.uid.set(UUID(s)), ctx)
    assert run(Bag.uid.hex(), ctx)[0] == "12345678123456781234567812345678"


# --- storing a computed Nu term ---------------------------------------------


def test_store_computed_term(ctx) -> None:
    run(Bag.dec.set(Decimal("100")), ctx)
    run(Bag.dec.set(Bag.dec + Decimal("1")), ctx)
    assert run(Bag.dec, ctx)[0] == Decimal("101")


# --- async read coerces too (guards the base acoerce path) ------------------


async def test_async_read_coerces(ctx) -> None:
    dt = datetime(2026, 7, 2, 12, 30, tzinfo=UTC)
    await arun(Bag.dt.set(dt), ctx)
    got = (await arun(Bag.dt, ctx))[0]
    assert got == dt
    assert isinstance(got, datetime)
