"""Tests for the arm book: births, deaths, restarts, the done set, the first error."""

from __future__ import annotations

import asyncio

import pytest
from _support.reactive import settle_loop, until

from nu.core.reactive._arms import ArmBook


def _book(
    log: list, plan: dict | None = None, gate: asyncio.Event | None = None, **kw: object
) -> ArmBook:
    """A book whose arms park, finish or raise as ``plan`` says (parking by default).

    ``gate`` ties two arms together: an ``unwind-slowly`` arm sets it when
    cancelled and yields a few ticks before it goes, a ``finish-at-gate`` or
    ``boom-at-gate`` arm waits on it and then finishes or raises.
    """
    plan = plan or {}

    async def arm(key: object) -> None:
        log.append(("start", key))
        try:
            what = plan.get(key, "park")
            if what == "boom":
                msg = f"boom {key}"
                raise ValueError(msg)
            if what == "park":
                await asyncio.Event().wait()
            if what == "unwind-raises":
                try:
                    await asyncio.Event().wait()
                except asyncio.CancelledError:
                    msg = f"unwind {key}"
                    raise RuntimeError(msg) from None
            if what == "unwind-slowly":
                try:
                    await asyncio.Event().wait()
                except asyncio.CancelledError:
                    gate.set()  # type: ignore[union-attr]
                    for _ in range(3):
                        await asyncio.sleep(0)
                    raise
            if what in ("finish-at-gate", "boom-at-gate"):
                await gate.wait()  # type: ignore[union-attr]
                if what == "boom-at-gate":
                    msg = f"boom {key}"
                    raise ValueError(msg)
        finally:
            log.append(("end", key))

    return ArmBook(lambda key: asyncio.ensure_future(arm(key)), **kw)


def _starts(log: list, key: object) -> int:
    return log.count(("start", key))


# ---------------------------------------------------------------------------
# align: births and deaths
# ---------------------------------------------------------------------------


async def test_align_births_the_missing_and_kills_the_gone() -> None:
    log: list = []
    book = _book(log)
    await book.align(["a", "b"])
    await settle_loop()
    assert sorted(log) == [("start", "a"), ("start", "b")]
    await book.align(["a"])
    assert ("end", "b") in log
    assert ("end", "a") not in log
    assert set(book.arms) == {"a"}
    await book.drain()
    assert ("end", "a") in log
    assert book.arms == {}


async def test_align_gives_a_repeated_id_one_arm() -> None:
    log: list = []
    book = _book(log)
    await book.align(["a", "a", "a"])
    await settle_loop()
    assert _starts(log, "a") == 1
    await book.drain()


async def test_unhashable_ids_are_a_clear_error_naming_the_owner() -> None:
    book = _book([], owner="Flow")
    with pytest.raises(TypeError, match=r"Flow: ids must be hashable, got list \[1\]"):
        await book.align(["a", [1]])
    assert book.arms == {}


async def test_a_death_that_finishes_while_a_sibling_death_unwinds_is_settled() -> None:
    """Two ids leave in one pass; the second ends on its own while the first is drained."""
    log, gate = [], asyncio.Event()
    book = _book(log, {"a": "unwind-slowly", "b": "finish-at-gate"}, gate, once=True)
    await book.align(["a", "b"])
    await settle_loop()
    await book.align([])
    assert sorted(log) == [("end", "a"), ("end", "b"), ("start", "a"), ("start", "b")]
    assert book.arms == {}
    assert book.done == set()
    assert not book.failed
    await book.align(["b"])
    await until(lambda: _starts(log, "b") == 2)
    await book.drain()


async def test_a_death_that_raises_while_a_sibling_death_unwinds_is_the_error() -> None:
    """Same shape, but the arm that ends on its own raises: its error is what align raises."""
    log, gate = [], asyncio.Event()
    book = _book(log, {"a": "unwind-slowly", "b": "boom-at-gate"}, gate, once=True)
    await book.align(["a", "b"])
    await settle_loop()
    with pytest.raises(ValueError, match="boom b"):
        await book.align([])
    assert sorted(log) == [("end", "a"), ("end", "b"), ("start", "a"), ("start", "b")]
    assert book.arms == {}
    assert book.failed
    with pytest.raises(ValueError, match="boom b"):
        await book.align(["c"])
    assert ("start", "c") not in log


# ---------------------------------------------------------------------------
# rule 1: the done set
# ---------------------------------------------------------------------------


async def test_once_keeps_a_finished_arm_finished_until_its_id_leaves() -> None:
    log: list = []
    book = _book(log, {"a": "finish"}, once=True)
    await book.align(["a"])
    await until(lambda: ("end", "a") in log)
    await settle_loop()
    assert book.arms == {}
    assert book.done == {"a"}
    await book.align(["a"])
    assert _starts(log, "a") == 1
    await book.align([])
    assert book.done == set()
    await book.align(["a"])
    await until(lambda: _starts(log, "a") == 2)
    await book.drain()


