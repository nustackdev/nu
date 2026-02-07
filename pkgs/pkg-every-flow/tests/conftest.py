"""Test helpers for every_flow."""

from everybase import Context, Flow


class Recorder(Flow):
    """Flow leaf that records execution by appending to a log list."""

    def __init__(self, log, label="x"):
        super().__init__()
        self._log = log
        self._label = label

    async def execute(self, ctx):
        self._log.append(self._label)


class Raiser(Flow):
    """Flow leaf that raises a given exception."""

    def __init__(self, exc=None):
        super().__init__()
        self._exc = exc or RuntimeError("boom")

    async def execute(self, ctx):
        raise self._exc


def ctx():
    """Create an empty context."""
    return Context()
