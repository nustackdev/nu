"""nu.std.datetime seed: the datetime classes as Forms, the v2 way.

Imported like the stdlib: ``from nu.std.datetime import date, timedelta, ...``.
Property reads reuse core GetAttrQuery; method calls reuse the shared
MethodCallQuery; arithmetic and comparison reuse the core atoms (Python does
the real op on the resolved values). Each entry prints run result, term type,
and the expression.
"""

from __future__ import annotations

from nu import Context, run
from nu.std.datetime import date, datetime, time, timedelta, timezone


ctx = Context()

# 1. Build a date, read a component (GetAttrQuery).
e1 = date.of(2026, 6, 30).month()
print(run(e1, ctx)[0], type(e1), e1)

# 2. Parse ISO, call a method (MethodCallQuery).
e2 = date.from_iso("2026-06-30").weekday()
print(run(e2, ctx)[0], type(e2), e2)

# 3. Date arithmetic: date + timedelta -> date (core AddQuery), then isoformat.
e3 = (date.of(2026, 6, 30) + timedelta.of(days=5)).isoformat()
print(run(e3, ctx)[0], type(e3), e3)

# 4. Date difference: date - date -> timedelta (core SubQuery), total_seconds.
e4 = (date.of(2026, 7, 10) - date.of(2026, 6, 30)).total_seconds()
print(run(e4, ctx)[0], type(e4), e4)

# 5. timedelta scaling and a comparison (core MulQuery + GtQuery).
e5 = (timedelta.of(hours=1) * 3).total_seconds()
print(run(e5, ctx)[0], type(e5), e5)

# 6. A datetime, replace a field (MethodCallQuery with kwargs), isoformat.
e6 = datetime.of(2026, 6, 30, 14, 30).replace(hour=9).isoformat()
print(run(e6, ctx)[0], type(e6), e6)

# 7. datetime split: .date() returns a date Form, then its year.
e7 = datetime.of(2026, 6, 30, 14, 30).date().year()
print(run(e7, ctx)[0], type(e7), e7)

# 8. time comparison via the < operator (core LtQuery).
e8 = time.of(9, 0) < time.of(17, 0)
print(run(e8, ctx)[0], type(e8), e8)

# 9. timezone: utc offset as a timedelta, total_seconds (should be 0.0).
e9 = timezone.utc().utcoffset().total_seconds()
print(run(e9, ctx)[0], type(e9), e9)
