"""Functional tests for ``nu.std.cmath`` - drive the Forms through the engine.

Covers the ``complex`` value type (constructor, property reads, conjugate, abs,
arithmetic, equality), several ``cmath`` functions across the return shapes
(complex, float, bool, tuple), a constant, and the async path, asserting against
the real ``complex`` / ``cmath`` results.
"""

from __future__ import annotations

import asyncio
import cmath
import math
from builtins import complex as _complex

from nu.lang.helpers import arun, run
from nu.std.cmath import complex, isnan, phase, pi, polar, sqrt


# --- the complex value type ---------------------------------------------


def test_complex_ctor() -> None:
    value, _ = run(complex.of(3, 4))
    assert value == (3 + 4j)
    assert isinstance(value, _complex)


def test_complex_real_part() -> None:
    value, _ = run(complex.of(3, 4).real())
    assert value == 3.0


def test_complex_imag_part() -> None:
    value, _ = run(complex.of(3, 4).imag())
    assert value == 4.0


def test_complex_conjugate() -> None:
    value, _ = run(complex.of(3, 4).conjugate())
    assert value == (3 - 4j)


def test_complex_abs_is_magnitude() -> None:
    value, _ = run(abs(complex.of(3, 4)))
    assert value == 5.0
    assert isinstance(value, float)


def test_complex_add() -> None:
    value, _ = run(complex.of(1, 2) + complex.of(3, 4))
    assert value == (4 + 6j)


def test_complex_mul() -> None:
    value, _ = run(complex.of(1, 2) * complex.of(3, 4))
    assert value == ((1 + 2j) * (3 + 4j))


def test_complex_eq() -> None:
    assert run(complex.of(3, 4).eq(complex.of(3, 4)))[0] is True


def test_complex_ne() -> None:
    assert run(complex.of(3, 4).ne(complex.of(0, 1)))[0] is True


# --- cmath functions ----------------------------------------------------


def test_sqrt_of_negative() -> None:
    value, _ = run(sqrt(complex.of(-1, 0)))
    assert cmath.isclose(value, cmath.sqrt(-1 + 0j))


def test_phase_returns_float() -> None:
    value, _ = run(phase(complex.of(0, 1)))
    assert isinstance(value, float)
    assert math.isclose(value, cmath.phase(1j))


def test_polar_returns_tuple() -> None:
    value, _ = run(polar(complex.of(0, 1)))
    expected = cmath.polar(1j)
    assert math.isclose(value[0], expected[0])
    assert math.isclose(value[1], expected[1])


def test_isnan_returns_bool() -> None:
    value, _ = run(isnan(complex.of(float("nan"), 0)))
    assert value is True


def test_isnan_false() -> None:
    value, _ = run(isnan(complex.of(1, 2)))
    assert value is False


# --- constant -----------------------------------------------------------


def test_pi_constant() -> None:
    value, _ = run(pi)
    assert math.isclose(value, cmath.pi)


# --- async path ---------------------------------------------------------


def test_runs_on_async_path() -> None:
    value, _ = asyncio.run(arun(sqrt(complex.of(-1, 0))))
    assert cmath.isclose(value, cmath.sqrt(-1 + 0j))
