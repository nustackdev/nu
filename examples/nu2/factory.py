"""InteractionFactory: declare Nu atoms from plain Python callables.

Most atoms in ``nu2.core`` look the same: resolve the children, call a
Python function, return the result. ``InteractionFactory`` collapses the
boilerplate into one call. Pass a base kind, a name, and a function, and
out comes a real ``Nu`` subclass with sync + async thunks, sentinel
short-circuit, and any declared attributes you supply.
"""

from __future__ import annotations

import asyncio

from nu2.core import Literal
from nu2.lang import Command, Effect, InteractionFactory, ScalarQuery
from nu2.lang.helpers import arun, run
from nu2.lang.sentinels import EMPTY, INVALID


# 1. A bare arithmetic atom: one line, behaves like a hand-written ScalarQuery.
Add = InteractionFactory(
    ScalarQuery, "Add", lambda *xs: sum(xs), commutative=True, associative=True
)
value, _ = run(Add(1, 2, 3))
assert value == 6
print(value)


# 2. Built atoms compose with each other and with core atoms.
Mul = InteractionFactory(ScalarQuery, "Mul", lambda a, b: a * b, commutative=True, associative=True)
Neg = InteractionFactory(ScalarQuery, "Neg", lambda x: -x)
value, _ = run(Add(Mul(2, 3), Neg(1)))
assert value == 5
print(value)


# 3. Sentinel propagation is on by default: any EMPTY/INVALID child collapses
#    the call to INVALID without invoking the function.
calls: list[object] = []
Track = InteractionFactory(ScalarQuery, "Track", lambda x: calls.append(x) or x)
value, _ = run(Track(Literal(EMPTY)))
assert value is INVALID
assert calls == []  # function never ran
print(value)


# 4. Opt out of propagation if the function wants to see sentinels raw.
def keep(a: object, b: object) -> object:
    return (a, b)


Pair = InteractionFactory(ScalarQuery, "Pair", keep, propagate_sentinels=False)
value, _ = run(Pair(Literal(EMPTY), Literal(INVALID)))
assert value == (EMPTY, INVALID)
print(value)


# 5. Async callables are detected; the class declares requires_async and only
#    the async path is wired.
async def adouble(x: int) -> int:
    await asyncio.sleep(0)
    return x * 2


Double = InteractionFactory(ScalarQuery, "Double", adouble)
assert Double.attributes["requires_async"].value is True
value, _ = asyncio.run(arun(Double(21)))
assert value == 42
print(value)


# 6. Commands carry effect declarations the same way hand-written ones do.
#    The function runs for its side effect; the thunk returns None.
log: list[tuple[object, ...]] = []


def record(*args: object) -> None:
    log.append(args)


Log = InteractionFactory(Command, "Log", record, own_effects={0: Effect.WRITE})
print(Log.attributes["own_effects"].value)


# 7. Custom attributes pass through declared. Beyond effects, attributes like
#    commutative / associative / idempotent reach the schema unchanged.
Max = InteractionFactory(
    ScalarQuery,
    "Max",
    lambda *xs: max(xs),
    commutative=True,
    associative=True,
    idempotent=True,
)
assert Max.attributes["idempotent"].value is True
value, _ = run(Max(3, 7, 1, 5))
assert value == 7
print(value)
