"""Tests for the typed attrs refs (immutable primitives and collections, Object).

Each typed ref is an AttrRef (reads ctx.attrs) combined with a Form mixin that
exposes typed authoring operations, read-only: attrs values never change in
place. The MRO puts AttrRef first so its
compile/acompile wins over the form passthrough, and sort resolves to REF, not
SCALAR_QUERY.
"""

from __future__ import annotations

import pytest

import nu
from nu.context import (
    BoolRef,
    BytesRef,
    FloatRef,
    FrozenSetRef,
    IntRef,
    ObjectRef,
    StrRef,
    TupleRef,
)
from nu.context.attrs import AttrRef
from nu.forms.collections import FrozenSet, Tuple
from nu.forms.primitives import Bool, Bytes, Float, Int, Object, Str
from nu.lang import INVALID, Attr, Context, Sort
from nu.lang.helpers import compile, run


# --- isinstance checks ---------------------------------------------------


def test_int_attr_ref_is_an_attr_ref():
    assert isinstance(IntRef("x"), AttrRef)


def test_float_attr_ref_is_an_attr_ref():
    assert isinstance(FloatRef("x"), AttrRef)


def test_str_attr_ref_is_an_attr_ref():
    assert isinstance(StrRef("x"), AttrRef)


def test_bool_attr_ref_is_an_attr_ref():
    assert isinstance(BoolRef("x"), AttrRef)


def test_bytes_attr_ref_is_an_attr_ref():
    assert isinstance(BytesRef("x"), AttrRef)


def test_any_attr_ref_is_an_attr_ref():
    assert isinstance(ObjectRef("x"), AttrRef)


def test_frozenset_attr_ref_is_an_attr_ref():
    assert isinstance(FrozenSetRef("fs"), AttrRef)


def test_tuple_attr_ref_is_an_attr_ref():
    assert isinstance(TupleRef("t"), AttrRef)


# --- form mixin isinstance checks ----------------------------------------


def test_int_attr_ref_is_an_int_form():
    assert isinstance(IntRef("x"), Int)


def test_float_attr_ref_is_a_float_form():
    assert isinstance(FloatRef("x"), Float)


def test_str_attr_ref_is_a_str_form():
    assert isinstance(StrRef("x"), Str)


def test_bool_attr_ref_is_a_bool_form():
    assert isinstance(BoolRef("x"), Bool)


def test_bytes_attr_ref_is_a_bytes_form():
    assert isinstance(BytesRef("x"), Bytes)


def test_any_attr_ref_is_an_any_form():
    assert isinstance(ObjectRef("x"), Object)


def test_frozenset_attr_ref_is_a_frozenset_form():
    assert isinstance(FrozenSetRef("fs"), FrozenSet)


def test_tuple_attr_ref_is_a_tuple_form():
    assert isinstance(TupleRef("t"), Tuple)


# --- sort resolves to REF ------------------------------------------------


def test_int_attr_ref_sort_is_ref():
    program = compile(IntRef("x"))
    assert program.attr(program.root, Attr.SORT) is Sort.REF


# --- typed authoring: int arithmetic composes and evaluates --------------


def test_int_attr_ref_add_composes_to_int_form():
    result = IntRef("x") + 3
    assert isinstance(result, Int)


def test_int_attr_ref_add_evaluates_correctly():
    ctx = Context()
    ctx.attrs["x"] = 10
    value, _ = run(IntRef("x") + 3, ctx)
    assert value == 13


def test_int_attr_ref_unbound_propagates_invalid():
    value, _ = run(IntRef("missing") + 3)
    assert value is INVALID


# --- float authoring -----------------------------------------------------


def test_float_attr_ref_mul_composes_to_float_form():
    result = FloatRef("f") * 2.0
    assert isinstance(result, Float)


# --- str authoring -------------------------------------------------------


def test_str_attr_ref_add_composes_to_str_form():
    result = StrRef("s") + "_suffix"
    assert isinstance(result, Str)


# --- immutable collections ------------------------------------------------


def test_tuple_ref_slice_composes_to_tuple_form():
    assert isinstance(TupleRef("t")[0:2], Tuple)


def test_frozenset_ref_union_evaluates():
    ctx = Context()
    ctx.attrs["fs"] = frozenset({1})
    value, _ = run(FrozenSetRef("fs").union(frozenset({2})), ctx)
    assert value == frozenset({1, 2})


# --- no in-place mutation ---------------------------------------------------

_MUTATORS = (
    "append",
    "extend",
    "insert",
    "remove",
    "discard",
    "pop",
    "popitem",
    "clear",
    "sort",
    "reverse",
    "add",
    "update",
    "set_item",
    "del_at",
    "setdefault",
    "intersection_update",
    "difference_update",
    "symmetric_difference_update",
)

_TYPED = (IntRef, FloatRef, StrRef, BoolRef, BytesRef, TupleRef, FrozenSetRef, ObjectRef)


@pytest.mark.parametrize("ref_type", _TYPED)
def test_typed_refs_expose_no_in_place_mutator(ref_type: type) -> None:
    exposed = [name for name in _MUTATORS if hasattr(ref_type, name)]
    assert exposed == []


@pytest.mark.parametrize("term", [ObjectRef("d"), Object({"k": 0})], ids=["ref", "form"])
def test_object_has_no_in_place_mutation(term: Object) -> None:
    for name in ("__setitem__", "__delitem__", "merge_update"):
        assert not hasattr(type(term), name)
    with pytest.raises(TypeError, match="does not support item assignment"):
        term["k"] = 1
    with pytest.raises(TypeError, match=r"(does not|doesn't) support item deletion"):
        del term["k"]


# --- public surface -------------------------------------------------------


@pytest.mark.parametrize("ref_type", _TYPED)
def test_typed_refs_are_top_level(ref_type: type) -> None:
    assert getattr(nu, ref_type.__name__) is ref_type


@pytest.mark.parametrize(
    "name",
    [
        "AttrRef",
        "SetCmd",
        "Delete",
        "AttrExists",
        "Exists",
        "StrAttrRef",
        "IntAttrRef",
        "FloatAttrRef",
        "BoolAttrRef",
        "BytesAttrRef",
        "ObjectAttrRef",
        "TupleAttrRef",
        "FrozenSetAttrRef",
        "ListAttrRef",
        "DictAttrRef",
        "SetAttrRef",
        "NoneAttrRef",
    ],
)
def test_removed_names_are_gone(name: str) -> None:
    assert not hasattr(nu, name)
    assert name not in nu.context.__all__
    assert name not in nu.__all__


def test_top_level_set_stays_the_set_form() -> None:
    assert nu.Set is nu.forms.Set


def test_the_attrs_exists_query_is_reached_through_the_ref() -> None:
    assert not hasattr(nu, "Exists")
    assert "Exists" not in nu.context.__all__
    assert isinstance(nu.ObjectRef("x").exists(), nu.context.attrs.Exists)
