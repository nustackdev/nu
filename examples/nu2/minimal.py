"""Minimal nu2 sketches. One pattern per section. Each runs standalone.

The high-level ``run`` / ``arun`` entries take a description (Symbol),
compile it, validate it, then evaluate it. No Program juggling, no
ceremony - the three phases collapse into one call.

This is the pure scalar slice: Literal, arithmetic, logic. Refs, streams,
commands and spans come online as the fabric pieces land.
"""

from __future__ import annotations

from nu2.core import Add, And, Div, Eq, Literal, Lt, Mul, Neg, Not, Or, Set, Sub
from nu2.lang import EMPTY, INVALID, Ref
from nu2.runtime import run, run_in_loop


# 1. The trivial program: a Literal yields its value.
value, _ = run(Literal(42))
assert value == 42


# 2. Arithmetic: Add folds its operands.
value, _ = run(Add(Literal(1), Literal(2), Literal(3)))
assert value == 6


# 3. Nested expressions compose into one tree.
value, _ = run(Add(Mul(Literal(2), Literal(3)), Neg(Literal(1))))
assert value == 5


# 4. Subtraction and division are binary; order matters.
value, _ = run(Sub(Literal(10), Literal(3)))
assert value == 7
value, _ = run(Div(Literal(20), Literal(4)))
assert value == 5


# 5. Comparisons yield booleans.
value, _ = run(Eq(Literal(2), Literal(2)))
assert value is True
value, _ = run(Lt(Literal(1), Literal(2)))
assert value is True


# 6. Boolean operators fold eagerly over their children.
value, _ = run(And(Literal(True), Literal(True), Literal(True)))
assert value is True
value, _ = run(Or(Literal(False), Literal(False), Literal(True)))
assert value is True
value, _ = run(Not(Literal(False)))
assert value is True


# 7. Sentinel propagation: an EMPTY operand collapses the query to INVALID.
value, _ = run(Add(Literal(EMPTY), Literal(1)))
assert value is INVALID
value, _ = run(Mul(Literal(2), Literal(INVALID)))
assert value is INVALID


# 8. ``run_in_loop`` drives the async path from sync code; no asyncio import.
value, _ = run_in_loop(Add(Literal(2), Literal(3)))
assert value == 5


# 9. Validation fires before execution: a Command in a Query slot is refused.
run(Add(Set(Ref("x"), Literal(1)), Literal(2)))

# 10. Mixed arithmetic and logic compose under one tree.
value, _ = run(
    And(
        Lt(Literal(0), Literal(10)),
        Eq(Add(Literal(2), Literal(2)), Literal(4)),
    ),
)
assert value is True
