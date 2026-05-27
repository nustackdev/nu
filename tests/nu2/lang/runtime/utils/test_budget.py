"""Unit tests for ``nu2.lang.runtime.utils.budget``.

Covers ``Budget`` -- per-execution resources. Cheap construction at
``max_parallel == 1``, thread-pool allocation otherwise, async semaphore
in async mode, idempotent close.
"""

from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor

import pytest

from nu2.lang.runtime.utils.budget import Budget


def test_default_construction() -> None:
    b = Budget()
    assert b.max_parallel == 1
    assert b.async_mode is False
    assert b.thread_pool is None
    assert b.async_sem is None


@pytest.mark.parametrize("bad", [0, -1, -100])
def test_max_parallel_below_one_raises(bad: int) -> None:
    with pytest.raises(ValueError, match="max_parallel must be >= 1"):
        Budget(bad)


def test_parallel_sync_mode_allocates_pool_only() -> None:
    b = Budget(4)
    try:
        assert isinstance(b.thread_pool, ThreadPoolExecutor)
        assert b.async_sem is None
    finally:
        b.close()


async def test_parallel_async_mode_allocates_pool_and_sem() -> None:
    b = Budget(4, async_mode=True)
    try:
        assert isinstance(b.thread_pool, ThreadPoolExecutor)
        assert isinstance(b.async_sem, asyncio.Semaphore)
    finally:
        b.close()


def test_close_shuts_down_pool() -> None:
    b = Budget(4)
    assert b.thread_pool is not None
    b.close()
    assert b.thread_pool is None


def test_close_is_idempotent() -> None:
    b = Budget(4)
    b.close()
    b.close()
    assert b.thread_pool is None


def test_close_on_zero_concurrency_budget() -> None:
    b = Budget()
    b.close()
    assert b.thread_pool is None


def test_context_manager_returns_self_and_closes() -> None:
    with Budget(4) as b:
        assert isinstance(b, Budget)
        assert b.thread_pool is not None
    assert b.thread_pool is None


@pytest.mark.parametrize(
    ("max_parallel", "async_mode"),
    [(1, False), (4, False), (4, True)],
)
def test_repr_contains_fields(max_parallel: int, async_mode: bool) -> None:
    b = Budget(max_parallel, async_mode=async_mode)
    try:
        r = repr(b)
        assert f"max_parallel={max_parallel}" in r
        assert f"async_mode={async_mode}" in r
    finally:
        b.close()
