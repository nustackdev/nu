"""The shape grid mirrors nu.forms: every form has its three tiers, each a form and a ref.

Rows are the Python types ``nu.forms`` defines (ABC, built-in, primitive);
columns are the slot capabilities (read, mutable, reactive). Each cell is an
explicit shape form (capability base + forms type) and its ref (that form +
``StructuredRef``).
"""

from __future__ import annotations

import inspect
from itertools import pairwise

import pytest

import nu.domains.shape as shape
from nu import forms
from nu.domains.shape import collection as cap
from nu.domains.shape import item
from nu.domains.shape.base import StructuredRef
from nu.domains.shape.collections import abc as sabc
from nu.domains.shape.collections import dict_, list_, set_, tuple_
from nu.domains.shape.form import SlotForm
from nu.domains.shape.primitives import bool_, bytes_, float_, int_, object_, str_
from nu.forms.collections import abc as fabc
from nu.lang import TypedNu


LEVELS = ("read", "mutable", "reactive")

COLLECTION_CAPS = (cap.CollectionForm, cap.MutableCollectionForm, cap.ReactiveCollectionForm)
ITEM_CAPS = (item.ItemForm, item.MutableItemForm, item.ReactiveItemForm)
ITEM_REFS = (item.ItemRef, item.MutableItemRef, item.ReactiveItemRef)

ABC_MAPPING_REFS = (sabc.MappingRef, sabc.MutableMappingRef, sabc.ReactiveMappingRef)
ABC_ORDERED_REFS = (
    sabc.OrderedMappingRef,
    sabc.MutableOrderedMappingRef,
    sabc.ReactiveOrderedMappingRef,
)
ABC_SEQUENCE_REFS = (sabc.SequenceRef, sabc.MutableSequenceRef, sabc.ReactiveSequenceRef)
ABC_SET_REFS = (sabc.SetRef, sabc.MutableSetRef, sabc.ReactiveSetRef)


def _cells(module: object, stem: str) -> tuple[tuple[type, ...], tuple[type, ...]]:
    """The (forms, refs) of one row, read tier first, looked up by the naming scheme."""
    prefixes = ("", "Mutable", "Reactive")
    cell_forms = tuple(getattr(module, f"{p}{stem}Form") for p in prefixes)
    cell_refs = tuple(getattr(module, f"{p}{stem}Ref") for p in prefixes)
    return cell_forms, cell_refs


# row: (forms type per tier, shape module, name stem, capability bases, ABC refs per tier)
ROWS: dict[str, tuple] = {
    # ABC rows: the forms type changes with the tier, like Python's ABCs.
    "Mapping": (
        (fabc.MappingForm, fabc.MutableMappingForm, fabc.ReactiveMappingForm),
        sabc,
        "Mapping",
        COLLECTION_CAPS,
        ABC_MAPPING_REFS,
    ),
    "OrderedMapping": (
        (
            fabc.OrderedMappingForm,
            fabc.MutableOrderedMappingForm,
            fabc.ReactiveOrderedMappingForm,
        ),
        sabc,
        "OrderedMapping",
        COLLECTION_CAPS,
        ABC_ORDERED_REFS,
    ),
    "Sequence": (
        (fabc.SequenceForm, fabc.MutableSequenceForm, fabc.ReactiveSequenceForm),
        sabc,
        "Sequence",
        COLLECTION_CAPS,
        ABC_SEQUENCE_REFS,
    ),
    # Built-in rows: one forms type at every tier.
    "Dict": ((forms.Dict,) * 3, dict_, "PyDict", COLLECTION_CAPS, ABC_ORDERED_REFS),
    "List": ((forms.List,) * 3, list_, "PyList", COLLECTION_CAPS, ABC_SEQUENCE_REFS),
    "Set": ((forms.Set,) * 3, set_, "PySet", COLLECTION_CAPS, ABC_SET_REFS),
    # A tuple or frozenset slot is writable, its value is not: only the read
    # tier sits on an ABC ref.
    "Tuple": ((forms.Tuple,) * 3, tuple_, "PyTuple", COLLECTION_CAPS, (sabc.SequenceRef,) * 3),
    "FrozenSet": ((forms.FrozenSet,) * 3, set_, "PyFrozenSet", COLLECTION_CAPS, (sabc.SetRef,) * 3),
    # Primitive rows: leaves.
    "Int": ((forms.Int,) * 3, int_, "PyInt", ITEM_CAPS, ITEM_REFS),
    "Str": ((forms.Str,) * 3, str_, "PyStr", ITEM_CAPS, ITEM_REFS),
    "Float": ((forms.Float,) * 3, float_, "PyFloat", ITEM_CAPS, ITEM_REFS),
    "Bool": ((forms.Bool,) * 3, bool_, "PyBool", ITEM_CAPS, ITEM_REFS),
    "Bytes": ((forms.Bytes,) * 3, bytes_, "PyBytes", ITEM_CAPS, ITEM_REFS),
    "Object": ((forms.Object,) * 3, object_, "PyObject", ITEM_CAPS, ITEM_REFS),
}