async def test_once_settles_an_arm_that_finished_on_the_same_tick() -> None:
    """A done callback lands a tick late; the sweep inside align must not wait for it."""
    log: list = []
    book = _book(log, {"a": "finish"}, once=True)
    await book.align(["a"])
    await until(lambda: ("end", "a") in log)
    await book.align(["a"])
    assert _starts(log, "a") == 1
    assert book.done == {"a"}


async def test_without_once_a_finished_arm_is_born_again_on_the_next_align() -> None:
    log: list = []
    book = _book(log, {"a": "finish"})
    await book.align(["a"])
    await until(lambda: ("end", "a") in log)
    await settle_loop()
    assert book.done is None
    await book.align(["a"])
    await until(lambda: _starts(log, "a") == 2)
    await book.drain()


async def test_a_killed_arm_is_not_done() -> None:
    log: list = []
    book = _book(log, once=True)
    await book.align(["a"])
    await settle_loop()
    await book.align([])
    assert ("end", "a") in log
    assert book.done == set()
    await book.align(["a"])
    await until(lambda: _starts(log, "a") == 2)
    await book.drain()


# ---------------------------------------------------------------------------
# restart
# ---------------------------------------------------------------------------


async def test_restart_kills_and_rebirths_only_that_arm() -> None:
    log: list = []
    book = _book(log)
    await book.align(["a", "b"])
    await settle_loop()
    await book.restart("a")
    assert ("end", "a") in log
    await until(lambda: _starts(log, "a") == 2)
    assert ("end", "b") not in log
    assert log.index(("end", "a")) < log.index(("start", "a"), 1)
    assert set(book.arms) == {"a", "b"}
    await book.drain()


async def test_restart_births_an_id_that_has_no_arm_and_a_done_one() -> None:
    log: list = []
    book = _book(log, {"a": "finish"}, once=True)
    await book.restart("a")
    await until(lambda: ("end", "a") in log)
    await settle_loop()
    assert book.done == {"a"}
    await book.restart("a")
    assert book.done == set()
    await until(lambda: _starts(log, "a") == 2 and log.count(("end", "a")) == 2)


# ---------------------------------------------------------------------------
# rule 2: the first error
# ---------------------------------------------------------------------------


async def test_wait_returns_what_it_awaited_when_no_arm_raises() -> None:
    book = _book([])
    assert await book.wait(asyncio.sleep(0, "value")) == "value"
    assert not book.failed


async def test_wait_raises_the_arm_error_and_cancels_the_wait() -> None:
    log: list = []
    book = _book(log, {"a": "boom", "b": "park"})
    await book.align(["a", "b"])
    cancelled = asyncio.Event()

    async def forever() -> None:
        try:
            await asyncio.Event().wait()
        finally:
            cancelled.set()

    with pytest.raises(ValueError, match="boom a"):
        await book.wait(forever())
    assert cancelled.is_set()
    assert book.failed
    assert set(book.arms) == {"b"}
    with pytest.raises(ValueError, match="boom a"):
        await book.wait(asyncio.sleep(0))
    await book.drain()
    assert ("end", "b") in log


async def test_align_raises_an_error_it_finds_and_starts_nothing_after_it() -> None:
    log: list = []
    book = _book(log, {"a": "boom"})
    await book.align(["a"])
    await until(lambda: ("end", "a") in log)
    with pytest.raises(ValueError, match="boom a"):
        await book.align(["a", "b"])
    assert ("start", "b") not in log
    with pytest.raises(ValueError, match="boom a"):
        await book.restart("b")
    assert ("start", "b") not in log


async def test_the_first_error_wins() -> None:
    log: list = []
    book = _book(log, {"a": "boom", "b": "boom"})
    await book.align(["a"])
    await until(lambda: ("end", "a") in log)
    await settle_loop()
    book.sweep()
    assert book.failed
    with pytest.raises(ValueError, match="boom a"):
        await book.align(["b"])


async def test_a_death_that_raises_on_unwind_is_an_error() -> None:
    log: list = []
    book = _book(log, {"a": "unwind-raises"})
    await book.align(["a"])
    await settle_loop()
    with pytest.raises(RuntimeError, match="unwind a"):
        await book.align([])
    assert book.failed
    assert book.arms == {}


async def test_a_wait_cancelled_from_outside_drains_what_it_awaited() -> None:
    book = _book([])
    drained = asyncio.Event()

    async def forever() -> None:
        try:
            await asyncio.Event().wait()
        finally:
            drained.set()

    task = asyncio.ensure_future(book.wait(forever()))
    await settle_loop()
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert drained.is_set()
    assert not book.failed
