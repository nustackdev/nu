"""BufferedStdio - transaction pattern for stdio.

Captures all writes in StringIO buffers. Flushes on success, discards on failure.
"""

from __future__ import annotations

from io import StringIO
from typing import TYPE_CHECKING

from nu.terms.op import ScopedOp

from .backend import StdioBackend


if TYPE_CHECKING:
    from nu.context import Context


__all__ = [
    "BufferedStdio",
]


class BufferedStdio(ScopedOp):
    """Buffer stdio writes. Flush on success, discard on failure.

    before(): creates StdioBackend with StringIO buffers, rebinds in Context.
    after(): flushes buffers to real streams (commit).
    after_failure(): discards buffers (rollback).

    stdin passes through unbuffered (can't rollback reads).
    """

    def __init__(self, *children: object) -> None:
        super().__init__(*children)
        self._real_backend: StdioBackend | None = None
        self._buffered_backend: StdioBackend | None = None

    def before(self, ctx: Context) -> Context:
        """Set up buffered streams."""
        # Get real backend (or create default from sys streams)
        if ctx.has(StdioBackend):
            self._real_backend = ctx.get(StdioBackend)
        else:
            self._real_backend = StdioBackend()

        # Create buffered backend - stdin passes through
        self._buffered_backend = StdioBackend(
            stdout=StringIO(),
            stderr=StringIO(),
            stdin=self._real_backend.stdin,
        )
        return ctx.bind(StdioBackend, self._buffered_backend)

    def after(self, ctx: Context) -> None:
        """Flush buffers to real streams (commit)."""
        if self._real_backend is None or self._buffered_backend is None:
            return

        stdout_content = self._buffered_backend.stdout.getvalue()
        stderr_content = self._buffered_backend.stderr.getvalue()

        if stdout_content:
            self._real_backend.stdout.write(stdout_content)
        if stderr_content:
            self._real_backend.stderr.write(stderr_content)

    def after_failure(self, ctx: Context, error: BaseException) -> None:
        """Discard buffers (rollback). Nothing written to real streams."""
        self._real_backend = None
        self._buffered_backend = None

    def __repr__(self) -> str:
        args = ", ".join(repr(c) for c in self.children)
        return f"BufferedStdio({args})"
