"""Tests for annotation-driven Slot synthesis + ``TypeInfo`` stamping.

Phase 2 of task-119. The metaclass reads shape-slot annotations under the
task-119 typing discipline: bare Ref class -> auto-slot; parametric Ref
class -> auto-slot with kwargs derived via ``_slot_kwargs_from_type_args``;
bare Shape subclass without an explicit ``.slot()`` -> hard error; anything
else -> legacy path (explicit ``= <Ref>.slot(T)`` assignment). All paths
stamp a recursive ``TypeInfo`` onto the created ref's ``_payload``.
"""

from __future__ import annotations

from typing import Any

import pytest

import nu
from nu.kv.refs import (
    Kh57Ref,
    Kh57ShapesRef,
    PrimitiveDictRef,
    PrimitiveListRef,
)
from nu.lang import TypeInfo
from nu.mem.refs import (
    IntRef,
    ListRef,
    ShapeRef,
    ShapesDictRef,
    ShapesListRef,
    StrRef,
)


# --- module-scope shapes -------------------------------------------------


class LeafShape(nu.Shape):
    n: IntRef
    label: StrRef


class Bare(nu.Shape):
    """No annotations - fully legacy path."""

    n = IntRef.slot()


class LegacyPythonTyped(nu.Shape):
    """Legacy Python-typed annotation + explicit ``.slot()``."""

    tags: list[str] = ListRef.slot(str)


# --- bare Ref synthesis --------------------------------------------------


def test_bare_ref_annotation_synthesizes_slot() -> None:
    """`n: IntRef` alone -> Slot(IntRef); ref navigates."""
    assert "n" in LeafShape._slots
    assert LeafShape._slots["n"].ref_cls is IntRef


def test_bare_ref_annotation_stamps_type_info_on_ref() -> None:
    ref = LeafShape.n
    assert ref._payload["type_info"] == TypeInfo(IntRef)


def test_multiple_bare_refs_all_synthesize() -> None:
    assert LeafShape._slots["label"].ref_cls is StrRef
    assert LeafShape.label._payload["type_info"] == TypeInfo(StrRef)


# --- parametric Ref synthesis --------------------------------------------


class ListHolder(nu.Shape):
    tags: PrimitiveListRef[str]


def test_primitive_list_ref_synthesizes_with_no_kwargs() -> None:
    slot = ListHolder._slots["tags"]
    assert slot.ref_cls is PrimitiveListRef
    assert slot.kwargs == {}


def test_primitive_list_ref_stamps_recursive_type_info() -> None:
    ref = ListHolder.tags
    assert ref._payload["type_info"] == TypeInfo(PrimitiveListRef, elem=TypeInfo(str))


class DictHolder(nu.Shape):
    meta: PrimitiveDictRef[str, int]


def test_primitive_dict_ref_stamps_key_and_elem() -> None:
    info = DictHolder.meta._payload["type_info"]
    assert info == TypeInfo(PrimitiveDictRef, key=TypeInfo(str), elem=TypeInfo(int))


class DecomposedListHolder(nu.Shape):
    """Legacy: annotation is a python container, assignment is explicit."""

    items: list[int] = ListRef.slot(int)


def test_decomposed_list_ref_derives_slot_kwargs_from_annotation() -> None:
    """`items: ListRef[int]` would auto-synth. Here we still use legacy."""
    slot = DecomposedListHolder._slots["items"]
    assert slot.ref_cls is ListRef
    assert slot.kwargs["item_type"] is int


class ShapesDictHolder(nu.Shape):
    by_id: ShapesDictRef[int, LeafShape]


def test_shapes_dict_ref_synthesizes_with_derived_kwargs() -> None:
    slot = ShapesDictHolder._slots["by_id"]
    assert slot.ref_cls is ShapesDictRef
    assert slot.kwargs["shape_type"] is LeafShape
    assert slot.kwargs["key_type"] is int


def test_shapes_dict_ref_stamps_recursive_type_info() -> None:
    info = ShapesDictHolder.by_id._payload["type_info"]
    assert info == TypeInfo(ShapesDictRef, key=TypeInfo(int), elem=TypeInfo(LeafShape))


class ShapesListHolder(nu.Shape):
    rows: ShapesListRef[LeafShape]


def test_shapes_list_ref_synthesizes_with_shape_kwarg() -> None:
    slot = ShapesListHolder._slots["rows"]
    assert slot.ref_cls is ShapesListRef
    assert slot.kwargs["shape_type"] is LeafShape


