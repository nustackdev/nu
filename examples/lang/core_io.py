"""nu.core.io: console read/write through the stdio fabric, the v2 way.

``io.print`` writes to stdout (a Command - yields nothing), ``io.input`` reads a
line from stdin (a ScalarAction - yields the line). Both go through a hidden
singleton stdio Ref, so the caller never touches it. Streams are redirected here
by binding a ``StdioBackend`` on the Context, so the example is self-contained
(no real terminal). Each entry prints run result, term type, and the expression.
"""

from __future__ import annotations

import io as _io

import nu.core.io as io
from nu import Context, run


# Capture stdout and script stdin so the example runs without a real console.
out = _io.StringIO()
ctx = Context().bind(io.StdioBackend, io.StdioBackend(stdout=out, stdin=_io.StringIO("Gor\n")))

# 1. Print two values - a PrintCommand (writes "hello 42\n", yields None).
e1 = io.print("hello", 42)
print(run(e1, ctx)[0], type(e1), e1)

# 2. Read a line - an InputAction wrapped in a StrForm (yields "Gor").
e2 = io.input()
print(run(e2, ctx)[0], type(e2), e2)

# 3. Compose: greet using the captured name (string term feeding a print).
e3 = io.print("hi", io.input())
ctx3 = Context().bind(io.StdioBackend, io.StdioBackend(stdout=out, stdin=_io.StringIO("world\n")))
print(run(e3, ctx3)[0], type(e3), e3)

# Show what actually landed on the captured stdout.
print("--- captured stdout ---")
print(repr(out.getvalue()))
