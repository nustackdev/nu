"""Tests for Parallel."""

import pytest

from every_flow import Parallel
from everyabc import Context, Flow

from .conftest import Raiser


async def test_parallel_all_execute():
    log = []

    class SafeRecorder(Flow):
        def __init__(self, log, label):
            super().__init__()
            self._log = log
            self._label = label

        async def execute(self, ctx):
            self._log.append(self._label)

    tree = Parallel(
        SafeRecorder(log, "a"),
        SafeRecorder(log, "b"),
        SafeRecorder(log, "c"),
    )
    await tree.execute(Context())
    assert sorted(log) == ["a", "b", "c"]


async def test_parallel_empty():
    tree = Parallel()
    await tree.execute(Context())  # no-op


async def test_parallel_propagates_exception():
    tree = Parallel(Raiser(RuntimeError("fail")))
    with pytest.raises(RuntimeError, match="fail"):
        await tree.execute(Context())
