"""Tests for progress tracking."""

import pytest

from eb_flow import Seq, Var
from eb_flow_ext import Progress, add_progress
from everybase import Context, Flow


class Recorder(Flow):
    def __init__(self, log, label="x"):
        super().__init__()
        self._log = log
        self._label = label

    async def execute(self, ctx):
        self._log.append(self._label)


class Raiser(Flow):
    def __init__(self, exc):
        super().__init__()
        self._exc = exc

    async def execute(self, ctx):
        raise self._exc


async def test_progress_success():
    started = Var(False)
    finished = Var(False)
    error = Var("")
    log = []

    p = Progress(Recorder(log, "work"), started=started, finished=finished, error=error)
    await p.execute(Context())

    assert started.get() is True
    assert finished.get() is True
    assert error.get() == ""
    assert log == ["work"]


async def test_progress_error():
    started = Var(False)
    finished = Var(False)
    error = Var("")

    p = Progress(Raiser(RuntimeError("oops")), started=started, finished=finished, error=error)

    with pytest.raises(RuntimeError, match="oops"):
        await p.execute(Context())

    assert started.get() is True
    assert finished.get() is False
    assert error.get() == "oops"


async def test_add_progress():
    log = []
    tree = Seq(Recorder(log, "a"), Recorder(log, "b"))
    result = add_progress(tree)

    # The Seq and its children should be wrapped
    assert isinstance(result, Progress)
    await result.execute(Context())
    assert log == ["a", "b"]
