"""time interactions - one factory binding per host call.

``time`` is a function module: free functions over the process clock, no central
class. Core can't read a clock or block, so each call is a new atom bound straight
to the ``time.*`` callable.

Two flavors here:

- **clock reads** (``time``, ``monotonic``, ``perf_counter``, ``process_time`` and
  their ``*_ns`` twins) are ``ScalarQuery`` atoms. Every one is NON-DETERMINISTIC
  - it reads the clock, so it declares ``deterministic=False`` and must not be
  constant-folded (fold gate = pure AND deterministic).
- **``sleep``** runs for its effect (it blocks) and produces no real value. The
  clean home for that is a ``Command``, but a Command must write through a Ref
  today (the ``command_has_write`` law), and blocking touches no fabric. So until
  the io/effect model gives effects a non-Ref home, ``sleep`` rides as a
  ``ScalarQuery`` that yields ``None``. It is SYNC-ONLY - blocking a running event
  loop is exactly what it must not do - so it declares ``async_affinity=False``
  (the async sibling is ``nu.std.asyncio.sleep``). It also declares
  ``deterministic=False`` as a conservative fold-guard: its value (``None``) is
  constant, but its real-world effect (wall-clock advance) must never be folded
  away.
"""

from __future__ import annotations

import time as _time

from nu.lang import ScalarQueryFactory


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

TimeTime = ScalarQueryFactory("TimeTime", _time.time, deterministic=False)
TimeMonotonic = ScalarQueryFactory("TimeMonotonic", _time.monotonic, deterministic=False)
TimePerfCounter = ScalarQueryFactory("TimePerfCounter", _time.perf_counter, deterministic=False)
TimeProcessTime = ScalarQueryFactory("TimeProcessTime", _time.process_time, deterministic=False)

# --- clock reads (int nanoseconds) ------------------------------------------

TimeTimeNs = ScalarQueryFactory("TimeTimeNs", _time.time_ns, deterministic=False)
TimeMonotonicNs = ScalarQueryFactory("TimeMonotonicNs", _time.monotonic_ns, deterministic=False)
TimePerfCounterNs = ScalarQueryFactory(
    "TimePerfCounterNs", _time.perf_counter_ns, deterministic=False
)

# --- blocking sleep (sync-only, effect-only) --------------------------------

TimeSleep = ScalarQueryFactory("TimeSleep", _time.sleep, async_affinity=False, deterministic=False)
