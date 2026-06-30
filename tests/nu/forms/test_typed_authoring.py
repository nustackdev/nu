"""Unit tests for the typed-authoring surface (typed AttrRef + form operators).

For each representative expression, tests assert BOTH:
- ``isinstance(expr, ExpectedForm)`` — type-narrowing reflected in the runtime
  form class at compose time.
- the evaluated value via run/eval with a seeded Context.

Groups: int arithmetic + promotion, comparison/logic, str ops, bytes, list,
dict, set, sentinel, and the 5 convoluted compositions.
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
from nu.forms.collections import ListForm, TupleForm
from nu.forms.primitives import AnyForm, BoolForm, BytesForm, FloatForm, IntForm, StrForm
from nu.lang import Context
from nu.lang.helpers import run


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def ctx(**kw: object) -> Context:
    """Build a Context pre-populated with keyword attrs."""
    c = Context()
    for k, v in kw.items():
        c.attrs[k] = v
    return c


def val(expr: object, c: Context | None = None) -> object:
    """Evaluate expr and return the value only."""
    return run(expr, c or Context())[0]


# ---------------------------------------------------------------------------
# Int arithmetic + promotion
# ---------------------------------------------------------------------------


def test_int_add_int_narrows_to_int_form():
    n = IntAttrRef("n")
    assert isinstance(n + 3, IntForm)


def test_int_add_int_evaluates():
    assert val(IntAttrRef("n") + 3, ctx(n=10)) == 13


def test_int_mul_int_narrows_to_int_form():
    n = IntAttrRef("n")
    assert isinstance(n * 2, IntForm)


def test_int_mul_int_evaluates():
    assert val(IntAttrRef("n") * 2, ctx(n=7)) == 14


def test_int_add_float_promotes_to_float_form():
    n = IntAttrRef("n")
    assert isinstance(n + 1.5, FloatForm)


def test_int_add_float_evaluates():
    assert val(IntAttrRef("n") + 1.5, ctx(n=10)) == 11.5


def test_int_sub_evaluates():
    assert val(IntAttrRef("n") - 4, ctx(n=10)) == 6


def test_int_pow_evaluates():
    assert val(IntAttrRef("n") ** 3, ctx(n=2)) == 8


# ---------------------------------------------------------------------------
# Comparison / logic
# ---------------------------------------------------------------------------


def test_int_gt_narrows_to_bool_form():
    assert isinstance(IntAttrRef("n") > 5, BoolForm)


def test_int_gt_evaluates_true():
    assert val(IntAttrRef("n") > 5, ctx(n=10)) is True


def test_int_gt_evaluates_false():
    assert val(IntAttrRef("n") > 5, ctx(n=3)) is False


def test_int_eq_narrows_to_bool_form():
    assert isinstance(IntAttrRef("n") == 10, BoolForm)


def test_int_lt_evaluates():
    assert val(IntAttrRef("n") < 20, ctx(n=10)) is True


def test_bool_and_narrows_to_bool_form():
    assert isinstance(BoolAttrRef("f").and_(True), BoolForm)


def test_bool_and_evaluates():
    assert val(BoolAttrRef("f").and_(False), ctx(f=True)) is False


def test_bool_or_evaluates():
    assert val(BoolAttrRef("f").or_(True), ctx(f=False)) is True


def test_bool_not_evaluates():
    assert val(BoolAttrRef("f").not_(), ctx(f=True)) is False


def test_chained_and_gt_evaluates():
    n = IntAttrRef("n")
    assert val((n > 5).and_(n < 100), ctx(n=10)) is True


# ---------------------------------------------------------------------------
# Str ops + slicing
# ---------------------------------------------------------------------------


def test_str_upper_narrows_to_str_form():
    assert isinstance(StrAttrRef("s").upper(), StrForm)


def test_str_upper_evaluates():
    assert val(StrAttrRef("s").upper(), ctx(s="hello")) == "HELLO"


def test_str_lower_evaluates():
    assert val(StrAttrRef("s").lower(), ctx(s="WORLD")) == "world"


def test_str_add_narrows_to_str_form():
    assert isinstance(StrAttrRef("s") + "_x", StrForm)


def test_str_add_evaluates():
    assert val(StrAttrRef("s") + " world", ctx(s="hello")) == "hello world"


def test_str_slice_narrows_to_str_form():
    assert isinstance(StrAttrRef("s")[0:3], StrForm)


def test_str_slice_evaluates():
    assert val(StrAttrRef("s")[0:5], ctx(s="hello world")) == "hello"


def test_str_startswith_narrows_to_bool_form():
    assert isinstance(StrAttrRef("s").startswith("he"), BoolForm)


def test_str_startswith_evaluates():
    assert val(StrAttrRef("s").startswith("HI"), ctx(s="HI there")) is True


def test_str_endswith_evaluates():
    assert val(StrAttrRef("s").endswith("!"), ctx(s="hello!")) is True


# ---------------------------------------------------------------------------
# Bytes
# ---------------------------------------------------------------------------


def test_bytes_upper_narrows_to_bytes_form():
    assert isinstance(BytesAttrRef("b").upper(), BytesForm)


def test_bytes_upper_evaluates():
    assert val(BytesAttrRef("b").upper(), ctx(b=b"hello")) == b"HELLO"


def test_bytes_slice_narrows_to_bytes_form():
    assert isinstance(BytesAttrRef("b")[0:3], BytesForm)


def test_bytes_slice_evaluates():
    assert val(BytesAttrRef("b")[0:5], ctx(b=b"Hello World")) == b"Hello"


def test_bytes_hex_narrows_to_str_form():
    assert isinstance(BytesAttrRef("b").hex_(), StrForm)


def test_bytes_hex_evaluates():
    assert val(BytesAttrRef("b").hex_(), ctx(b=b"\xff")) == "ff"


def test_bytes_startswith_narrows_to_bool_form():
    assert isinstance(BytesAttrRef("b").startswith(b"Hi"), BoolForm)


def test_bytes_startswith_evaluates():
    assert val(BytesAttrRef("b").startswith(b"Hello"), ctx(b=b"Hello World")) is True


# ---------------------------------------------------------------------------
# AnyAttrRef
# ---------------------------------------------------------------------------


def test_any_add_narrows_to_any_form():
    assert isinstance(AnyAttrRef("x") + 1, AnyForm)


def test_any_add_evaluates():
    assert val(AnyAttrRef("x") + 8, ctx(x=42)) == 50


def test_any_gt_narrows_to_bool_form():
    assert isinstance(AnyAttrRef("x") > 0, BoolForm)


def test_any_gt_evaluates():
    assert val(AnyAttrRef("x") > 10, ctx(x=42)) is True


# ---------------------------------------------------------------------------
# NoneAttrRef
# ---------------------------------------------------------------------------


def test_none_not_narrows_to_bool_form():
    assert isinstance(NoneAttrRef("z").not_(), BoolForm)


def test_none_not_evaluates():
    assert val(NoneAttrRef("z").not_(), ctx(z=None)) is True


def test_none_or_evaluates():
    assert val(NoneAttrRef("z").or_(True), ctx(z=None)) is True


# ---------------------------------------------------------------------------
# List element / slice
# ---------------------------------------------------------------------------


def test_list_first_elem_narrows_to_any_form():
    assert isinstance(ListAttrRef("xs").first_elem(), AnyForm)


def test_list_first_elem_evaluates():
    assert val(ListAttrRef("xs").first_elem(), ctx(xs=[3, 1, 2])) == 3


def test_list_getitem_index_narrows_to_any_form():
    assert isinstance(ListAttrRef("xs")[0], AnyForm)


def test_list_getitem_evaluates():
    assert val(ListAttrRef("xs")[0], ctx(xs=[10, 20, 30])) == 10


def test_list_slice_narrows_to_list_form():
    assert isinstance(ListAttrRef("xs")[0:2], ListForm)


def test_list_slice_evaluates():
    assert val(ListAttrRef("xs")[0:2], ctx(xs=[10, 20, 30])) == [10, 20]


def test_list_mul_narrows_to_list_form():
    assert isinstance(ListAttrRef("xs") * 2, ListForm)


def test_list_mul_evaluates():
    assert val(ListAttrRef("xs") * 2, ctx(xs=[1, 2])) == [1, 2, 1, 2]


# ---------------------------------------------------------------------------
# Dict get / keys / copy
# ---------------------------------------------------------------------------


def test_dict_get_narrows_to_any_form():
    assert isinstance(DictAttrRef("d").get("k"), AnyForm)


def test_dict_get_evaluates():
    assert val(DictAttrRef("d").get("x"), ctx(d={"x": 1, "y": 2})) == 1


def test_dict_get_default_evaluates():
    assert val(DictAttrRef("d").get("z", 99), ctx(d={"x": 1})) == 99


def test_dict_keys_evaluates():
    result = val(DictAttrRef("d").keys(), ctx(d={"a": 1, "b": 2}))
    assert set(result) == {"a", "b"}  # type: ignore[call-overload]


def test_dict_copy_evaluates():
    assert val(DictAttrRef("d").copy(), ctx(d={"a": 1})) == {"a": 1}


# ---------------------------------------------------------------------------
# Set ops
# ---------------------------------------------------------------------------


def test_set_union_evaluates():
    st = SetAttrRef("st")
    assert val(st.union(LiteralQuery({4, 5})), ctx(st={1, 2, 3})) == {1, 2, 3, 4, 5}


def test_set_intersection_evaluates():
    st = SetAttrRef("st")
    assert val(st.intersection(LiteralQuery({2, 3, 4})), ctx(st={1, 2, 3})) == {2, 3}


def test_set_issubset_narrows_to_bool_form():
    assert isinstance(SetAttrRef("st").issubset(LiteralQuery({1, 2, 3})), BoolForm)


def test_set_issubset_evaluates():
    assert val(SetAttrRef("st").issubset(LiteralQuery({1, 2, 3, 4})), ctx(st={1, 2})) is True


def test_frozenset_union_evaluates():
    fs = FrozenSetAttrRef("fs")
    result = val(fs.union(LiteralQuery(frozenset({40}))), ctx(fs=frozenset({10, 20})))
    assert result == frozenset({10, 20, 40})


def test_frozenset_isdisjoint_evaluates():
    fs = FrozenSetAttrRef("fs")
    assert val(fs.isdisjoint(LiteralQuery(frozenset({99}))), ctx(fs=frozenset({1, 2}))) is True


# ---------------------------------------------------------------------------
# TupleAttrRef
# ---------------------------------------------------------------------------


def test_tuple_getitem_narrows_to_any_form():
    assert isinstance(TupleAttrRef("tp")[0], AnyForm)


def test_tuple_getitem_evaluates():
    assert val(TupleAttrRef("tp")[0], ctx(tp=(10, 20, 30))) == 10


def test_tuple_first_elem_evaluates():
    assert val(TupleAttrRef("tp").first_elem(), ctx(tp=(10, 20, 30))) == 10


def test_tuple_slice_narrows_to_tuple_form():
    assert isinstance(TupleAttrRef("tp")[0:2], TupleForm)


def test_tuple_slice_evaluates():
    assert val(TupleAttrRef("tp")[0:2], ctx(tp=(10, 20, 30))) == (10, 20)


# ---------------------------------------------------------------------------
# Sentinel checks
# ---------------------------------------------------------------------------


def test_missing_ref_is_empty_narrows_to_bool_form():
    assert isinstance(IntAttrRef("missing").is_empty(), BoolForm)


def test_missing_ref_is_empty_evaluates_true():
    assert val(IntAttrRef("missing").is_empty()) is True


def test_missing_ref_not_empty_evaluates_false():
    assert val(IntAttrRef("missing").not_empty()) is False


def test_bound_ref_is_empty_evaluates_false():
    assert val(IntAttrRef("n").is_empty(), ctx(n=5)) is False


def test_bound_ref_not_empty_evaluates_true():
    assert val(IntAttrRef("n").not_empty(), ctx(n=5)) is True


# ---------------------------------------------------------------------------
# Convoluted 1: chained promotion + comparison
# (n + 1.5) * 2 > 20 -> BoolForm; value = (10 + 1.5) * 2 = 23.0 > 20
# ---------------------------------------------------------------------------


def test_convo1_intermediate_types():
    n = IntAttrRef("n")
    step1 = n + 1.5
    assert isinstance(step1, FloatForm)
    step2 = step1 * 2
    assert isinstance(step2, FloatForm)
    convo1 = step2 > 20
    assert isinstance(convo1, BoolForm)


def test_convo1_evaluates():
    n = IntAttrRef("n")
    expr = (n + 1.5) * 2 > 20
    assert isinstance(expr, BoolForm)
    assert val(expr, ctx(n=10)) is True


def test_convo1_evaluates_false_below_threshold():
    n = IntAttrRef("n")
    # (5 + 1.5) * 2 = 13.0 <= 20
    assert val((n + 1.5) * 2 > 20, ctx(n=5)) is False


# ---------------------------------------------------------------------------
# Convoluted 2: two int refs + comparison + and_ with bool ref
# (a + b > 10).and_(flag) -> BoolForm
# ---------------------------------------------------------------------------


def test_convo2_narrows_to_bool_form():
    a = IntAttrRef("a")
    b = IntAttrRef("b")
    flag = BoolAttrRef("flag")
    assert isinstance((a + b > 10).and_(flag), BoolForm)


def test_convo2_evaluates_true():
    a = IntAttrRef("a")
    b = IntAttrRef("b")
    flag = BoolAttrRef("flag")
    assert val((a + b > 10).and_(flag), ctx(a=7, b=5, flag=True)) is True


def test_convo2_evaluates_false_when_sum_low():
    a = IntAttrRef("a")
    b = IntAttrRef("b")
    flag = BoolAttrRef("flag")
    assert val((a + b > 10).and_(flag), ctx(a=3, b=3, flag=True)) is False


def test_convo2_evaluates_false_when_flag_false():
    a = IntAttrRef("a")
    b = IntAttrRef("b")
    flag = BoolAttrRef("flag")
    assert val((a + b > 10).and_(flag), ctx(a=7, b=5, flag=False)) is False


# ---------------------------------------------------------------------------
# Convoluted 3: string build + predicate
# (s.upper() + "!").startswith("HELLO") -> BoolForm
# ---------------------------------------------------------------------------


def test_convo3_narrows_to_bool_form():
    s = StrAttrRef("s")
    assert isinstance((s.upper() + "!").startswith("HELLO"), BoolForm)


def test_convo3_evaluates_true():
    s = StrAttrRef("s")
    assert val((s.upper() + "!").startswith("HELLO"), ctx(s="hello")) is True


def test_convo3_evaluates_false():
    s = StrAttrRef("s")
    assert val((s.upper() + "!").startswith("HELLO"), ctx(s="world")) is False


def test_convo3_intermediate_str_forms():
    s = StrAttrRef("s")
    upper_expr = s.upper()
    assert isinstance(upper_expr, StrForm)
    cat_expr = upper_expr + "!"
    assert isinstance(cat_expr, StrForm)


# ---------------------------------------------------------------------------
# Convoluted 4: list first_elem used in arithmetic
# xs.first_elem() + 3 -> AnyForm; value = 5 + 3 = 8
# ---------------------------------------------------------------------------


def test_convo4_narrows_to_any_form():
    xs = ListAttrRef("xs")
    assert isinstance(xs.first_elem() + 3, AnyForm)


def test_convo4_evaluates():
    xs = ListAttrRef("xs")
    assert val(xs.first_elem() + 3, ctx(xs=[5, 10, 15])) == 8


def test_convo4_different_list():
    xs = ListAttrRef("xs")
    assert val(xs.first_elem() + 10, ctx(xs=[100, 200])) == 110


# ---------------------------------------------------------------------------
# Convoluted 5: comparison of two arithmetic subtrees
# (n * 2) == (n + n) -> BoolForm; always True
# ---------------------------------------------------------------------------


def test_convo5_narrows_to_bool_form():
    n = IntAttrRef("n")
    assert isinstance(n * 2 == n + n, BoolForm)


def test_convo5_lhs_rhs_are_int_forms():
    n = IntAttrRef("n")
    assert isinstance(n * 2, IntForm)
    assert isinstance(n + n, IntForm)


def test_convo5_evaluates_true():
    n = IntAttrRef("n")
    assert val(n * 2 == n + n, ctx(n=7)) is True


def test_convo5_evaluates_true_for_zero():
    n = IntAttrRef("n")
    assert val(n * 2 == n + n, ctx(n=0)) is True
