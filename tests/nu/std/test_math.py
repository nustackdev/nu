"""Functional tests for ``nu.std.math`` - drive the Forms through the engine.

Covers the three return shapes (float, int, bool wrappers), a constant, and the
async path, asserting against the real ``math`` results.
"""

from __future__ import annotations

import asyncio
import math

from nu.lang.helpers import arun, run
from nu.std.math import (
    atan2,
    e,
    factorial,
    floor,
    gcd,
    hypot,
    isnan,
    log,
    pi,
    pow,
    sqrt,
)


def test_sqrt() -> None:
    value, _ = run(sqrt(2))
    assert math.isclose(value, math.sqrt(2))


def test_pow() -> None:
    value, _ = run(pow(2, 10))
    assert math.isclose(value, math.pow(2, 10))


def test_hypot() -> None:
    value, _ = run(hypot(3, 4))
    assert math.isclose(value, math.hypot(3, 4))


def test_atan2_two_args() -> None:
    value, _ = run(atan2(1, 1))
    assert math.isclose(value, math.atan2(1, 1))


def test_log_with_base() -> None:
    value, _ = run(log(8, 2))
    assert math.isclose(value, math.log(8, 2))


def test_floor_returns_int() -> None:
    value, _ = run(floor(3.7))
    assert value == 3
    assert isinstance(value, int)


def test_gcd_returns_int() -> None:
    value, _ = run(gcd(12, 8))
    assert value == math.gcd(12, 8)


def test_factorial_returns_int() -> None:
    value, _ = run(factorial(5))
    assert value == math.factorial(5)


def test_isnan_returns_bool() -> None:
    value, _ = run(isnan(float("nan")))
    assert value is True


def test_isnan_false() -> None:
    value, _ = run(isnan(0.0))
    assert value is False


def test_pi_constant() -> None:
    value, _ = run(pi)
    assert math.isclose(value, math.pi)


def test_e_constant() -> None:
    value, _ = run(e)
    assert math.isclose(value, math.e)


def test_runs_on_async_path() -> None:
    value, _ = asyncio.run(arun(sqrt(2)))
    assert math.isclose(value, math.sqrt(2))
