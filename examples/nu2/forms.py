"""Typed authoring surface: forms, typed refs, and operator overloading.

``IntAttrRef`` / ``StrAttrRef`` / ``ListAttrRef`` / ``DictAttrRef`` are
``AttrRef`` subclasses with a ``Form`` mixin bolted on. The MRO puts
``AttrRef`` first so the ref resolves through ``ctx.attrs``; the form mixin
adds every operator the underlying Python type supports. The result is a
composable expression tree with full type-narrowing via overloads.

Each section seeds a ``Context``, builds an expression, and evaluates it with
``run(expr, ctx)``. No asyncio - everything here is sync.
"""

from __future__ import annotations

from nu2.context import DictAttrRef, IntAttrRef, ListAttrRef, StrAttrRef
from nu2.lang import Context
from nu2.lang.helpers import run


# ---------------------------------------------------------------------------
# 1. Typed ref read + arithmetic: IntAttrRef + 3 evaluates to 13
# ---------------------------------------------------------------------------

# IntAttrRef("n") reads ctx.attrs["n"] at runtime. The + operator is wired
# on IntForm and returns a new IntForm wrapping AddQuery(ref, 3).
ctx = Context()
ctx.attrs["n"] = 10

n = IntAttrRef("n")
value, _ = run(n + 3, ctx)
assert value == 13
print(value)  # 13


# ---------------------------------------------------------------------------
# 2. int/float promotion: int * int -> IntForm; int + float -> FloatForm
# ---------------------------------------------------------------------------

ctx = Context()
ctx.attrs["n"] = 10

n = IntAttrRef("n")

value_mul, _ = run(n * 2, ctx)
assert value_mul == 20
print(value_mul)  # 20

value_float, _ = run(n + 1.5, ctx)
assert value_float == 11.5
print(value_float)  # 11.5


# ---------------------------------------------------------------------------
# 3. Comparison yielding BoolForm: (n > 5) -> True
# ---------------------------------------------------------------------------

ctx = Context()
ctx.attrs["n"] = 10

n = IntAttrRef("n")
value, _ = run(n > 5, ctx)
assert value is True
print(value)  # True


# ---------------------------------------------------------------------------
# 4. String ops: upper() and slice
# ---------------------------------------------------------------------------

ctx = Context()
ctx.attrs["s"] = "hello world"

s = StrAttrRef("s")

value_upper, _ = run(s.upper(), ctx)
assert value_upper == "HELLO WORLD"
print(value_upper)  # HELLO WORLD

# Slice syntax: s[0:5] uses StrForm.__getitem__ with a Python slice object.
value_slice, _ = run(s[0:5], ctx)
assert value_slice == "hello"
print(value_slice)  # hello


# ---------------------------------------------------------------------------
# 5. Boolean logic: (n > 5).and_(n < 100) -> True
# ---------------------------------------------------------------------------

ctx = Context()
ctx.attrs["n"] = 10

n = IntAttrRef("n")
# n > 5 returns BoolForm; .and_() is BoolForm.and_() which wraps AndQuery.
value, _ = run((n > 5).and_(n < 100), ctx)
assert value is True
print(value)  # True


# ---------------------------------------------------------------------------
# 6. List typed ref: xs[0] -> 3
# ---------------------------------------------------------------------------

ctx = Context()
ctx.attrs["xs"] = [3, 1, 2]

xs = ListAttrRef("xs")

# __getitem__ with an int index delegates to GetItemQuery.
value, _ = run(xs[0], ctx)
assert value == 3
print(value)  # 3

# first_elem() is the form-level helper for the same.
value_first, _ = run(xs.first_elem(), ctx)
assert value_first == 3
print(value_first)  # 3


# ---------------------------------------------------------------------------
# 7. Dict typed ref: .get() and .keys()
# ---------------------------------------------------------------------------

ctx = Context()
ctx.attrs["d"] = {"x": 1, "y": 2, "z": 3}

d = DictAttrRef("d")

# .get("x") returns AnyForm wrapping GetQuery(d, "x").
value_get, _ = run(d.get("x"), ctx)
assert value_get == 1
print(value_get)  # 1

# .keys() returns DictKeysForm wrapping KeysQuery(d); evaluates to the view.
value_keys_raw, _ = run(d.keys(), ctx)
assert set(value_keys_raw) == {"x", "y", "z"}  # type: ignore[call-overload]
print(sorted(value_keys_raw))  # type: ignore[call-overload]  # ['x', 'y', 'z']

# .copy() returns DictForm wrapping CopyQuery(d); evaluates to a plain dict.
value_copy, _ = run(d.copy(), ctx)
assert value_copy == {"x": 1, "y": 2, "z": 3}
print(value_copy)  # {'x': 1, 'y': 2, 'z': 3}
