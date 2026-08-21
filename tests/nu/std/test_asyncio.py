"""Functional tests for ``nu.std.asyncio`` - the non-blocking sleep.

``asyncio.sleep`` is async-only, so it drives through ``arun``; a sync ``run`` is
refused by the async law. Checks: the VOID yield, the elapsed suspension, and
the async-only tag.
"""

from __future__ import annotations

import asyncio

from nu.lang import compile
from nu.lang.helpers import arun, run
from nu.std.asyncio import sleep


def test_sleep_yields_none() -> None:
    value, _ = asyncio.run(arun(sleep(0.01)))
    assert value is None


def test_sleep_actually_suspends() -> None:
    async def drive() -> float:
        loop = asyncio.get_running_loop()
        start = loop.time()
        await arun(sleep(0.05))
        return loop.time() - start

    elapsed = asyncio.run(drive())
    assert elapsed >= 0.04


def test_sleep_is_async_only() -> None:
    # asyncio.sleep is an ``async def`` -> requires a loop; sync run is refused.
    try:
        run(sleep(0.0))
    except RuntimeError:
        pass
    else:
        msg = "expected sync run of an async-only atom to raise RuntimeError"
        raise AssertionError(msg)


def test_sleep_atom_tags() -> None:
    program = compile(sleep(0.0))
    assert program.attr((0,), "requires_async") is True
