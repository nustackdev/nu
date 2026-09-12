"""Execution tests for the logical atoms in ``nu.core.logical``.

Compile small programs over Literal leaves and check the value each logical
atom yields, the bool-coercing short-circuit semantics of And / Or, and
sentinel propagation to INVALID.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from nu.core.logical import And as And
from nu.core.logical import Not as Not
from nu.core.logical import Or as Or
from nu.core.logical import ToBool as Bool
from nu.lang import EMPTY, INVALID, ScalarQuery
from nu.lang.helpers import aeval, compile, eval
from nu.lang.literal import Literal


if TYPE_CHECKING:
    from collections.abc import Callable

    from nu.lang.runtime import Runtime


class Boom(ScalarQuery):
    """An atom that raises the moment it is evaluated."""

    def _compile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        def thunk(rt: Runtime) -> object:
            raise AssertionError("short-circuited child was evaluated")

        return thunk

    def _acompile(self, nid: int, children: tuple[Callable, ...]) -> Callable:
        async def athunk(rt: Runtime) -> object:
            raise AssertionError("short-circuited child was evaluated")

        return athunk


def _eval(term: object) -> object:
    value, _ = eval(compile(term))
    return value


async def _aeval(term: object) -> object:
    value, _ = await aeval(compile(term))
    return value


# --- And -----------------------------------------------------------------


def test_and_conjoins():
    assert _eval(And(Literal(True), Literal(True))) is True
    assert _eval(And(Literal(True), Literal(False))) is False
    assert _eval(And(Literal(False), Literal(False))) is False


def test_and_is_variadic():
    assert _eval(And(Literal(True), Literal(True), Literal(True))) is True
    assert _eval(And(Literal(True), Literal(True), Literal(False))) is False


def test_and_coerces_to_bool_not_an_operand():
    # Python `1 and 2` is 2; Nu And yields a plain bool.
    assert _eval(And(Literal(1), Literal(2))) is True
    assert _eval(And(Literal(0), Literal(2))) is False


# --- Or ------------------------------------------------------------------


def test_or_disjoins():
    assert _eval(Or(Literal(False), Literal(True))) is True
    assert _eval(Or(Literal(False), Literal(False))) is False
    assert _eval(Or(Literal(True), Literal(True))) is True


def test_or_is_variadic():
    assert _eval(Or(Literal(False), Literal(False), Literal(True))) is True
    assert _eval(Or(Literal(False), Literal(False), Literal(False))) is False


def test_or_coerces_to_bool_not_an_operand():
    # Python `0 or 3` is 3; Nu Or yields a plain bool.
    assert _eval(Or(Literal(0), Literal(3))) is True
    assert _eval(Or(Literal(0), Literal(0))) is False


# --- Not -----------------------------------------------------------------


def test_not_negates():
    assert _eval(Not(Literal(False))) is True
    assert _eval(Not(Literal(True))) is False
    assert _eval(Not(Literal(0))) is True
    assert _eval(Not(Literal(7))) is False


# --- Bool ----------------------------------------------------------------


def test_bool_casts_truthiness():
    assert _eval(Bool(Literal(7))) is True
    assert _eval(Bool(Literal(0))) is False
    assert _eval(Bool(Literal(""))) is False
    assert _eval(Bool(Literal("x"))) is True


# --- async mirrors sync --------------------------------------------------


def test_aeval_mirrors_eval():
    assert asyncio.run(_aeval(And(Literal(True), Literal(True)))) is True
    assert asyncio.run(_aeval(Or(Literal(False), Literal(True)))) is True
    assert asyncio.run(_aeval(Not(Literal(False)))) is True
    assert asyncio.run(_aeval(Bool(Literal(7)))) is True


# --- sentinel propagation ------------------------------------------------


def test_a_sentinel_operand_collapses_to_invalid():
    assert _eval(And(Literal(True), Literal(EMPTY))) is INVALID
    assert _eval(Or(Literal(False), Literal(INVALID))) is INVALID
    assert _eval(Not(Literal(EMPTY))) is INVALID
    assert _eval(Bool(Literal(INVALID))) is INVALID
    assert asyncio.run(_aeval(And(Literal(EMPTY), Literal(True)))) is INVALID


# --- short-circuit -------------------------------------------------------


def test_and_does_not_evaluate_children_past_the_first_falsy_one():
    assert _eval(And(Literal(False), Boom())) is False
    assert _eval(And(Literal(True), Literal(0), Boom())) is False
    assert asyncio.run(_aeval(And(Literal(False), Boom()))) is False


def test_or_does_not_evaluate_children_past_the_first_truthy_one():
    assert _eval(Or(Literal(True), Boom())) is True
    assert _eval(Or(Literal(False), Literal(1), Boom())) is True
    assert asyncio.run(_aeval(Or(Literal(True), Boom()))) is True


def test_short_circuit_beats_sentinel_poisoning():
    # The sentinel sits in a child that is never reached, so it never fires.
    assert _eval(And(Literal(False), Literal(INVALID))) is False
    assert _eval(And(Literal(False), Literal(EMPTY))) is False
    assert _eval(Or(Literal(True), Literal(INVALID))) is True
    assert _eval(Or(Literal(True), Literal(EMPTY))) is True
    assert asyncio.run(_aeval(And(Literal(False), Literal(INVALID)))) is False
    assert asyncio.run(_aeval(Or(Literal(True), Literal(INVALID)))) is True


def test_a_sentinel_in_an_evaluated_child_still_collapses():
    assert _eval(And(Literal(INVALID), Literal(False))) is INVALID
    assert _eval(And(Literal(True), Literal(EMPTY), Literal(False))) is INVALID
    assert _eval(Or(Literal(EMPTY), Literal(True))) is INVALID
    assert _eval(Or(Literal(False), Literal(INVALID), Literal(True))) is INVALID


def test_no_children_yields_the_identity():
    assert _eval(And()) is True
    assert _eval(Or()) is False
    assert asyncio.run(_aeval(And())) is True
    assert asyncio.run(_aeval(Or())) is False


def test_and_guards_an_unsafe_child():
    # The motivating case: the guard must keep the guarded work from running.
    assert _eval(And(Literal(""), Boom())) is False
    assert _eval(Or(Not(Literal("")), Boom())) is True
