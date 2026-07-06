"""Tests for ``nu.lang.typeinfo`` - Phase 1 of task-119.

Covers annotation normalization + ``to_form`` dispatch under the task-119
typing discipline: annotations carry Ref subclasses (bare or parametric),
Shape subclasses, or primitive python types; unions/optionals normalize;
``ForwardRef`` / string annotations resolve via ``hints``.
"""

from __future__ import annotations

import typing
from typing import Any, ClassVar, ForwardRef, Optional, Union

from nu.forms import (
    AnyForm,
    BoolForm,
    BytesForm,
    DictForm,
    FloatForm,
    FrozenSetForm,
    IntForm,
    ListForm,
    SetForm,
    StrForm,
    TupleForm,
)
from nu.lang import TypeInfo
from nu.mem.refs import (
    DictRef,
    IntRef,
    ListRef,
    ShapeRef,
    ShapesDictRef,
    ShapesListRef,
    StrRef,
)
from nu.virtuals.refs import (
    PrimitiveDictRef,
    PrimitiveListRef,
)


# module-scope stand-in Shape for annotation tests
class _StubShape:
    """Stand-in for a Shape subclass; duck-typed via ``_slots``."""

    _slots: ClassVar[dict] = {}


# --- primitive leaves ---------------------------------------------------


def test_primitive_leaves_normalize_flat() -> None:
    for py in (int, str, bool, float, bytes):
        info = TypeInfo.from_annotation(py)
        assert info == TypeInfo(py)
        assert info.is_primitive
        assert not info.is_ref
        assert not info.is_shape


def test_any_normalizes_to_any_leaf() -> None:
    assert TypeInfo.from_annotation(Any) == TypeInfo(Any)
    assert TypeInfo.any() == TypeInfo(Any)
    assert TypeInfo.any().is_any


def test_unknown_class_stays_as_leaf() -> None:
    class Custom:
        pass

    info = TypeInfo.from_annotation(Custom)
    assert info == TypeInfo(Custom)
    assert not info.is_ref
    assert not info.is_shape
    assert not info.is_primitive


# --- bare ref classes ----------------------------------------------------


def test_bare_ref_class_normalizes_to_ref_leaf() -> None:
    info = TypeInfo.from_annotation(StrRef)
    assert info == TypeInfo(StrRef)
    assert info.is_ref
    assert not info.is_shape
    assert not info.is_primitive


def test_bare_int_ref_normalizes() -> None:
    assert TypeInfo.from_annotation(IntRef).is_ref


# --- parametric ref classes ---------------------------------------------


def test_primitive_list_ref_records_elem_type() -> None:
    info = TypeInfo.from_annotation(PrimitiveListRef[str])
    assert info == TypeInfo(PrimitiveListRef, elem=TypeInfo(str))
    assert info.is_ref
    assert info.elem is not None and info.elem.is_primitive


def test_primitive_dict_ref_records_key_and_elem() -> None:
    info = TypeInfo.from_annotation(PrimitiveDictRef[str, int])
    assert info == TypeInfo(
        PrimitiveDictRef, key=TypeInfo(str), elem=TypeInfo(int)
    )


def test_shapes_dict_ref_records_key_and_shape_elem() -> None:
    info = TypeInfo.from_annotation(ShapesDictRef[int, _StubShape])
    assert info == TypeInfo(
        ShapesDictRef, key=TypeInfo(int), elem=TypeInfo(_StubShape)
    )
    assert info.is_ref
    assert info.elem is not None and info.elem.is_shape


def test_shapes_list_ref_records_shape_elem() -> None:
    info = TypeInfo.from_annotation(ShapesListRef[_StubShape])
    assert info == TypeInfo(ShapesListRef, elem=TypeInfo(_StubShape))


def test_shape_ref_records_shape_elem() -> None:
    info = TypeInfo.from_annotation(ShapeRef[_StubShape])
    assert info == TypeInfo(ShapeRef, elem=TypeInfo(_StubShape))


def test_chained_parametric_refs_recurse() -> None:
    """``ListRef[DictRef[str, int]]`` -> nested Ref TypeInfos."""
    info = TypeInfo.from_annotation(ListRef[DictRef[str, int]])
    assert info.py_type is ListRef
    inner = info.elem
    assert inner is not None
    assert inner.py_type is DictRef
    assert inner.key == TypeInfo(str)
    assert inner.elem == TypeInfo(int)


# --- bare Shape subclass -------------------------------------------------


def test_bare_shape_subclass_normalizes_to_shape_leaf() -> None:
    info = TypeInfo.from_annotation(_StubShape)
    assert info == TypeInfo(_StubShape)
    assert info.is_shape
    assert not info.is_ref
    assert not info.is_primitive


# --- native container generics (backcompat) ------------------------------


def test_dict_generic_recurses_key_and_elem() -> None:
    info = TypeInfo.from_annotation(dict[str, int])
    assert info == TypeInfo(dict, key=TypeInfo(str), elem=TypeInfo(int))


def test_list_generic_recurses_elem() -> None:
    assert TypeInfo.from_annotation(list[int]) == TypeInfo(
        list, elem=TypeInfo(int)
    )


