"""Tests for annotation-driven Slot synthesis + ``TypeInfo`` stamping.

Phase 2 of task-119. The metaclass reads shape-slot annotations under the
task-119 typing discipline: bare Ref class -> auto-slot; parametric Ref
class -> auto-slot whose type arguments are its declaration, the same one an
explicit ``.slot(...)`` makes; bare Shape subclass without an explicit ``.slot()`` -> hard error; anything
else -> legacy path (explicit ``= <Ref>.slot(T)`` assignment). All paths
stamp a recursive ``TypeInfo`` onto the created ref's ``_payload``.
"""

from __future__ import annotations

from typing import Any

import pytest

import nu
from nu.lang import TypeInfo
from nustd.kv.refs import (
    Kh57Ref,
    PrimitiveDictRef,
    PrimitiveListRef,
)
from nustd.mem.refs import (
    DictRef,
    IntRef,
    ListRef,
    ShapeRef,
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
    assert nu.tree.payload(ref)["type_info"] == TypeInfo(IntRef)


def test_multiple_bare_refs_all_synthesize() -> None:
    assert LeafShape._slots["label"].ref_cls is StrRef
    assert nu.tree.payload(LeafShape.label)["type_info"] == TypeInfo(StrRef)


# --- parametric Ref synthesis --------------------------------------------


class ListHolder(nu.Shape):
    tags: PrimitiveListRef[str]


def test_primitive_list_ref_synthesizes_with_no_kwargs() -> None:
    slot = ListHolder._slots["tags"]
    assert slot.ref_cls is PrimitiveListRef
    assert slot.kwargs == {}


def test_primitive_list_ref_stamps_recursive_type_info() -> None:
    ref = ListHolder.tags
    assert nu.tree.payload(ref)["type_info"] == TypeInfo(PrimitiveListRef, elem=TypeInfo(str))


class DictHolder(nu.Shape):
    meta: PrimitiveDictRef[str, int]


def test_primitive_dict_ref_stamps_key_and_elem() -> None:
    info = nu.tree.payload(DictHolder.meta)["type_info"]
    assert info == TypeInfo(PrimitiveDictRef, key=TypeInfo(str), elem=TypeInfo(int))


class DecomposedListHolder(nu.Shape):
    """Legacy: annotation is a python container, assignment is explicit."""

    nums: list[int] = ListRef.slot(int)


def test_explicit_slot_declaration_wins_over_a_python_annotation() -> None:
    slot = DecomposedListHolder._slots["nums"]
    assert slot.ref_cls is ListRef
    assert slot.kwargs == {}
    info = nu.tree.payload(DecomposedListHolder.nums)["type_info"]
    assert info == TypeInfo(ListRef, elem=TypeInfo(int))


class ShapesDictHolder(nu.Shape):
    by_id: DictRef[int, LeafShape]


def test_shapes_dict_ref_synthesizes_with_no_kwargs() -> None:
    slot = ShapesDictHolder._slots["by_id"]
    assert slot.ref_cls is DictRef
    assert slot.kwargs == {}


def test_shapes_dict_ref_stamps_recursive_type_info() -> None:
    info = nu.tree.payload(ShapesDictHolder.by_id)["type_info"]
    assert info == TypeInfo(DictRef, key=TypeInfo(int), elem=TypeInfo(LeafShape))


class ShapesListHolder(nu.Shape):
    rows: ListRef[LeafShape]


def test_shapes_list_ref_synthesizes_with_no_kwargs() -> None:
    slot = ShapesListHolder._slots["rows"]
    assert slot.ref_cls is ListRef
    assert slot.kwargs == {}


def test_shapes_list_ref_stamps_type_info_with_shape_elem() -> None:
    info = nu.tree.payload(ShapesListHolder.rows)["type_info"]
    assert info == TypeInfo(ListRef, elem=TypeInfo(LeafShape))


class Kh57Holder(nu.Shape):
    entries: Kh57Ref[int]


def test_kh57_ref_synthesizes_with_no_kwargs() -> None:
    slot = Kh57Holder._slots["entries"]
    assert slot.ref_cls is Kh57Ref
    assert slot.kwargs == {}


def test_kh57_ref_stamps_recursive_type_info() -> None:
    info = nu.tree.payload(Kh57Holder.entries)["type_info"]
    assert info == TypeInfo(Kh57Ref, elem=TypeInfo(int))


class Kh57ShapesHolder(nu.Shape):
    points: Kh57Ref[LeafShape]


def test_kh57_shapes_ref_stamps_type_info_with_shape_elem() -> None:
    info = nu.tree.payload(Kh57ShapesHolder.points)["type_info"]
    assert info == TypeInfo(Kh57Ref, elem=TypeInfo(LeafShape))


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

    info = nu.tree.payload(RelHolder.rel)["type_info"]
    assert info == TypeInfo(LeafShape)


# --- legacy path (Python-typed annotation + explicit .slot()) ----------


def test_legacy_python_typed_annotation_takes_the_slot_declaration() -> None:
    ref = LegacyPythonTyped.tags
    assert nu.tree.payload(ref)["type_info"] == TypeInfo(ListRef, elem=TypeInfo(str))


# --- the two spellings agree ---------------------------------------------


class Spelled(nu.Shape):
    by_slot = DictRef.slot(LeafShape, key=int)
    by_annotation: DictRef[int, LeafShape]
    list_by_slot = ListRef.slot(str)
    list_by_annotation: ListRef[str]
    kh57_by_slot = Kh57Ref.slot(LeafShape)
    kh57_by_annotation: Kh57Ref[LeafShape]


@pytest.mark.parametrize(
    ("by_slot", "by_annotation"),
    [
        ("by_slot", "by_annotation"),
        ("list_by_slot", "list_by_annotation"),
        ("kh57_by_slot", "kh57_by_annotation"),
    ],
)
def test_slot_and_annotation_declare_the_same_ref(by_slot: str, by_annotation: str) -> None:
    a, b = getattr(Spelled, by_slot), getattr(Spelled, by_annotation)
    assert type(a) is type(b)
    assert nu.tree.payload(a)["type_info"] == nu.tree.payload(b)["type_info"]
    unnamed = lambda ref: {k: v for k, v in nu.tree.payload(ref).items() if k != "segment"}  # noqa: E731
    assert unnamed(a) == unnamed(b)


def test_no_annotation_no_type_info() -> None:
    ref = Bare.n
    assert "type_info" not in nu.tree.payload(ref)


# --- union / optional in annotations ------------------------------------


class OptionalHolder(nu.Shape):
    maybe: IntRef | None = IntRef.slot()


def test_optional_collapses_to_inner_ref() -> None:
    info = nu.tree.payload(OptionalHolder.maybe)["type_info"]
    assert info == TypeInfo(IntRef)


class UnionHolder(nu.Shape):
    """Non-trivial union collapses to Any; explicit .slot() carries the ref."""

    either: IntRef | StrRef = IntRef.slot()


def test_non_trivial_union_collapses_to_any() -> None:
    info = nu.tree.payload(UnionHolder.either)["type_info"]
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
