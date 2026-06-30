"""StdioBackend - the stdio fabric backend.

Simple dispatcher from StdioRef to stream handle.
Bound in Context to enable redirection and buffering.
"""

from __future__ import annotations

import sys
from typing import IO, TYPE_CHECKING


if TYPE_CHECKING:
    from .refs import StdioRef


__all__ = [
    "StdioBackend",
]


class StdioBackend:
    """Stdio fabric backend. Maps StdioRef to stream handles.

    Default streams are sys.stdout, sys.stderr, sys.stdin.
    Override in constructor for testing, buffering, or redirection.
    """

    __slots__ = ("stderr", "stdin", "stdout")

    def __init__(
        self,
        stdout: IO | None = None,
        stderr: IO | None = None,
        stdin: IO | None = None,
    ) -> None:
        self.stdout = stdout or sys.stdout
        self.stderr = stderr or sys.stderr
        self.stdin = stdin or sys.stdin

    def stream_for(self, ref: StdioRef) -> IO:
        """Return the stream for the given Ref."""
        return getattr(self, ref.name)

    def __repr__(self) -> str:
        return f"StdioBackend(stdout={self.stdout!r}, stderr={self.stderr!r}, stdin={self.stdin!r})"
