"""Functional tests for ``nu.std.decimal`` - drive the Form through the engine.

Covers every modeling path: constructors (factory atoms), arithmetic and
comparison (core atoms), method calls returning various Forms, predicates, and
the async path. Asserts against real ``decimal.Decimal`` with exact equality to
show precision is preserved (``Decimal('0.1') + Decimal('0.2') == Decimal('0.3')``).
"""

from __future__ import annotations

import asyncio
from decimal import Decimal as PyDecimal

from nu.lang.helpers import arun, run
from nu.std.decimal import Decimal


# --- constructors (factory atoms) ---------------------------------------


def test_of_from_str_is_exact() -> None:
    assert run(Decimal.of("0.1"))[0] == PyDecimal("0.1")


def test_of_from_int_is_exact() -> None:
    assert run(Decimal.of(7))[0] == PyDecimal("7")


def test_from_float() -> None:
    assert run(Decimal.from_float(0.5))[0] == PyDecimal.from_float(0.5)


# --- arithmetic (core atoms; Python does the real Decimal op) -----------


def test_add_is_exact() -> None:
    # the headline: binary float would give 0.30000000000000004
    assert run(Decimal.of("0.1") + Decimal.of("0.2"))[0] == PyDecimal("0.3")


def test_sub() -> None:
    assert run(Decimal.of("0.3") - Decimal.of("0.1"))[0] == PyDecimal("0.2")


def test_mul() -> None:
    assert run(Decimal.of("1.5") * Decimal.of("2"))[0] == PyDecimal("3.0")


def test_truediv() -> None:
    assert run(Decimal.of("1") / Decimal.of("4"))[0] == PyDecimal("0.25")


def test_pow() -> None:
    assert run(Decimal.of("2") ** Decimal.of("10"))[0] == PyDecimal("1024")


def test_neg_and_abs() -> None:
    assert run(-Decimal.of("5"))[0] == PyDecimal("-5")
    assert run(abs(Decimal.of("-5")))[0] == PyDecimal("5")


# --- method calls (factory atoms over unbound methods) ------------------


def test_quantize() -> None:
    value, _ = run(Decimal.of("3.14159").quantize(Decimal.of("0.01")))
    assert value == PyDecimal("3.14")


def test_sqrt() -> None:
    assert run(Decimal.of("4").sqrt())[0] == PyDecimal("2")


def test_normalize() -> None:
    assert run(Decimal.of("1.2300").normalize())[0] == PyDecimal("1.23")


def test_compare_returns_decimal() -> None:
    assert run(Decimal.of("1").compare(Decimal.of("2")))[0] == PyDecimal("-1")


def test_adjusted_returns_int() -> None:
    assert run(Decimal.of("123.45").adjusted())[0] == PyDecimal("123.45").adjusted()


def test_as_integer_ratio_returns_tuple() -> None:
    assert run(Decimal.of("1.5").as_integer_ratio())[0] == (3, 2)


# --- predicates (bool) --------------------------------------------------


def test_is_finite() -> None:
    assert run(Decimal.of("10").is_finite())[0] is True


def test_is_zero() -> None:
    assert run(Decimal.of("0").is_zero())[0] is True
    assert run(Decimal.of("1").is_zero())[0] is False


# --- comparison (core atoms) --------------------------------------------


def test_less_than() -> None:
    assert run(Decimal.of("1.5") < Decimal.of("2.5"))[0] is True


def test_eq() -> None:
    assert run(Decimal.of("0.10").eq(Decimal.of("0.1")))[0] is True


# --- async path ---------------------------------------------------------


def test_runs_on_async_path() -> None:
    value, _ = asyncio.run(arun(Decimal.of("0.1") + Decimal.of("0.2")))
    assert value == PyDecimal("0.3")