def _set_row() -> tuple:
    """The ABC set row: its read form is ``SetLikeForm``, its refs keep the ``SetRef`` name."""
    cell_forms = (sabc.SetLikeForm, sabc.MutableSetForm, sabc.ReactiveSetForm)
    return (
        (fabc.SetLikeForm, fabc.MutableSetForm, fabc.ReactiveSetForm),
        cell_forms,
        ABC_SET_REFS,
        COLLECTION_CAPS,
        ABC_SET_REFS,
    )


def _row(name: str) -> tuple:
    """(forms types, cell forms, cell refs, capability bases, ABC refs) of one row."""
    if name == "SetLike":
        return _set_row()
    form_types, module, stem, caps, abc_refs = ROWS[name]
    cell_forms, cell_refs = _cells(module, stem)
    return form_types, cell_forms, cell_refs, caps, abc_refs


ALL_ROWS = [*ROWS, "SetLike"]

#: Forms that are not a slot's value type, so they have no row.
NOT_SLOT_VALUES = {
    forms.Iterator,  # a stream, read once; no slot holds one
    forms.DictKeys,  # live views of a mapping, results only
    forms.DictValues,
    forms.DictItems,
    forms.None_,  # the result of a command
    forms.NullForm,  # the absence of a value
}

#: The single-method ABCs ``CollectionForm`` is built from; ``CollectionForm`` is
#: the read capability itself, so they have no row of their own.
CAPABILITY_FRAGMENTS = {
    fabc.CollectionForm,
    fabc.ContainerForm,
    fabc.IterableForm,
    fabc.SizedForm,
    fabc.SliceableForm,
}


def _all_forms() -> set[type]:
    """Every form class ``nu.forms`` exports: built-in, primitive and ABC."""
    found = set()
    for module in (forms, fabc):
        for value in vars(module).values():
            if inspect.isclass(value) and issubclass(value, forms.Form) and value is not forms.Form:
                found.add(value)
    return found


# ---------------------------------------------------------------------------
# completeness
# ---------------------------------------------------------------------------


def test_every_form_has_a_row() -> None:
    covered = {t for name in ALL_ROWS for t in _row(name)[0]}
    missing = _all_forms() - covered - NOT_SLOT_VALUES - CAPABILITY_FRAGMENTS
    assert not missing, f"forms with no shape row: {sorted(c.__name__ for c in missing)}"


@pytest.mark.parametrize("name", ALL_ROWS)
def test_row_has_three_tiers_of_forms_and_refs(name: str) -> None:
    _, cell_forms, cell_refs, _, _ = _row(name)
    assert len(cell_forms) == len(cell_refs) == len(LEVELS)
    assert len(set(cell_forms)) == len(set(cell_refs)) == len(LEVELS)


