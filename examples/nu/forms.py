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

from nu.context import (
    AnyAttrRef,
    BoolAttrRef,
    BytesAttrRef,
    DictAttrRef,
    FrozenSetAttrRef,
    IntAttrRef,
    ListAttrRef,
    NoneAttrRef,
    SetAttrRef,
    StrAttrRef,
    TupleAttrRef,
)
from nu.core import LiteralQuery
from nu.forms.collections import TupleForm
from nu.forms.primitives import AnyForm, BoolForm, BytesForm, FloatForm, IntForm, StrForm
from nu.lang import Context
from nu.lang.helpers import run


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


# ---------------------------------------------------------------------------
# 8. BytesAttrRef: upper(), slice, hex_(), startswith()
# ---------------------------------------------------------------------------

ctx = Context()
ctx.attrs["b"] = b"Hello World"

b = BytesAttrRef("b")

# .upper() -> BytesForm wrapping BytesUpperQuery
upper_expr = b.upper()
assert isinstance(upper_expr, BytesForm)
value_upper, _ = run(upper_expr, ctx)
assert value_upper == b"HELLO WORLD"
print(value_upper)  # b'HELLO WORLD'

# slice b[0:5] -> BytesForm via GetItemQuery + SliceQuery
slice_expr = b[0:5]
assert isinstance(slice_expr, BytesForm)
value_slice, _ = run(slice_expr, ctx)
assert value_slice == b"Hello"
print(value_slice)  # b'Hello'

# .hex_() -> StrForm wrapping HexQuery
hex_expr = b.hex_()
assert isinstance(hex_expr, StrForm)
value_hex, _ = run(hex_expr, ctx)
assert value_hex == "48656c6c6f20576f726c64"
print(value_hex)  # 48656c6c6f20576f726c64

# .startswith() -> BoolForm
sw_expr = b.startswith(b"Hello")
assert isinstance(sw_expr, BoolForm)
value_sw, _ = run(sw_expr, ctx)
assert value_sw is True
print(value_sw)  # True


# ---------------------------------------------------------------------------
# 9. BoolAttrRef: standalone and_() / or_() / not_()
# ---------------------------------------------------------------------------

ctx = Context()
ctx.attrs["flag"] = True

flag = BoolAttrRef("flag")

# .and_(False) -> BoolForm
and_expr = flag.and_(False)
assert isinstance(and_expr, BoolForm)
value_and, _ = run(and_expr, ctx)
assert value_and is False
print(value_and)  # False

# .or_(False) -> BoolForm; True OR False = True
or_expr = flag.or_(False)
assert isinstance(or_expr, BoolForm)
value_or, _ = run(or_expr, ctx)
assert value_or is True
print(value_or)  # True

# .not_() -> BoolForm; NOT True = False
not_expr = flag.not_()
assert isinstance(not_expr, BoolForm)
value_not, _ = run(not_expr, ctx)
assert value_not is False
print(value_not)  # False


# ---------------------------------------------------------------------------
# 10. AnyAttrRef: arithmetic and comparison stay typed
# ---------------------------------------------------------------------------

ctx = Context()
ctx.attrs["x"] = 42

x = AnyAttrRef("x")

# x + 8 -> AnyForm (dynamic result)
add_expr = x + 8
assert isinstance(add_expr, AnyForm)
value_add, _ = run(add_expr, ctx)
assert value_add == 50
print(value_add)  # 50

# x > 10 -> BoolForm (comparison narrows)
cmp_expr = x > 10
assert isinstance(cmp_expr, BoolForm)
value_cmp, _ = run(cmp_expr, ctx)
assert value_cmp is True
print(value_cmp)  # True


# ---------------------------------------------------------------------------
# 11. NoneAttrRef: logical ops on a None slot
# ---------------------------------------------------------------------------

ctx = Context()
ctx.attrs["z"] = None

z = NoneAttrRef("z")

# .not_() on None -> BoolForm; NOT None = True
not_expr = z.not_()
assert isinstance(not_expr, BoolForm)
value_not, _ = run(not_expr, ctx)
assert value_not is True
print(value_not)  # True

# .or_(True) -> BoolForm; None OR True = True
or_expr = z.or_(True)
assert isinstance(or_expr, BoolForm)
value_or, _ = run(or_expr, ctx)
assert value_or is True
print(value_or)  # True


# ---------------------------------------------------------------------------
# 12. SetAttrRef: union, intersection, issubset
# ---------------------------------------------------------------------------

ctx = Context()
ctx.attrs["st"] = {1, 2, 3}

st = SetAttrRef("st")

# .union() -> SetForm wrapping UnionQuery
union_expr = st.union(LiteralQuery({4, 5}))
value_union, _ = run(union_expr, ctx)
assert value_union == {1, 2, 3, 4, 5}
print(value_union)  # {1, 2, 3, 4, 5}

# .intersection() -> SetForm wrapping IntersectionQuery
inter_expr = st.intersection(LiteralQuery({2, 3, 4}))
value_inter, _ = run(inter_expr, ctx)
assert value_inter == {2, 3}
print(value_inter)  # {2, 3}

# .issubset() -> BoolForm
subset_expr = st.issubset(LiteralQuery({1, 2, 3, 4, 5}))
assert isinstance(subset_expr, BoolForm)
value_subset, _ = run(subset_expr, ctx)
assert value_subset is True
print(value_subset)  # True


# ---------------------------------------------------------------------------
# 13. FrozenSetAttrRef: immutable set — union works, no mutation
# ---------------------------------------------------------------------------

ctx = Context()
ctx.attrs["fs"] = frozenset({10, 20, 30})

fs = FrozenSetAttrRef("fs")