def test_shapes_list_ref_stamps_type_info_with_shape_elem() -> None:
    info = ShapesListHolder.rows._payload["type_info"]
    assert info == TypeInfo(ShapesListRef, elem=TypeInfo(LeafShape))


class Kh57Holder(nu.Shape):
    entries: Kh57Ref[int]


def test_kh57_ref_synthesizes_with_derived_kwargs() -> None:
    slot = Kh57Holder._slots["entries"]
    assert slot.ref_cls is Kh57Ref
    assert slot.kwargs["value_type"] is int


def test_kh57_ref_stamps_recursive_type_info() -> None:
    info = Kh57Holder.entries._payload["type_info"]
    assert info == TypeInfo(Kh57Ref, elem=TypeInfo(int))


class Kh57ShapesHolder(nu.Shape):
    points: Kh57ShapesRef[LeafShape]


def test_kh57_shapes_ref_synthesizes_with_shape_kwarg() -> None:
    slot = Kh57ShapesHolder._slots["points"]
    assert slot.ref_cls is Kh57ShapesRef
    assert slot.kwargs["shape_type"] is LeafShape


def test_kh57_shapes_ref_stamps_type_info_with_shape_elem() -> None:
    info = Kh57ShapesHolder.points._payload["type_info"]
    assert info == TypeInfo(Kh57ShapesRef, elem=TypeInfo(LeafShape))


# --- bare Shape annotation (must have explicit .slot()) ------------------


def test_bare_shape_annotation_with_slot_uses_assignment() -> None:
    class ShapeHolder(nu.Shape):
        # Explicit `.slot()` names the fabric. Annotation is documentation
        # (for dot-nav autocomplete on LeafShape's own slots).
        rel: LeafShape = ShapeRef.slot(LeafShape)

    slot = ShapeHolder._slots["rel"]
    assert slot.ref_cls is ShapeRef
    assert slot.kwargs["shape_type"] is LeafShape


def test_bare_shape_annotation_without_slot_raises() -> None:
    with pytest.raises(TypeError, match=r"Bare Shape annotation"):

        class BadShape(nu.Shape):
            rel: LeafShape  # no assignment -> fabric can't be inferred


def test_bare_shape_annotation_with_assignment_stamps_shape_type_info() -> None:
    class RelHolder(nu.Shape):
        rel: LeafShape = ShapeRef.slot(LeafShape)

    info = RelHolder.rel._payload["type_info"]
    assert info == TypeInfo(LeafShape)


# --- legacy path (Python-typed annotation + explicit .slot()) ----------


def test_legacy_python_typed_annotation_still_works() -> None:
    ref = LegacyPythonTyped.tags
    assert ref._payload["item_type"] is str
    assert ref._payload["type_info"] == TypeInfo(list, elem=TypeInfo(str))


def test_no_annotation_no_type_info() -> None:
    ref = Bare.n
    assert "type_info" not in ref._payload


# --- union / optional in annotations ------------------------------------


class OptionalHolder(nu.Shape):
    maybe: IntRef | None = IntRef.slot()


def test_optional_collapses_to_inner_ref() -> None:
    info = OptionalHolder.maybe._payload["type_info"]
    assert info == TypeInfo(IntRef)


class UnionHolder(nu.Shape):
    """Non-trivial union collapses to Any; explicit .slot() carries the ref."""

    either: IntRef | StrRef = IntRef.slot()


def test_non_trivial_union_collapses_to_any() -> None:
    info = UnionHolder.either._payload["type_info"]
    assert info == TypeInfo(Any)


# --- private / ClassVar annotations are ignored -------------------------


def test_underscore_prefixed_annotations_are_not_synthesized() -> None:
    class WithPrivate(nu.Shape):
        _internal: int = 42
        n: IntRef

    assert "_internal" not in WithPrivate._slots
    assert "n" in WithPrivate._slots


# --- inheritance --------------------------------------------------------


class Parent(nu.Shape):
    n: IntRef
    label: StrRef


class Child(Parent):
    extra: IntRef


def test_child_inherits_parent_slots_and_adds_own() -> None:
    assert set(Child._slots) == {"n", "label", "extra"}
    assert Child._slots["extra"].ref_cls is IntRef
    # Inherited slots keep their original owner_cls (Parent), so type_info
    # resolves via Parent's annotations.
    assert Parent._slots["n"]._owner_cls is Parent


# --- Slot._resolve_type_info memoization --------------------------------


def test_resolve_type_info_memoizes_result() -> None:
    slot = LeafShape._slots["n"]
    a = slot._resolve_type_info()
    b = slot._resolve_type_info()
    assert a is b
    assert a == TypeInfo(IntRef)
