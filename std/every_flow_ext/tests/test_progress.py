"""Tests for progress tracking."""

import pytest

from every_flow import Seq, Var
from every_flow_ext import Progress, add_progress
from everyabc import Context, Flow


class Recorder(Flow):
    __slots__ = ("_label", "_log")

    def __init__(self, log, label="x"):
        super().__init__()
        self._log = log
        self._label = label

    def execute(self, ctx):
        self._log.append(self._label)


class Raiser(Flow):
    __slots__ = ("_exc",)

    def __init__(self, exc):
        super().__init__()
        self._exc = exc

    def execute(self, ctx):
        raise self._exc


def test_progress_success():
    started = Var(False)
    finished = Var(False)
    error = Var("")
    log = []

    p = Progress(Recorder(log, "work"), started=started, finished=finished, error=error)
    p.execute(Context())

    assert started.get() is True
    assert finished.get() is True
    assert error.get() == ""
    assert log == ["work"]


def test_progress_error():
    started = Var(False)
    finished = Var(False)
    error = Var("")

    p = Progress(Raiser(RuntimeError("oops")), started=started, finished=finished, error=error)

    with pytest.raises(RuntimeError, match="oops"):
        p.execute(Context())

    assert started.get() is True
    assert finished.get() is False
    assert error.get() == "oops"


def test_add_progress():
    log = []
    tree = Seq(Recorder(log, "a"), Recorder(log, "b"))
    result = add_progress(tree)

    # The Seq and its children should be wrapped
    assert isinstance(result, Progress)
    result.execute(Context())
    assert log == ["a", "b"]
