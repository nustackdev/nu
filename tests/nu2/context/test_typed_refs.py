"""Tests for the typed AttrRef subclasses (primitives and collections).

Each typed ref is an AttrRef (reads ctx.attrs) combined with a Form mixin that
exposes typed authoring operations. The MRO puts AttrRef first so its
compile/acompile wins over the form passthrough, and sort resolves to REF, not
SCALAR_QUERY.
"""

from __future__ import annotations

from nu2.context import (
    AnyAttrRef,
    AttrRef,
    BoolAttrRef,
    BytesAttrRef,
    DictAttrRef,
    FloatAttrRef,
    FrozenSetAttrRef,
    IntAttrRef,
    ListAttrRef,
    NoneAttrRef,
    SetAttrRef,
    StrAttrRef,
    TupleAttrRef,
)
from nu2.forms.collections import DictForm, FrozenSetForm, ListForm, SetForm, TupleForm
from nu2.forms.primitives import AnyForm, BoolForm, BytesForm, FloatForm, IntForm, NoneForm, StrForm
from nu2.lang import INVALID, Attr, Context, Sort, compile
from nu2.lang.helpers import run


# --- isinstance checks ---------------------------------------------------


def test_int_attr_ref_is_an_attr_ref():
    assert isinstance(IntAttrRef("x"), AttrRef)


def test_float_attr_ref_is_an_attr_ref():
    assert isinstance(FloatAttrRef("x"), AttrRef)


def test_str_attr_ref_is_an_attr_ref():
    assert isinstance(StrAttrRef("x"), AttrRef)


def test_bool_attr_ref_is_an_attr_ref():
    assert isinstance(BoolAttrRef("x"), AttrRef)


def test_bytes_attr_ref_is_an_attr_ref():
    assert isinstance(BytesAttrRef("x"), AttrRef)


def test_any_attr_ref_is_an_attr_ref():
    assert isinstance(AnyAttrRef("x"), AttrRef)


def test_none_attr_ref_is_an_attr_ref():
    assert isinstance(NoneAttrRef("x"), AttrRef)


def test_list_attr_ref_is_an_attr_ref():
    assert isinstance(ListAttrRef("xs"), AttrRef)


def test_dict_attr_ref_is_an_attr_ref():
    assert isinstance(DictAttrRef("d"), AttrRef)


def test_set_attr_ref_is_an_attr_ref():
    assert isinstance(SetAttrRef("s"), AttrRef)


def test_frozenset_attr_ref_is_an_attr_ref():
    assert isinstance(FrozenSetAttrRef("fs"), AttrRef)


def test_tuple_attr_ref_is_an_attr_ref():
    assert isinstance(TupleAttrRef("t"), AttrRef)


# --- form mixin isinstance checks ----------------------------------------


def test_int_attr_ref_is_an_int_form():
    assert isinstance(IntAttrRef("x"), IntForm)


def test_float_attr_ref_is_a_float_form():
    assert isinstance(FloatAttrRef("x"), FloatForm)


def test_str_attr_ref_is_a_str_form():
    assert isinstance(StrAttrRef("x"), StrForm)


def test_bool_attr_ref_is_a_bool_form():
    assert isinstance(BoolAttrRef("x"), BoolForm)


def test_bytes_attr_ref_is_a_bytes_form():
    assert isinstance(BytesAttrRef("x"), BytesForm)


def test_any_attr_ref_is_an_any_form():
    assert isinstance(AnyAttrRef("x"), AnyForm)


def test_none_attr_ref_is_a_none_form():
    assert isinstance(NoneAttrRef("x"), NoneForm)


def test_list_attr_ref_is_a_list_form():
    assert isinstance(ListAttrRef("xs"), ListForm)


def test_dict_attr_ref_is_a_dict_form():
    assert isinstance(DictAttrRef("d"), DictForm)


def test_set_attr_ref_is_a_set_form():
    assert isinstance(SetAttrRef("s"), SetForm)


def test_frozenset_attr_ref_is_a_frozenset_form():
    assert isinstance(FrozenSetAttrRef("fs"), FrozenSetForm)


def test_tuple_attr_ref_is_a_tuple_form():
    assert isinstance(TupleAttrRef("t"), TupleForm)


# --- sort resolves to REF ------------------------------------------------


def test_int_attr_ref_sort_is_ref():
    program = compile(IntAttrRef("x"))
    assert program.attr(program.root, Attr.SORT) is Sort.REF


def test_list_attr_ref_sort_is_ref():
    program = compile(ListAttrRef("xs"))
    assert program.attr(program.root, Attr.SORT) is Sort.REF


def test_dict_attr_ref_sort_is_ref():
    program = compile(DictAttrRef("d"))
    assert program.attr(program.root, Attr.SORT) is Sort.REF


# --- typed authoring: int arithmetic composes and evaluates --------------


def test_int_attr_ref_add_composes_to_int_form():
    result = IntAttrRef("x") + 3
    assert isinstance(result, IntForm)


def test_int_attr_ref_add_evaluates_correctly():
    ctx = Context()
    ctx.attrs["x"] = 10
    value, _ = run(IntAttrRef("x") + 3, ctx)
    assert value == 13


def test_int_attr_ref_unbound_propagates_invalid():
    value, _ = run(IntAttrRef("missing") + 3)
    assert value is INVALID


# --- float authoring -----------------------------------------------------


def test_float_attr_ref_mul_composes_to_float_form():
    result = FloatAttrRef("f") * 2.0
    assert isinstance(result, FloatForm)


# --- str authoring -------------------------------------------------------


def test_str_attr_ref_add_composes_to_str_form():
    result = StrAttrRef("s") + "_suffix"
    assert isinstance(result, StrForm)


# --- collection: list authoring ------------------------------------------


def test_list_attr_ref_first_elem_builds():
    result = ListAttrRef("xs").first_elem()
    assert isinstance(result, AnyForm)


def test_list_attr_ref_mul_composes_to_list_form():
    result = ListAttrRef("xs") * 2
    assert isinstance(result, ListForm)


# --- collection: dict authoring ------------------------------------------


def test_dict_attr_ref_composes_get_key():
    result = DictAttrRef("d").get("k")
    assert isinstance(result, AnyForm)