def test_bare_container_class_fills_any_children() -> None:
    assert TypeInfo.from_annotation(dict) == TypeInfo(
        dict, key=TypeInfo(Any), elem=TypeInfo(Any)
    )
    assert TypeInfo.from_annotation(list) == TypeInfo(list, elem=TypeInfo(Any))
    assert TypeInfo.from_annotation(tuple) == TypeInfo(tuple, elem=TypeInfo(Any))
    assert TypeInfo.from_annotation(set) == TypeInfo(set, elem=TypeInfo(Any))
    assert TypeInfo.from_annotation(frozenset) == TypeInfo(
        frozenset, elem=TypeInfo(Any)
    )


# --- deep recursion ------------------------------------------------------


def test_four_levels_deep_stays_typed() -> None:
    info = TypeInfo.from_annotation(dict[str, list[dict[int, str]]])
    assert info.py_type is dict
    assert info.key == TypeInfo(str)
    lvl2 = info.elem
    assert lvl2 is not None and lvl2.py_type is list
    lvl3 = lvl2.elem
    assert lvl3 is not None and lvl3.py_type is dict
    assert lvl3.key == TypeInfo(int)
    assert lvl3.elem == TypeInfo(str)


# --- union / optional ----------------------------------------------------


def test_optional_collapses_to_inner_type() -> None:
    assert TypeInfo.from_annotation(int | None) == TypeInfo(int)
    assert TypeInfo.from_annotation(Optional[int]) == TypeInfo(int)  # noqa: UP045


def test_optional_of_parametric_ref_collapses() -> None:
    info = TypeInfo.from_annotation(PrimitiveListRef[str] | None)
    assert info == TypeInfo(PrimitiveListRef, elem=TypeInfo(str))


def test_non_trivial_union_becomes_any() -> None:
    assert TypeInfo.from_annotation(int | str) == TypeInfo(Any)
    assert TypeInfo.from_annotation(Union[int, str, bytes]) == TypeInfo(Any)  # noqa: UP007


def test_union_nested_in_container_becomes_any_elem() -> None:
    assert TypeInfo.from_annotation(list[int | str]) == TypeInfo(
        list, elem=TypeInfo(Any)
    )


# --- forward refs --------------------------------------------------------


def test_string_annotation_resolved_via_hints() -> None:
    class MyShape:
        pass

    info = TypeInfo.from_annotation("MyShape", {"MyShape": MyShape})
    assert info == TypeInfo(MyShape)


def test_string_annotation_without_hint_degrades_to_any() -> None:
    assert TypeInfo.from_annotation("Unknown") == TypeInfo(Any)


def test_forward_ref_object_resolved_via_hints() -> None:
    class MyShape:
        pass

    ref = ForwardRef("MyShape")
    info = TypeInfo.from_annotation(ref, {"MyShape": MyShape})
    assert info == TypeInfo(MyShape)


def test_forward_ref_object_without_hint_degrades_to_any() -> None:
    ref = ForwardRef("Unknown")
    assert TypeInfo.from_annotation(ref) == TypeInfo(Any)


def test_get_type_hints_pipeline() -> None:
    """The metaclass will call ``get_type_hints`` then hand values in."""

    class Owner:
        field: dict[str, list[int]]

    hints = typing.get_type_hints(Owner)
    info = TypeInfo.from_annotation(hints["field"])
    assert info == TypeInfo(
        dict, key=TypeInfo(str), elem=TypeInfo(list, elem=TypeInfo(int))
    )


# --- to_form dispatch ----------------------------------------------------


def test_to_form_maps_primitive_leaves() -> None:
    pairs = [
        (bool, BoolForm),
        (int, IntForm),
        (float, FloatForm),
        (str, StrForm),
        (bytes, BytesForm),
    ]
    for py, form in pairs:
        assert TypeInfo(py).to_form() is form


def test_to_form_maps_container_leaves() -> None:
    pairs = [
        (list, ListForm),
        (dict, DictForm),
        (set, SetForm),
        (frozenset, FrozenSetForm),
        (tuple, TupleForm),
    ]
    for py, form in pairs:
        assert TypeInfo(py).to_form() is form


def test_to_form_any_yields_any_form() -> None:
    assert TypeInfo(Any).to_form() is AnyForm


def test_to_form_ref_class_falls_back_to_any_form() -> None:
    # Ref-typed nodes are handled by the wrapper's ref descent, not to_form.
    # to_form on them defaults to AnyForm.
    assert TypeInfo(StrRef).to_form() is AnyForm


def test_to_form_shape_class_falls_back_to_any_form() -> None:
    assert TypeInfo(_StubShape).to_form() is AnyForm


def test_to_form_ignores_tier_arg() -> None:
    assert TypeInfo(int).to_form(tier="anything") is IntForm


# --- accessors ------------------------------------------------------------


def test_accessors_are_mutually_exclusive() -> None:
    ti_ref = TypeInfo(StrRef)
    ti_shape = TypeInfo(_StubShape)
    ti_prim = TypeInfo(int)
    ti_any = TypeInfo(Any)
    for ti in (ti_ref, ti_shape, ti_prim, ti_any):
        flags = [ti.is_ref, ti.is_shape, ti.is_primitive, ti.is_any]
        assert sum(flags) == 1, (ti, flags)
