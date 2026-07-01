"""nu.std.time seed: the process clock and a blocking sleep, the v2 way.

Imported like the stdlib: ``from nu.std.time import monotonic, sleep`` (or
``import nu.std.time as time``). ``time`` is a function module, so the surface is
free functions - no central class. Clock reads are non-deterministic (they read
the clock), so output varies run to run; ``sleep`` yields nothing (a Command) and
just blocks. Each entry prints run result, term type, and the expression.
"""

from __future__ import annotations

from nu import Context, run
from nu.std.time import monotonic, perf_counter, sleep, time, time_ns


ctx = Context()

# 1. Seconds since the epoch - a FloatForm (TimeTime atom, non-deterministic).
e1 = time()
print(run(e1, ctx)[0], type(e1), e1)

# 2. A monotonic clock read - a FloatForm (TimeMonotonic atom).
e2 = monotonic()
print(run(e2, ctx)[0], type(e2), e2)

# 3. The high-resolution timer - a FloatForm (TimePerfCounter atom).
e3 = perf_counter()
print(run(e3, ctx)[0], type(e3), e3)

# 4. Nanoseconds since the epoch - an IntForm (TimeTimeNs atom).
e4 = time_ns()
print(run(e4, ctx)[0], type(e4), e4)

# 5. Block for 10ms - a NoneForm (TimeSleep Command; yields None, sync-only).
e5 = sleep(0.01)
print(run(e5, ctx)[0], type(e5), e5)
