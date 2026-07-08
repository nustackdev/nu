"""Inspecting a Nu tree: render it, and annotate it with logging.

``nu.inspect`` has two halves. ``render_nu`` turns any Nu term into a printable
box-tree, one node per line, each kind color coded. The ``annotate_*`` rewrites
layer logging onto a tree without changing what it computes - a step tracker
around each ``Sequential`` child, per-attempt hooks on each ``Retry`` - all
logged through the stderr side of the stdio fabric.
"""

from __future__ import annotations

import io

from nu import Context, run
from nu.core import AddQuery, LiteralQuery, MulQuery, PrintCommand
from nu.core.io import STDOUT, StdioBackend, input
from nu.flows import Sequential
from nu.inspect import annotate_steps, render_nu, set_logger_name


# 1. A pure arithmetic tree: Query nodes (green, dotted), Literal leaves (cyan).
expr = AddQuery(MulQuery(2, 3), LiteralQuery(4))
print(render_nu(expr, as_="plain"))
print()


# 2. An effectful, composed program: a Flow (blue) over a Command (red) that
#    writes through a StdioRef (yellow), then an Action (bright red) that reads.
program = Sequential(
    PrintCommand(STDOUT, LiteralQuery("enter your name:")),
    input(),
)
print(render_nu(program, as_="plain"))
print()


# 3. The default form emits ANSI color for a terminal.
print(render_nu(expr))
print()


# 4. annotate_steps wraps each step in a logging Bracket; set_logger_name
#    retargets the logger. We capture stderr so the demo is self-contained.
steps = Sequential(PrintCommand(STDOUT, LiteralQuery("a")), PrintCommand(STDOUT, LiteralQuery("b")))
annotated = set_logger_name(annotate_steps(steps), "demo")
err = io.StringIO()
run(annotated, ctx=Context().bind(StdioBackend, StdioBackend(stderr=err)))
print(err.getvalue(), end="")