# ---------------------------------------------------------------------------
# bases
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("name", ALL_ROWS)
def test_each_form_is_its_forms_type_under_its_capability(name: str) -> None:
    form_types, cell_forms, _, caps, _ = _row(name)
    for form_type, cell, capability in zip(form_types, cell_forms, caps, strict=True):
        assert issubclass(cell, form_type), (cell, form_type)
        assert issubclass(cell, capability), (cell, capability)
        assert not issubclass(cell, StructuredRef), cell


@pytest.mark.parametrize("name", ALL_ROWS)
def test_each_tier_builds_on_the_one_below(name: str) -> None:
    _, cell_forms, cell_refs, _, _ = _row(name)
    for lower, upper in pairwise(cell_forms):
        assert issubclass(upper, lower), (upper, lower)
    for lower, upper in pairwise(cell_refs):
        assert issubclass(upper, lower), (upper, lower)


@pytest.mark.parametrize("name", ALL_ROWS)
def test_each_ref_is_its_form_plus_structured_ref(name: str) -> None:
    _, cell_forms, cell_refs, _, abc_refs = _row(name)
    for cell, ref, abc_ref in zip(cell_forms, cell_refs, abc_refs, strict=True):
        assert issubclass(ref, cell), (ref, cell)
        assert issubclass(ref, StructuredRef), ref
        assert issubclass(ref, abc_ref), (ref, abc_ref)


@pytest.mark.parametrize("name", ALL_ROWS)
def test_the_slot_capability_wins_over_the_value_form(name: str) -> None:
    # A ref is a fabric read: ``Ref`` must precede ``TypedNu`` (a passthrough
    # query), and the capability tier must precede the forms type, so ``set``
    # and the watches act on the slot.
    form_types, _, cell_refs, caps, _ = _row(name)
    for form_type, ref, capability in zip(form_types, cell_refs, caps, strict=True):
        mro = ref.__mro__
        if TypedNu in mro:
            assert mro.index(StructuredRef) < mro.index(TypedNu), ref
        assert mro.index(capability) < mro.index(form_type), ref


def test_package_exports_every_ref() -> None:
    for name in ALL_ROWS:
        for ref in _row(name)[2]:
            assert getattr(shape, ref.__name__) is ref
            assert ref.__name__ in shape.__all__


# ---------------------------------------------------------------------------
# what the tiers mean
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("ref", [tuple_.MutablePyTupleRef, set_.MutablePyFrozenSetRef])
def test_a_frozen_value_slot_is_writable_but_its_value_is_not(ref: type) -> None:
    assert hasattr(ref, "set")
    assert hasattr(ref, "erase")
    for in_place in ("append", "insert", "add", "discard", "update"):
        assert not hasattr(ref, in_place), (ref, in_place)


@pytest.mark.parametrize(
    "ref", [tuple_.ReactivePyTupleRef, set_.ReactivePyFrozenSetRef, dict_.ReactivePyDictRef]
)
def test_a_reactive_slot_is_watched_whatever_it_holds(ref: type) -> None:
    from nu.core.reactive import OnChange

    assert isinstance(ref("slot").on_change(), OnChange)


def test_read_tiers_have_no_slot_writes() -> None:
    for name in ALL_ROWS:
        read_ref = _row(name)[2][0]
        assert not hasattr(read_ref, "erase"), read_ref


def test_built_in_rows_carry_the_built_in_only_calls() -> None:
    assert hasattr(dict_.PyDictRef, "merge")
    assert hasattr(list_.PyListRef, "sort")
    assert hasattr(set_.PySetRef, "copy")
    assert not hasattr(sabc.MappingRef, "merge")
    assert not hasattr(sabc.SequenceRef, "sort")


def test_a_fallback_off_a_slot_reads_as_the_plain_value_form() -> None:
    assert type(int_.ReactivePyIntRef("n").fallback(0)) is forms.Int
    assert type(dict_.MutablePyDictRef("d").fallback({})) is forms.Dict
    assert issubclass(int_.PyIntForm, SlotForm)
