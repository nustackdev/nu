"""Functional tests for ``nu.std.fractions`` - drive the Form through the engine.

Covers every modeling path: constructors and method calls (factory atoms),
property reads (core ``GetAttr``), arithmetic and comparison (core atoms;
Python does the real rational op), and the async path. Results are asserted
against the real ``fractions.Fraction`` for exact equality.
"""

from __future__ import annotations

import asyncio
from decimal import Decimal
from fractions import Fraction as PyFraction

from nu.lang.helpers import arun, run
from nu.std.fractions import Fraction


# --- constructors -------------------------------------------------------


def test_of() -> None:
    assert run(Fraction.of(1, 3))[0] == PyFraction(1, 3)


def test_of_reduces_to_lowest_terms() -> None:
    assert run(Fraction.of(2, 4))[0] == PyFraction(1, 2)


def test_from_str() -> None:
    assert run(Fraction.from_str("3/4"))[0] == PyFraction("3/4")


def test_from_float() -> None:
    assert run(Fraction.from_float(0.5))[0] == PyFraction.from_float(0.5)


def test_from_decimal() -> None:
    assert run(Fraction.from_decimal(Decimal("1.25")))[0] == PyFraction.from_decimal(
        Decimal("1.25")
    )


# --- property reads (core GetAttr) ---------------------------------


def test_numerator() -> None:
    assert run(Fraction.of(2, 4).numerator())[0] == 1


def test_denominator() -> None:
    assert run(Fraction.of(2, 4).denominator())[0] == 2


# --- arithmetic (core atoms; exact rational result) ---------------------


def test_add_is_exact() -> None:
    assert run(Fraction.of(1, 3) + Fraction.of(1, 6))[0] == PyFraction(1, 2)


def test_sub_is_exact() -> None:
    assert run(Fraction.of(3, 4) - Fraction.of(1, 4))[0] == PyFraction(1, 2)


def test_mul_is_exact() -> None:
    assert run(Fraction.of(2, 3) * Fraction.of(3, 4))[0] == PyFraction(1, 2)


def test_truediv_is_exact() -> None:
    assert run(Fraction.of(1, 2) / Fraction.of(1, 4))[0] == PyFraction(2, 1)


def test_floordiv() -> None:
    assert run(Fraction.of(7, 2) // Fraction.of(1, 1))[0] == PyFraction(7, 2) // PyFraction(1)


def test_mod() -> None:
    assert run(Fraction.of(7, 2) % Fraction.of(1, 1))[0] == PyFraction(7, 2) % PyFraction(1)


def test_pow() -> None:
    assert run(Fraction.of(2, 3) ** 2)[0] == PyFraction(4, 9)


def test_neg() -> None:
    assert run(-Fraction.of(1, 3))[0] == PyFraction(-1, 3)


def test_abs() -> None:
    assert run(abs(Fraction.of(-1, 3)))[0] == PyFraction(1, 3)


def test_pos() -> None:
    assert run(+Fraction.of(1, 3))[0] == PyFraction(1, 3)


# --- methods (factory atoms over unbound methods) -----------------------


def test_limit_denominator() -> None:
    value, _ = run(Fraction.from_float(3.141592653589793).limit_denominator(100))
    assert value == PyFraction.from_float(3.141592653589793).limit_denominator(100)


def test_as_integer_ratio() -> None:
    assert run(Fraction.of(3, 4).as_integer_ratio())[0] == (3, 4)


# --- comparison (core atoms) --------------------------------------------


def test_less_than() -> None:
    assert run(Fraction.of(1, 3) < Fraction.of(1, 2))[0] is True


def test_eq() -> None:
    assert run(Fraction.of(2, 4).eq(Fraction.of(1, 2)))[0] is True


def test_ne() -> None:
    assert run(Fraction.of(1, 3).ne(Fraction.of(1, 2)))[0] is True


# --- async path ---------------------------------------------------------


def test_runs_on_async_path() -> None:
    value, _ = asyncio.run(arun(Fraction.of(1, 3) + Fraction.of(1, 6)))
    assert value == PyFraction(1, 2)
