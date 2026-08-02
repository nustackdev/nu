"""nu.std.asyncio seed: the one leaf primitive Flows can't express - a sleep.

Imported like the stdlib: ``from nu.std.asyncio import sleep`` (or
``import nu.std.asyncio as asyncio``). ``asyncio`` orchestration (gather, wait,
run) maps onto Nu Flows, so the only atom here is the non-blocking ``sleep``. It
is async-only: it must run on a loop, so this example drives it with ``arun``,
not ``run``. It yields nothing (a Command). Each entry prints run result, term
type, and the expression.
"""

from __future__ import annotations

import asyncio as _asyncio

from nu import Context, arun
from nu.std.asyncio import sleep


ctx = Context()

# 1. Suspend for 10ms without blocking the loop - a None_ (AsyncioSleep atom).
e1 = sleep(0.01)
print(_asyncio.run(arun(e1, ctx))[0], type(e1), e1)