# .union() returns a new frozenset (FrozenSetForm wrapping UnionQuery)
fs_union_expr = fs.union(LiteralQuery(frozenset({40})))
value_fs_union, _ = run(fs_union_expr, ctx)
assert value_fs_union == frozenset({10, 20, 30, 40})
print(sorted(value_fs_union))  # [10, 20, 30, 40]

# .isdisjoint() -> BoolForm
disj_expr = fs.isdisjoint(LiteralQuery(frozenset({1, 2})))
assert isinstance(disj_expr, BoolForm)
value_disj, _ = run(disj_expr, ctx)
assert value_disj is True
print(value_disj)  # True


# ---------------------------------------------------------------------------
# 14. TupleAttrRef: indexing, first_elem, slice
# ---------------------------------------------------------------------------

ctx = Context()
ctx.attrs["tp"] = (10, 20, 30)

tp = TupleAttrRef("tp")

# tp[0] -> AnyForm wrapping GetItemQuery
elem_expr = tp[0]
assert isinstance(elem_expr, AnyForm)
value_elem, _ = run(elem_expr, ctx)
assert value_elem == 10
print(value_elem)  # 10

# .first_elem() -> AnyForm
first_expr = tp.first_elem()
assert isinstance(first_expr, AnyForm)
value_first, _ = run(first_expr, ctx)
assert value_first == 10
print(value_first)  # 10

# slice tp[0:2] -> TupleForm
slice_expr = tp[0:2]
assert isinstance(slice_expr, TupleForm)
value_slice, _ = run(slice_expr, ctx)
assert value_slice == (10, 20)
print(value_slice)  # (10, 20)


# ---------------------------------------------------------------------------
# 15. Sentinel checks: is_empty() and not_empty() -> BoolForm
# ---------------------------------------------------------------------------

# Missing ref: is_empty() -> True
missing_expr = IntAttrRef("missing").is_empty()
assert isinstance(missing_expr, BoolForm)
value_empty, _ = run(missing_expr, Context())
assert value_empty is True
print(value_empty)  # True

# Bound ref: not_empty() -> True
ctx = Context()
ctx.attrs["n"] = 5
ne_expr = IntAttrRef("n").not_empty()
assert isinstance(ne_expr, BoolForm)
value_ne, _ = run(ne_expr, ctx)
assert value_ne is True
print(value_ne)  # True


# ---------------------------------------------------------------------------
# convoluted 1: chained promotion + comparison: (n + 1.5) * 2 > 20 -> BoolForm
# ---------------------------------------------------------------------------

ctx = Context()
ctx.attrs["n"] = 10

n = IntAttrRef("n")
# n + 1.5 promotes to FloatForm; * 2 stays FloatForm; > 20 narrows to BoolForm
step1 = n + 1.5
assert isinstance(step1, FloatForm)
step2 = step1 * 2
assert isinstance(step2, FloatForm)
convo1 = step2 > 20
assert isinstance(convo1, BoolForm)
value_c1, _ = run(convo1, ctx)
assert value_c1 is True  # (10 + 1.5) * 2 = 23.0 > 20
print(value_c1)  # True


# ---------------------------------------------------------------------------
# convoluted 2: two int refs added, compared, then AND'd with a bool ref
# ---------------------------------------------------------------------------

ctx = Context()
ctx.attrs["a"] = 7
ctx.attrs["b"] = 5
ctx.attrs["flag"] = True

a = IntAttrRef("a")
b_ref = IntAttrRef("b")
flag = BoolAttrRef("flag")

# (a + b > 10) -> BoolForm; .and_(flag) -> BoolForm
convo2 = (a + b_ref > 10).and_(flag)
assert isinstance(convo2, BoolForm)
value_c2, _ = run(convo2, ctx)
assert value_c2 is True  # (7 + 5 = 12) > 10 AND True
print(value_c2)  # True


# ---------------------------------------------------------------------------
# convoluted 3: string build + predicate
# ---------------------------------------------------------------------------

ctx = Context()
ctx.attrs["s"] = "hello"

s = StrAttrRef("s")
# s.upper() -> StrForm; + "!" -> StrForm; .startswith("HELLO") -> BoolForm
convo3 = (s.upper() + "!").startswith("HELLO")
assert isinstance(convo3, BoolForm)
value_c3, _ = run(convo3, ctx)
assert value_c3 is True  # "hello".upper() + "!" = "HELLO!" startswith "HELLO"
print(value_c3)  # True


# ---------------------------------------------------------------------------
# convoluted 4: list first_elem used in arithmetic
# ---------------------------------------------------------------------------

ctx = Context()
ctx.attrs["xs"] = [5, 10, 15]

xs = ListAttrRef("xs")
# first_elem() -> AnyForm; + 3 -> AnyForm; evaluates to 5 + 3 = 8
first = xs.first_elem()
assert isinstance(first, AnyForm)
convo4 = first + 3
assert isinstance(convo4, AnyForm)
value_c4, _ = run(convo4, ctx)
assert value_c4 == 8
print(value_c4)  # 8


# ---------------------------------------------------------------------------
# convoluted 5: comparison of two arithmetic subtrees (n * 2 == n + n)
# ---------------------------------------------------------------------------

ctx = Context()
ctx.attrs["n"] = 7

n = IntAttrRef("n")
# (n * 2) == (n + n) => 14 == 14 => True; BoolForm via __eq__ on IntForm
lhs = n * 2
rhs = n + n
assert isinstance(lhs, IntForm)
assert isinstance(rhs, IntForm)
convo5 = lhs == rhs
assert isinstance(convo5, BoolForm)
value_c5, _ = run(convo5, ctx)
assert value_c5 is True
print(value_c5)  # True
