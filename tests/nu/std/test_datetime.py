"""Functional tests for ``nu.std.datetime`` - drive the Forms through the engine.

Covers every modeling path across the five classes: constructors and method
calls (factory atoms), property reads (core ``GetAttrQuery``), arithmetic and
comparison (core atoms), kwargs (``replace``), and the async path.
"""

from __future__ import annotations

import asyncio
import datetime as pydt

from nu.lang.helpers import arun, run
from nu.std.datetime import date, datetime, time, timedelta, timezone


# --- property reads (core GetAttrQuery) ---------------------------------


def test_date_property() -> None:
    assert run(date.of(2026, 6, 30).month())[0] == 6


def test_timedelta_property() -> None:
    assert run(timedelta.of(days=2).days())[0] == 2


# --- method calls (factory atoms over unbound methods) ------------------


def test_date_weekday() -> None:
    assert run(date.from_iso("2026-06-30").weekday())[0] == pydt.date(2026, 6, 30).weekday()


def test_date_isoformat() -> None:
    assert run(date.of(2026, 6, 30).isoformat())[0] == "2026-06-30"


def test_datetime_replace_kwargs() -> None:
    value, _ = run(datetime.of(2026, 6, 30, 14, 30).replace(hour=9).isoformat())
    assert value == "2026-06-30T09:30:00"


def test_datetime_date_part() -> None:
    assert run(datetime.of(2026, 6, 30, 14, 30).date().year())[0] == 2026


# --- arithmetic (core atoms; Python does the real op) -------------------


def test_date_plus_timedelta() -> None:
    value, _ = run((date.of(2026, 6, 30) + timedelta.of(days=5)).isoformat())
    assert value == "2026-07-05"


def test_date_minus_date_is_timedelta() -> None:
    value, _ = run((date.of(2026, 7, 10) - date.of(2026, 6, 30)).total_seconds())
    assert value == 10 * 86400


def test_timedelta_scaling() -> None:
    assert run((timedelta.of(hours=1) * 3).total_seconds())[0] == 10800.0


# --- comparison (core atoms) --------------------------------------------


def test_time_comparison() -> None:
    assert run(time.of(9, 0) < time.of(17, 0))[0] is True


# --- timezone -----------------------------------------------------------


def test_timezone_utc_offset() -> None:
    assert run(timezone.utc().utcoffset().total_seconds())[0] == 0.0


# --- non-deterministic constructor + async path -------------------------


def test_now_returns_a_datetime() -> None:
    value, _ = run(datetime.now())
    assert isinstance(value, pydt.datetime)


def test_runs_on_async_path() -> None:
    value, _ = asyncio.run(arun(date.of(2026, 6, 30).isoformat()))
    assert value == "2026-06-30"
