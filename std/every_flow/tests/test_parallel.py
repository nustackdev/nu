"""Tests for Parallel."""

import threading

import pytest

from every_flow import Parallel
from everyabc import Context

from .conftest import Raiser, Recorder


def test_parallel_all_execute():
    log = []
    lock = threading.Lock()

    class SafeRecorder(Recorder):
        def execute(self, ctx):
            with lock:
                self._log.append(self._label)

    tree = Parallel(
        SafeRecorder(log, "a"),
        SafeRecorder(log, "b"),
        SafeRecorder(log, "c"),
    )
    tree.execute(Context())
    assert sorted(log) == ["a", "b", "c"]


def test_parallel_empty():
    tree = Parallel()
    tree.execute(Context())  # no-op


def test_parallel_propagates_exception():
    tree = Parallel(Raiser(RuntimeError("fail")))
    with pytest.raises(RuntimeError, match="fail"):
        tree.execute(Context())
