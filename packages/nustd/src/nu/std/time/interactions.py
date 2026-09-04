"""time interactions - one factory binding per host call.

``time`` is a function module: free functions over the process clock, no central
class. Core can't read a clock or block, so each call is a new atom bound straight
to the ``time.*`` callable.

Two flavors here:

- **clock reads** (``time``, ``monotonic``, ``perf_counter``, ``process_time``
  and their ``*_ns`` twins) are ``ScalarQuery`` atoms that read the clock.
- **``sleep``** runs for its effect (it blocks) and produces no real value. The
  clean home for that is a ``Command``, but a Command must write through a Ref
  today (the ``command_has_write`` law), and blocking touches no fabric. So until
  the io/effect model gives effects a non-Ref home, ``sleep`` rides as a
  ``ScalarQuery`` that yields ``None``. It is SYNC-ONLY - blocking a running event
  loop is exactly what it must not do - so it declares ``async_affinity=False``
  (the async sibling is ``nu.std.asyncio.sleep``).
"""

from __future__ import annotations

import time as _time

from nu.factory import host


__all__ = [
    "TimeMonotonic",
    "TimeMonotonicNs",
    "TimePerfCounter",
    "TimePerfCounterNs",
    "TimeProcessTime",
    "TimeSleep",
    "TimeTime",
    "TimeTimeNs",
]


# --- clock reads (float seconds) --------------------------------------------

TimeTime = host(_time.time, name="TimeTime")
TimeMonotonic = host(_time.monotonic, name="TimeMonotonic")
TimePerfCounter = host(_time.perf_counter, name="TimePerfCounter")
TimeProcessTime = host(_time.process_time, name="TimeProcessTime")

# --- clock reads (int nanoseconds) ------------------------------------------

TimeTimeNs = host(_time.time_ns, name="TimeTimeNs")
TimeMonotonicNs = host(_time.monotonic_ns, name="TimeMonotonicNs")
TimePerfCounterNs = host(_time.perf_counter_ns, name="TimePerfCounterNs")

# --- blocking sleep (sync-only, effect-only) --------------------------------

TimeSleep = host(_time.sleep, name="TimeSleep", async_affinity=False)
