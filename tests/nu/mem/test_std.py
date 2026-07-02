"""Functional tests for the dict-substrate stdlib-typed refs (``std``).

Each ref stores a serialized primitive in the nested dict and carries the
matching ``nu.std`` Form. These tests drive the store/read round-trip through a
dict-backed context, assert the value comes back as its true domain type, and
check that the Form interface flows through the ref. Constructor / method
coverage of the Forms themselves lives under ``tests/nu/std``.

Sync path throughout; one async test guards that ``coerce`` still runs on the
async read path (``acoerce``).
"""

from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta, timezone
from decimal import Decimal
from fractions import Fraction
from pathlib import PurePath
from uuid import UUID, uuid4

import pytest

from nu import Context, Shape, arun, run
from nu.mem import (
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
from nu.std.fin import PyBasisPoint, PyPercentage


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


@pytest.fixture
def bag_ctx() -> Context:
    """Context with a fresh root dict scoped to the Bag shape."""
    return Context().bind(dict, {}, Bag)


def _roundtrip(ref, value, ctx):
    run(ref.store(value), ctx)
    return run(ref, ctx)[0]


# --- numeric ----------------------------------------------------------------


def test_decimal_roundtrip_is_exact(bag_ctx) -> None:
    got = _roundtrip(Bag.dec, Decimal("0.1") + Decimal("0.2"), bag_ctx)
    assert got == Decimal("0.3")
    assert isinstance(got, Decimal)


def test_decimal_from_string(bag_ctx) -> None:
    assert _roundtrip(Bag.dec, "999.99", bag_ctx) == Decimal("999.99")


def test_fraction_roundtrip(bag_ctx) -> None:
    got = _roundtrip(Bag.frac, Fraction(3, 4), bag_ctx)
    assert got == Fraction(3, 4)
    assert isinstance(got, Fraction)


def test_complex_roundtrip(bag_ctx) -> None:
    got = _roundtrip(Bag.cplx, 3.5 + 2.25j, bag_ctx)
    assert got == 3.5 + 2.25j
    assert isinstance(got, complex)


def test_basis_point_roundtrip(bag_ctx) -> None:
    got = _roundtrip(Bag.bps, PyBasisPoint(500), bag_ctx)
    assert got == PyBasisPoint(500)
    assert isinstance(got, PyBasisPoint)


def test_percentage_roundtrip(bag_ctx) -> None:
    got = _roundtrip(Bag.pct, PyPercentage(2.5), bag_ctx)
    assert got == PyPercentage(2.5)
    assert isinstance(got, PyPercentage)


# --- datetime family --------------------------------------------------------


def test_date_roundtrip(bag_ctx) -> None:
    d = date(2026, 7, 2)
    assert _roundtrip(Bag.d, d, bag_ctx) == d


def test_datetime_roundtrip(bag_ctx) -> None:
    dt = datetime(2026, 7, 2, 12, 30, tzinfo=UTC)
    assert _roundtrip(Bag.dt, dt, bag_ctx) == dt


def test_time_roundtrip(bag_ctx) -> None:
    t = time(12, 30, 15)
    assert _roundtrip(Bag.t, t, bag_ctx) == t


def test_timedelta_roundtrip(bag_ctx) -> None:
    td = timedelta(seconds=3661.5)
    got = _roundtrip(Bag.td, td, bag_ctx)
    assert got == td
    assert isinstance(got, timedelta)


def test_timezone_roundtrip_offset(bag_ctx) -> None:
    tz = timezone(timedelta(hours=5, minutes=30))
    assert _roundtrip(Bag.tz, tz, bag_ctx) == tz


def test_timezone_roundtrip_utc(bag_ctx) -> None:
    assert _roundtrip(Bag.tz, UTC, bag_ctx) == UTC


# --- path + uuid ------------------------------------------------------------


def test_path_roundtrip(bag_ctx) -> None:
    got = _roundtrip(Bag.p, PurePath("/home/user/file.txt"), bag_ctx)
    assert got == PurePath("/home/user/file.txt")


def test_path_from_string(bag_ctx) -> None:
    assert _roundtrip(Bag.p, "/etc/config.json", bag_ctx) == PurePath("/etc/config.json")


def test_uuid_roundtrip(bag_ctx) -> None:
    u = uuid4()
    got = _roundtrip(Bag.uid, u, bag_ctx)
    assert got == u
    assert isinstance(got, UUID)


def test_uuid_from_string(bag_ctx) -> None:
    s = "12345678-1234-5678-1234-567812345678"
    assert _roundtrip(Bag.uid, s, bag_ctx) == UUID(s)


# --- the Form interface flows through the ref -------------------------------


def test_decimal_form_op_through_ref(bag_ctx) -> None:
    run(Bag.dec.store(Decimal("123.456789")), bag_ctx)
    got = run(Bag.dec.quantize(Decimal("0.01")), bag_ctx)[0]
    assert got == Decimal("123.46")


def test_basis_point_apply_through_ref(bag_ctx) -> None:
    run(Bag.bps.store(PyBasisPoint(500)), bag_ctx)
    assert run(Bag.bps.apply(1000), bag_ctx)[0] == 50.0


def test_uuid_hex_through_ref(bag_ctx) -> None:
    s = "12345678-1234-5678-1234-567812345678"
    run(Bag.uid.store(UUID(s)), bag_ctx)
    assert run(Bag.uid.hex(), bag_ctx)[0] == "12345678123456781234567812345678"


# --- storing a computed Nu term ---------------------------------------------


def test_store_computed_term(bag_ctx) -> None:
    run(Bag.dec.store(Decimal("100")), bag_ctx)
    run(Bag.dec.store(Bag.dec + Decimal("1")), bag_ctx)
    assert run(Bag.dec, bag_ctx)[0] == Decimal("101")


# --- serialized storage shape (dict holds primitives, not objects) ----------


def test_stored_values_are_serialized_primitives(bag_ctx) -> None:
    run(Bag.dec.store(Decimal("1.5")), bag_ctx)
    run(Bag.bps.store(PyBasisPoint(500)), bag_ctx)
    run(Bag.pct.store(PyPercentage(2.5)), bag_ctx)
    raw = run(Bag.dec, bag_ctx)[1].get(dict, Bag)
    assert raw["dec"] == "1.5"
    assert raw["bps"] == 500
    assert raw["pct"] == 2.5


# --- async read coerces too (guards the base acoerce path) ------------------


async def test_async_read_coerces(bag_ctx) -> None:
    dt = datetime(2026, 7, 2, 12, 30, tzinfo=UTC)
    await arun(Bag.dt.store(dt), bag_ctx)
    got = (await arun(Bag.dt, bag_ctx))[0]
    assert got == dt
    assert isinstance(got, datetime)
