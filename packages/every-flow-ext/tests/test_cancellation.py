"""Tests for cancellation."""

import pytest

from every_flow import ForRange, Seq, Var, While
from every_flow_ext import CancelledError, CheckCancellation, add_cancellation_checks
from everyabc import Context, Flow


class Recorder(Flow):
    def __init__(self, log, label="x"):
        super().__init__()
        self._log = log
        self._label = label

    async def execute(self, ctx):
        self._log.append(self._label)


async def test_check_cancellation_not_cancelled():
    cancelled = Var(False)
    check = CheckCancellation(cancelled)
    await check.execute(Context())  # should not raise


async def test_check_cancellation_raises():
    cancelled = Var(True)
    check = CheckCancellation(cancelled)
    with pytest.raises(CancelledError):
        await check.execute(Context())


async def test_add_cancellation_checks_while():
    cancelled = Var(False)
    counter = Var(3)

    class Decrement(Flow):
        def __init__(self, log):
            super().__init__()
            self._log = log

        async def execute(self, ctx):
            self._log.append("tick")
            counter.set(counter.get() - 1)
            if counter.get() <= 1:
                cancelled.set(True)

    log = []
    tree = While(counter, Decrement(log))
    tree_with_checks = add_cancellation_checks(tree, cancelled)

    with pytest.raises(CancelledError):
        await tree_with_checks.execute(Context())

    # Should have executed body twice before cancellation check caught it
    assert len(log) == 2


async def test_add_cancellation_checks_for_range():
    cancelled = Var(False)
    log = []

    class CancelAfterTwo(Flow):
        def __init__(self, log):
            super().__init__()
            self._log = log

        async def execute(self, ctx):
            self._log.append("step")
            if len(self._log) >= 2:
                cancelled.set(True)

    tree = ForRange(0, 10, CancelAfterTwo(log))
    tree_with_checks = add_cancellation_checks(tree, cancelled)

    with pytest.raises(CancelledError):
        await tree_with_checks.execute(Context())

    assert len(log) == 2


async def test_add_cancellation_checks_preserves_seq():
    cancelled = Var(False)
    log = []
    tree = Seq(Recorder(log, "a"), Recorder(log, "b"))
    result = add_cancellation_checks(tree, cancelled)
    await result.execute(Context())
    assert log == ["a", "b"]  # Seq unaffected
