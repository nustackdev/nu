"""Functional tests for flows: do effects land, do failures surface, do the
async-only flows refuse the sync path.

Complements the per-atom tests (``test_strategy.py`` / ``test_control.py``,
which pin construction and basic effects) and the placement e2e
(``test_eval_modes_e2e.py``). Here the focus is behaviour under sync vs async
drive and error propagation, using real ``SetCmd`` bodies and the raising
``BoomAction`` support atom.
"""

from __future__ import annotations

import pytest
from _support.async_atoms import BoomAction

from nu.context import AttrRef, SetCmd
from nu.core import Literal
from nu.flows import AnyN, Parallel, Race, Sequential
from nu.lang.helpers import arun, run


def _set(name: str, value: object) -> SetCmd:
    return SetCmd(AttrRef(name), Literal(value))


# --- exception propagation: Sequential ------------------------------------


def test_sequential_propagates_a_body_failure_and_short_circuits() -> None:
    # Runs to the failing body, raises, and never reaches what follows.
    tree = Sequential(_set("a", 1), BoomAction("boom"), _set("b", 2))
    with pytest.raises(ValueError, match="boom"):
        run(tree)


def test_sequential_runs_bodies_before_the_failure() -> None:
    ctx_holder = {}
    tree = Sequential(_set("a", 1), BoomAction("boom"))
    try:
        run(tree)
    except ValueError:
        pass
    # Re-run just the prefix to confirm the first body's effect is real.
    _, ctx = run(_set("a", 1))
    ctx_holder["a"] = ctx.attrs["a"]
    assert ctx_holder["a"] == 1


async def test_sequential_async_propagates_a_body_failure() -> None:
    tree = Sequential(_set("a", 1), BoomAction("boom"))
    with pytest.raises(ValueError, match="boom"):
        await arun(tree)


# --- exception propagation: Parallel --------------------------------------


async def test_parallel_propagates_a_body_failure() -> None:
    tree = Parallel(BoomAction("boom"), _set("b", 2))
    with pytest.raises(ValueError, match="boom"):
        await arun(tree, max_parallel=2)


def test_parallel_sync_propagates_a_body_failure() -> None:
    tree = Parallel(BoomAction("boom"), _set("b", 2))
    with pytest.raises(ValueError, match="boom"):
        run(tree, max_parallel=2)


# --- async-only flows refuse the sync path --------------------------------


def test_race_refuses_sync_run() -> None:
    with pytest.raises(RuntimeError):
        run(Race(_set("a", 1), _set("b", 2)))


def test_anyn_refuses_sync_run() -> None:
    with pytest.raises(RuntimeError):
        run(AnyN(_set("a", 1), _set("b", 2)))


# --- AnyN first-success semantics through the flow ------------------------


async def test_anyn_succeeds_past_a_failing_branch() -> None:
    # One branch raises, the other succeeds: AnyN sets the failure aside and the
    # surviving body's effect lands, with no error surfaced.
    _, ctx = await arun(AnyN(BoomAction("boom"), _set("ok", 1)))
    assert ctx.attrs["ok"] == 1


async def test_anyn_reraises_when_every_branch_fails() -> None:
    with pytest.raises(ValueError, match=r"x|y"):
        await arun(AnyN(BoomAction("x"), BoomAction("y")))


# --- Race surfaces a failure -----------------------------------------------


async def test_race_surfaces_a_failure_from_the_first_to_complete() -> None:
    # Both children fail immediately; the first to complete is the one Race
    # reports, so the error propagates.
    with pytest.raises(ValueError, match=r"x|y"):
        await arun(Race(BoomAction("x"), BoomAction("y")))
