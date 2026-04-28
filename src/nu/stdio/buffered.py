"""BufferedStdio - transaction pattern for stdio.

Captures all writes in StringIO buffers. Flushes on success, discards on failure.

Migrated to a `Bracket` Span: single body slot at 0. When constructed with
multiple children, they're wrapped in a `Sequential` automatically so the
Bracket's single-body contract holds.
"""

from __future__ import annotations

from io import StringIO
from typing import TYPE_CHECKING, Any, ClassVar

from nu.terms.flow import Sequential
from nu.terms.span import Bracket
from nu.terms.types import Mode

from .backend import StdioBackend


if TYPE_CHECKING:
    from nu.context import Context


__all__ = [
    "BufferedStdio",
]


class BufferedStdio(Bracket):
    """Buffer stdio writes. Flush on success, discard on failure.

    before(): creates StdioBackend with StringIO buffers, rebinds in Context.
    after(): flushes buffers to real streams (commit).
    after_failure(): discards buffers (rollback).

    stdin passes through unbuffered (can't rollback reads).
    """

    body_slot: ClassVar[int] = 0
    support: ClassVar[frozenset[Mode]] = frozenset({Mode.SYNC, Mode.ASYNC})

    def __init__(self, *children: Any) -> None:  # noqa: ANN401
        # Wrap multiple children in a Sequential so Bracket's single-body
        # invariant holds.
        if len(children) == 1:
            super().__init__(children[0])
        else:
            super().__init__(Sequential(*children))
        self._real_backend: StdioBackend | None = None
        self._buffered_backend: StdioBackend | None = None

    def before(self, ctx: Context) -> Context:
        """Set up buffered streams."""
        if ctx.has(StdioBackend):
            self._real_backend = ctx.get(StdioBackend)
        else:
            self._real_backend = StdioBackend()

        # Buffered backend - stdin passes through (can't rollback reads).
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
        args = ", ".join(repr(c) for c in self._children)
        return f"BufferedStdio({args})"
