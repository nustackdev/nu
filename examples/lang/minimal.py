"""Minimal nu sketches. One pattern per section. Each runs standalone.

The high-level ``run`` / ``arun`` entries take a description (Term),
attribute it, validate it, then evaluate it. No AttributedTerm juggling, no
ceremony - the three phases collapse into one call.

Bare Python values are auto-wrapped as ``Literal`` at construction, so
``Add(1, 2)`` reads the same as ``Add(Literal(1), Literal(2))``. The
explicit ``Literal`` shows up only where a value carries a sentinel that
would otherwise confuse the reader.

This is the pure scalar slice: literals, arithmetic, logic. Refs, streams,
commands and spans come online as the fabric pieces land.
"""

from __future__ import annotations

from nu.context import AttrRef, SetCmd
from nu.core import (
    Add,
    And,
    Div,
    Eq,
    Literal,
    Lt,
    Mul,
    Neg,
    Not,
    Or,
    Sub,
)
from nu.lang import EMPTY, INVALID
from nu.lang.helpers import run, run_in_loop


# 1. The trivial program: a bare value is wrapped as a Literal at the root.
value, _ = run(Literal(42))
assert value == 42
print(value)


# 2. Arithmetic: Add folds its operands. Bare ints get auto-wrapped.
value, _ = run(Add(1, 2, 3))
assert value == 6
print(value)


# 3. Nested expressions compose into one tree.
value, _ = run(Add(Mul(2, 3), Neg(1)))
assert value == 5
print(value)


# 4. Subtraction and division are binary; order matters.
value, _ = run(Sub(10, 3))
assert value == 7
print(value)
value, _ = run(Div(20, 4))
assert value == 5
print(value)


# 5. Comparisons yield booleans.
value, _ = run(Eq(2, 2))
assert value is True
print(value)
value, _ = run(Lt(1, 2))
assert value is True
print(value)


# 6. Boolean operators fold eagerly over their children.
value, _ = run(And(True, True, True))
assert value is True
print(value)
value, _ = run(Or(False, False, True))
assert value is True
print(value)
value, _ = run(Not(False))
assert value is True
print(value)


# 7. Sentinel propagation: an EMPTY operand collapses the query to INVALID.
#    Wrap sentinels in Literal explicitly - the auto-wrap would do the same,
#    but the explicit form makes the intent obvious.
value, _ = run(Add(Literal(EMPTY), 1))
assert value is INVALID
print(value)
value, _ = run(Mul(2, Literal(INVALID)))
assert value is INVALID
print(value)


# 8. ``run_in_loop`` drives the async path from sync code; no asyncio import.
value, _ = run_in_loop(Add(2, 3))
assert value == 5
print(value)


# 9. Validation fires before execution: a Command in a Query slot is refused.
try:
    run(Add(SetCmd(AttrRef("x"), 1), 2))
except Exception as e:
    print(e)

# 10. Mixed arithmetic and logic compose under one tree.
value, _ = run(
    And(
        Lt(0, 10),
        Eq(Add(2, 2), 4),
    ),
)
assert value is True
print(value)
