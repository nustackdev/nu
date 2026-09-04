"""Nu surface for Python's ``asyncio`` module.

``asyncio`` is mostly orchestration - ``gather``, ``wait``, ``create_task``,
``run`` - and that is exactly what Nu Flows already are, so none of it is mirrored
here. The one leaf primitive Flows can't express is the non-blocking sleep, so
that is the whole surface::

    from nu.std.asyncio import sleep
    import nu.std.asyncio as asyncio     # then asyncio.sleep(1)

``sleep`` is an async-only, effect-only op that yields ``None`` (it suspends the
coroutine). It must run on a loop (``arun``); the sync, blocking sibling is
``nu.std.time.sleep``.
"""

from __future__ import annotations

from nu.std.asyncio.functions import sleep


__all__ = ["sleep"]
