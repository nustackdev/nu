"""Functional tests for the dict-substrate stdlib-typed refs (``items_extended``).

Each ref stores a serialized primitive in the nested dict and carries the
matching ``nu.std`` Form. These tests drive the store/read round-trip through a
dict-backed context, assert the value comes back as its true domain type, and
check that the Form interface flows through the ref. Constructor / method
coverage of the Forms themselves lives under ``tests/nu/std``.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta, timezone
from decimal import Decimal
from fractions import Fraction
from pathlib import PurePath
from uuid import UUID, uuid4

import pytest

from nu import Context, arun
from nu.domains.shape import Shape
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
from nu.std.fin.native import BasisPoint, Percentage


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


async def _roundtrip(ref, value, ctx):
    await arun(ref.store(value), ctx)
    return (await arun(ref, ctx))[0]


# --- numeric ----------------------------------------------------------------


async def test_decimal_roundtrip_is_exact(bag_ctx) -> None:
    got = await _roundtrip(Bag.dec, Decimal("0.1") + Decimal("0.2"), bag_ctx)
    assert got == Decimal("0.3")
    assert isinstance(got, Decimal)


async def test_decimal_from_string(bag_ctx) -> None:
    assert await _roundtrip(Bag.dec, "999.99", bag_ctx) == Decimal("999.99")


async def test_fraction_roundtrip(bag_ctx) -> None:
    got = await _roundtrip(Bag.frac, Fraction(3, 4), bag_ctx)
    assert got == Fraction(3, 4)
    assert isinstance(got, Fraction)


async def test_complex_roundtrip(bag_ctx) -> None:
    got = await _roundtrip(Bag.cplx, 3.5 + 2.25j, bag_ctx)
    assert got == 3.5 + 2.25j
    assert isinstance(got, complex)


async def test_basis_point_roundtrip(bag_ctx) -> None:
    got = await _roundtrip(Bag.bps, BasisPoint(500), bag_ctx)
    assert got == BasisPoint(500)
    assert isinstance(got, BasisPoint)


async def test_percentage_roundtrip(bag_ctx) -> None:
    got = await _roundtrip(Bag.pct, Percentage(2.5), bag_ctx)
    assert got == Percentage(2.5)
    assert isinstance(got, Percentage)


# --- datetime family --------------------------------------------------------


async def test_date_roundtrip(bag_ctx) -> None:
    d = date(2026, 7, 2)
    assert await _roundtrip(Bag.d, d, bag_ctx) == d


async def test_datetime_roundtrip(bag_ctx) -> None:
    dt = datetime(2026, 7, 2, 12, 30, tzinfo=UTC)
    assert await _roundtrip(Bag.dt, dt, bag_ctx) == dt


async def test_time_roundtrip(bag_ctx) -> None:
    t = time(12, 30, 15)
    assert await _roundtrip(Bag.t, t, bag_ctx) == t


async def test_timedelta_roundtrip(bag_ctx) -> None:
    td = timedelta(seconds=3661.5)
    got = await _roundtrip(Bag.td, td, bag_ctx)
    assert got == td
    assert isinstance(got, timedelta)


async def test_timezone_roundtrip_offset(bag_ctx) -> None:
    tz = timezone(timedelta(hours=5, minutes=30))
    assert await _roundtrip(Bag.tz, tz, bag_ctx) == tz


async def test_timezone_roundtrip_utc(bag_ctx) -> None:
    assert await _roundtrip(Bag.tz, UTC, bag_ctx) == UTC


# --- path + uuid ------------------------------------------------------------


async def test_path_roundtrip(bag_ctx) -> None:
    got = await _roundtrip(Bag.p, PurePath("/home/user/file.txt"), bag_ctx)
    assert got == PurePath("/home/user/file.txt")


async def test_path_from_string(bag_ctx) -> None:
    assert await _roundtrip(Bag.p, "/etc/config.json", bag_ctx) == PurePath("/etc/config.json")


async def test_uuid_roundtrip(bag_ctx) -> None:
    u = uuid4()
    got = await _roundtrip(Bag.uid, u, bag_ctx)
    assert got == u
    assert isinstance(got, UUID)


async def test_uuid_from_string(bag_ctx) -> None:
    s = "12345678-1234-5678-1234-567812345678"
    assert await _roundtrip(Bag.uid, s, bag_ctx) == UUID(s)


# --- the Form interface flows through the ref -------------------------------


async def test_decimal_form_op_through_ref(bag_ctx) -> None:
    await arun(Bag.dec.store(Decimal("123.456789")), bag_ctx)
    got = (await arun(Bag.dec.quantize(Decimal("0.01")), bag_ctx))[0]
    assert got == Decimal("123.46")


async def test_basis_point_apply_through_ref(bag_ctx) -> None:
    await arun(Bag.bps.store(BasisPoint(500)), bag_ctx)
    assert (await arun(Bag.bps.apply(1000), bag_ctx))[0] == 50.0


async def test_uuid_hex_through_ref(bag_ctx) -> None:
    s = "12345678-1234-5678-1234-567812345678"
    await arun(Bag.uid.store(UUID(s)), bag_ctx)
    assert (await arun(Bag.uid.hex(), bag_ctx))[0] == "12345678123456781234567812345678"


# --- storing a computed Nu term ---------------------------------------------


async def test_store_computed_term(bag_ctx) -> None:
    await arun(Bag.dec.store(Decimal("100")), bag_ctx)
    await arun(Bag.dec.store(Bag.dec + Decimal("1")), bag_ctx)
    assert (await arun(Bag.dec, bag_ctx))[0] == Decimal("101")


# --- serialized storage shape (dict holds primitives, not objects) ----------


async def test_stored_values_are_serialized_primitives(bag_ctx) -> None:
    await arun(Bag.dec.store(Decimal("1.5")), bag_ctx)
    await arun(Bag.bps.store(BasisPoint(500)), bag_ctx)
    await arun(Bag.pct.store(Percentage(2.5)), bag_ctx)
    raw = (await arun(Bag.dec, bag_ctx))[1].get(dict, Bag)
    assert raw["dec"] == "1.5"
    assert raw["bps"] == 500
    assert raw["pct"] == 2.5
