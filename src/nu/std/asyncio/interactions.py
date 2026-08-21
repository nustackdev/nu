"""asyncio interactions - the async, non-blocking sleep.

``asyncio`` is mostly orchestration (``gather``, ``wait``, ``create_task``,
``run``) - and orchestration is what Nu Flows already are, so none of that belongs
here. What Nu can't express on its own is the one leaf primitive: suspend this
coroutine for a while without blocking the loop. That is ``asyncio.sleep``.

``AsyncioSleep`` runs for its effect (it suspends the coroutine) and produces no
real value. The clean home for that is a ``Command``, but a Command must write
through a Ref today (the ``command_has_write`` law), and suspending touches no
fabric - so until the io/effect model gives effects a non-Ref home, it rides as a
``ScalarQuery`` that yields ``None``. ``asyncio.sleep`` is an ``async def``, so the
factory infers ASYNC-ONLY - it declares ``requires_async=True`` and drives on
``acompile``; a sync ``run`` of it is refused by the async law (use ``arun``).
The sync, blocking sibling is ``nu.std.time.sleep``.
"""

from __future__ import annotations

import asyncio

from nu.factory import host


__all__ = ["AsyncioSleep"]


AsyncioSleep = host(asyncio.sleep, name="AsyncioSleep", requires_async=True)
