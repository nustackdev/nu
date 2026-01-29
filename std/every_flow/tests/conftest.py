"""Test helpers for every_flow."""

from everyabc import Context, Flow


class Recorder(Flow):
    """Flow leaf that records execution by appending to a log list."""

    __slots__ = ("_label", "_log")

    def __init__(self, log, label="x"):
        super().__init__()
        self._log = log
        self._label = label

    def execute(self, ctx):
        self._log.append(self._label)


class Raiser(Flow):
    """Flow leaf that raises a given exception."""

    __slots__ = ("_exc",)

    def __init__(self, exc=None):
        super().__init__()
        self._exc = exc or RuntimeError("boom")

    def execute(self, ctx):
        raise self._exc


def ctx():
    """Create an empty context."""
    return Context()
