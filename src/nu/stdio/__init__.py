"""Stdio fabric - standard streams as modeled interactions.

Refs: StdioRef (STDOUT, STDERR, STDIN singletons)
Ops: StdioWrite (WRITE), StdioRead, StdioFlush (WRITE)
Backend: StdioBackend (bound in Context for redirection/buffering)
Buffered: BufferedStdio (ScopedOp transaction pattern)
"""

from .backend import StdioBackend
from .buffered import BufferedStdio
from .ops import StdioFlush, StdioRead, StdioWrite
from .refs import STDERR, STDIN, STDOUT, StdioRef


__all__ = [
    "STDERR",
    "STDIN",
    "STDOUT",
    "BufferedStdio",
    "StdioBackend",
    "StdioFlush",
    "StdioRead",
    "StdioRef",
    "StdioWrite",
]
