"""Functional tests for ``nu.std.fin`` - drive the Forms through the engine.

Covers both value types (``Percentage``, ``BasisPoint``): constructors (factory
atoms), conversions and application (factory atoms over native methods),
arithmetic and comparison (core atoms), plus the async path. Asserts against the
native dataclasses.
"""

from __future__ import annotations

from nu.lang.helpers import arun, run
from nu.std.fin import BasisPoint, Percentage
from nu.std.fin.native import BasisPoint as PyBasisPoint
from nu.std.fin.native import Percentage as PyPercentage


# --- percentage constructors ------------------------------------------------


def test_percentage_of() -> None:
    assert run(Percentage.of(75.5))[0] == PyPercentage(75.5)


def test_percentage_from_dec() -> None:
    assert run(Percentage.from_dec(0.755))[0] == PyPercentage(75.5)


def test_percentage_from_bps() -> None:
    assert run(Percentage.from_bps(7550))[0] == PyPercentage(75.5)


def test_percentage_from_ratio() -> None:
    assert run(Percentage.from_ratio(3, 4))[0] == PyPercentage(75.0)


# --- percentage conversions + application -----------------------------------


def test_percentage_to_dec() -> None:
    assert run(Percentage.of(75.5).to_dec())[0] == 0.755


def test_percentage_to_bps() -> None:
    assert run(Percentage.of(75.5).to_bps())[0] == 7550


def test_percentage_apply() -> None:
    assert run(Percentage.of(10).apply(200))[0] == 20.0


def test_percentage_add_to() -> None:
    assert run(Percentage.of(50).add_to(100))[0] == 150.0


def test_percentage_sub_from() -> None:
    assert run(Percentage.of(25).sub_from(100))[0] == 75.0


def test_percentage_is_valid() -> None:
    assert run(Percentage.of(50).is_valid())[0] is True
    assert run(Percentage.of(150).is_valid())[0] is False


def test_percentage_clamp() -> None:
    assert run(Percentage.of(150).clamp())[0] == PyPercentage(100.0)


# --- percentage arithmetic + comparison (core atoms) ------------------------


def test_percentage_add() -> None:
    assert run(Percentage.of(10) + Percentage.of(5))[0] == PyPercentage(15)


def test_percentage_mul() -> None:
    assert run(Percentage.of(10) * 2)[0] == PyPercentage(20)


def test_percentage_neg() -> None:
    assert run(-Percentage.of(10))[0] == PyPercentage(-10)


def test_percentage_comparison() -> None:
    assert run(Percentage.of(10) < Percentage.of(20))[0] is True
    assert run(Percentage.of(30) >= Percentage.of(30))[0] is True
    assert run(Percentage.of(10).eq(Percentage.of(10)))[0] is True
    assert run(Percentage.of(10).ne(Percentage.of(20)))[0] is True


# --- basis point ------------------------------------------------------------


def test_basis_point_of() -> None:
    assert run(BasisPoint.of(500))[0] == PyBasisPoint(500)


def test_basis_point_from_pct() -> None:
    assert run(BasisPoint.from_pct(5.0))[0] == PyBasisPoint(500)


def test_basis_point_from_dec() -> None:
    assert run(BasisPoint.from_dec(0.05))[0] == PyBasisPoint(500)


def test_basis_point_to_pct() -> None:
    assert run(BasisPoint.of(500).to_pct())[0] == 5.0


def test_basis_point_to_dec() -> None:
    assert run(BasisPoint.of(500).to_dec())[0] == 0.05


def test_basis_point_apply() -> None:
    assert run(BasisPoint.of(500).apply(1000))[0] == 50.0


def test_basis_point_add() -> None:
    assert run(BasisPoint.of(500) + BasisPoint.of(100))[0] == PyBasisPoint(600)


def test_basis_point_floordiv() -> None:
    assert run(BasisPoint.of(500) // 2)[0] == PyBasisPoint(250)


def test_basis_point_comparison() -> None:
    assert run(BasisPoint.of(100) < BasisPoint.of(200))[0] is True
    assert run(BasisPoint.of(500).eq(BasisPoint.of(500)))[0] is True


# --- async path -------------------------------------------------------------


async def test_async_percentage_apply() -> None:
    assert (await arun(Percentage.of(10).apply(200)))[0] == 20.0


async def test_async_basis_point_add() -> None:
    assert (await arun(BasisPoint.of(500) + BasisPoint.of(100)))[0] == PyBasisPoint(600)
