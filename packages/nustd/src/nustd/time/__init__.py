"""Nu surface for Python's ``time`` module.

``time`` is a function module - module-level functions over the process clock,
no central class - so the Nu surface mirrors that: free functions (``time``,
``monotonic``, ``perf_counter``, ``sleep``, ...). Two layers behind it:
``functions`` (the typed wrappers) and ``interactions`` (the atoms each wrapper
builds). Import it the way you would the stdlib::

    from nustd.time import monotonic, sleep
    import nustd.time as time     # then time.monotonic()

Every clock read reads the process clock. ``sleep`` is a sync-only,
effect-only op that yields ``None`` (it blocks); the async sleep lives in
``nustd.asyncio``.
"""

from __future__ import annotations

from nustd.time.functions import (
    monotonic,
    monotonic_ns,
    perf_counter,
    perf_counter_ns,
    process_time,
    sleep,
    time,
    time_ns,
)


__all__ = [
    "monotonic",
    "monotonic_ns",
    "perf_counter",
    "perf_counter_ns",
    "process_time",
    "sleep",
    "time",
    "time_ns",
]
