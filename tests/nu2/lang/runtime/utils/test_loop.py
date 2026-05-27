"""Unit tests for ``nu2.lang.runtime.utils.loop``.

Covers ``into_loop`` (sync->async bridge: runs a coroutine to completion,
spinning a fresh loop when needed) and ``safely_closing`` /
``safely_aclosing`` (idempotent close on iterables with optional ``close``
/ ``aclose``).
"""

from __future__ import annotations

import asyncio

import pytest

from nu2.lang.runtime.utils.loop import into_loop, safely_aclosing, safely_closing


async def _return(value: int) -> int:
    return value


def test_into_loop_runs_coroutine_and_returns_value() -> None:
    assert into_loop(_return(42)) == 42


def test_into_loop_raises_when_loop_running() -> None:
    async def inner() -> None:
        into_loop(_return(1))

    with pytest.raises(RuntimeError, match="into_loop called while a loop is running"):
        asyncio.run(inner())


class _Closable:
    def __init__(self) -> None:
        self.closed = False

    def __iter__(self):
        return iter(())

    def close(self) -> None:
        self.closed = True


def test_safely_closing_calls_close_on_closable() -> None:
    c = _Closable()
    with safely_closing(c) as it:
        assert it is c
    assert c.closed is True


def test_safely_closing_noop_on_plain_list() -> None:
    data = [1, 2, 3]
    with safely_closing(data) as it:
        assert list(it) == [1, 2, 3]


def test_safely_closing_calls_close_on_exception() -> None:
    c = _Closable()
    with pytest.raises(RuntimeError, match="boom"), safely_closing(c):
        raise RuntimeError("boom")
    assert c.closed is True


def test_safely_closing_closes_real_generator() -> None:
    finalized = []

    def gen():
        try:
            yield 1
            yield 2
            yield 3
        finally:
            finalized.append(True)

    g = gen()
    with safely_closing(g) as it:
        for value in it:
            if value == 1:
                break
    assert finalized == [True]


class _AClosable:
    def __init__(self) -> None:
        self.closed = False

    def __aiter__(self):
        return self

    async def __anext__(self):
        raise StopAsyncIteration

    async def aclose(self) -> None:
        self.closed = True


async def test_safely_aclosing_calls_aclose() -> None:
    a = _AClosable()
    async with safely_aclosing(a) as it:
        assert it is a
    assert a.closed is True


class _PlainAIter:
    def __aiter__(self):
        return self

    async def __anext__(self):
        raise StopAsyncIteration


async def test_safely_aclosing_noop_without_aclose() -> None:
    a = _PlainAIter()
    async with safely_aclosing(a) as it:
        assert it is a


async def test_safely_aclosing_calls_aclose_on_exception() -> None:
    a = _AClosable()
    with pytest.raises(RuntimeError, match="boom"):
        async with safely_aclosing(a):
            raise RuntimeError("boom")
    assert a.closed is True
