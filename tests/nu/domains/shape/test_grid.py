"""The shape grid mirrors nu.forms: every form has its row of refs, named after it.

A ref is named after its form, ``Form`` swapped for ``Ref``. ABC rows have one
ref per ABC tier (``MappingRef``, ``MutableMappingRef``, ``ReactiveMappingRef``),
except the reactive set-like tier, which has none. Built-in and primitive rows
have two refs: the base ref (``DictRef``) carries the slot capability (exists,
extract, set, erase, init), the reactive ref (``ReactiveDictRef``) adds the
watches. Each ref is its forms type under its capability base, plus
``StructuredRef``.
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
from nu.domains.shape.form import SlotForm
from nu.forms.collections import abc as fabc
from nu.lang import TypedNu


def _ref_name(form: type) -> str:
    """The ref name a form's row uses: ``Form`` swapped for ``Ref``, or ``Ref`` appended."""
    name = form.__name__
    return f"{name.removesuffix('Form')}Ref"


# ---------------------------------------------------------------------------
# rows
# ---------------------------------------------------------------------------

#: ABC forms, read tier first, and the capability base of each tier.
ABC_ROWS: dict[str, tuple[type, ...]] = {
    "Mapping": (fabc.MappingForm, fabc.MutableMappingForm, fabc.ReactiveMappingForm),
    "OrderedMapping": (
        fabc.OrderedMappingForm,
        fabc.MutableOrderedMappingForm,
        fabc.ReactiveOrderedMappingForm,
    ),
    "Sequence": (fabc.SequenceForm, fabc.MutableSequenceForm, fabc.ReactiveSequenceForm),
    "SetLike": (fabc.SetLikeForm, fabc.MutableSetForm),
}
COLLECTION_CAPS = (cap.CollectionForm, cap.MutableCollectionForm, cap.ReactiveCollectionForm)

#: ABC forms with no shape ref: ``ReactiveSetRef`` is the built-in ``set`` row's.
ABC_WITHOUT_REF = {fabc.ReactiveSetForm}

BUILT_IN_ROWS = (forms.Dict, forms.List, forms.Set, forms.FrozenSet, forms.Tuple)
PRIMITIVE_ROWS = (forms.Int, forms.Str, forms.Float, forms.Bool, forms.Bytes, forms.Object)

#: The ABC ref each built-in ref sits on. A tuple or frozenset slot is writable,
#: its value is not, so it sits on the read ABC ref under the mutable capability.
BUILT_IN_ABC_REF = {
    forms.Dict: sabc.MutableOrderedMappingRef,
    forms.List: sabc.MutableSequenceRef,
    forms.Set: sabc.MutableSetRef,
    forms.FrozenSet: sabc.SetLikeRef,
    forms.Tuple: sabc.SequenceRef,
}


def _two_refs(form: type) -> tuple[type, type]:
    """The base and reactive ref of a built-in or primitive row."""
    name = _ref_name(form)
    return getattr(shape, name), getattr(shape, f"Reactive{name}")


#: Every ref with the forms type it holds and its capability base.
CELLS: list[tuple[type, type, type]] = [
    *(
        (getattr(sabc, _ref_name(form)), form, capability)
        for row in ABC_ROWS.values()
        for form, capability in zip(row, COLLECTION_CAPS, strict=False)
    ),
    *(
        (ref, form, capability)
        for form in BUILT_IN_ROWS
        for ref, capability in zip(_two_refs(form), COLLECTION_CAPS[1:], strict=True)
    ),
    *(
        (ref, form, capability)
        for form in PRIMITIVE_ROWS
        for ref, capability in zip(
            _two_refs(form), (item.MutableItemForm, item.ReactiveItemForm), strict=True
        )
    ),
]
CELL_IDS = [ref.__name__ for ref, _, _ in CELLS]

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
# completeness and naming
# ---------------------------------------------------------------------------


def test_every_form_has_a_row() -> None:
    covered = {form for _, form, _ in CELLS} | ABC_WITHOUT_REF
    missing = _all_forms() - covered - NOT_SLOT_VALUES - CAPABILITY_FRAGMENTS
    assert not missing, f"forms with no shape row: {sorted(c.__name__ for c in missing)}"


@pytest.mark.parametrize(("ref", "form", "capability"), CELLS, ids=CELL_IDS)
def test_each_ref_is_named_after_its_form(ref: type, form: type, capability: type) -> None:
    expected = _ref_name(form)
    if issubclass(capability, (cap.ReactiveCollectionForm, item.ReactiveItemForm)) and not (
        form.__name__.startswith("Reactive")
    ):
        expected = f"Reactive{expected}"
    assert ref.__name__ == expected


def test_abc_reactive_set_has_no_ref() -> None:
    assert not hasattr(sabc, "ReactiveSetRef")
    assert shape.ReactiveSetRef is shape.collections.ReactiveSetRef
    assert issubclass(shape.ReactiveSetRef, forms.Set)


def test_package_exports_every_ref() -> None:
    for ref, _, _ in CELLS:
        assert getattr(shape, ref.__name__) is ref
        assert ref.__name__ in shape.__all__


def test_no_shape_only_forms_beside_the_refs() -> None:
    # Built-in and primitive rows are refs only; the ABC rows keep their
    # shape forms, which ShapeRef and the built-in refs build on.
    from nu.domains.shape.collections import dict_, list_, set_, tuple_
    from nu.domains.shape.primitives import bool_, bytes_, float_, int_, object_, str_

    for module in (dict_, list_, set_, tuple_, bool_, bytes_, float_, int_, object_, str_):
        for name, value in vars(module).items():
            if inspect.isclass(value) and value.__module__ == module.__name__:
                assert issubclass(value, StructuredRef), name


# ---------------------------------------------------------------------------
# bases
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(("ref", "form", "capability"), CELLS, ids=CELL_IDS)
def test_each_ref_is_its_form_under_its_capability(ref: type, form: type, capability: type) -> None:
    assert issubclass(ref, form), (ref, form)
    assert issubclass(ref, capability), (ref, capability)
    assert issubclass(ref, StructuredRef), ref


@pytest.mark.parametrize(("ref", "form", "capability"), CELLS, ids=CELL_IDS)
def test_the_slot_capability_wins_over_the_value_form(
    ref: type, form: type, capability: type
) -> None:
    # A ref is a fabric read: ``Ref`` must precede ``TypedNu`` (a passthrough
    # query), and the capability must precede the forms type, so ``set`` and
    # the watches act on the slot.
    mro = ref.__mro__
    if TypedNu in mro:
        assert mro.index(StructuredRef) < mro.index(TypedNu), ref
    assert mro.index(capability) < mro.index(form), ref


@pytest.mark.parametrize("name", list(ABC_ROWS))
def test_each_abc_tier_builds_on_the_one_below(name: str) -> None:
    refs = [getattr(sabc, _ref_name(form)) for form in ABC_ROWS[name]]
    for lower, upper in pairwise(refs):
        assert issubclass(upper, lower), (upper, lower)


@pytest.mark.parametrize("form", BUILT_IN_ROWS + PRIMITIVE_ROWS, ids=lambda f: f.__name__)
def test_the_reactive_ref_builds_on_the_base_ref(form: type) -> None:
    base, reactive = _two_refs(form)
    assert issubclass(reactive, base)


@pytest.mark.parametrize("form", BUILT_IN_ROWS, ids=lambda f: f.__name__)
def test_built_in_refs_sit_on_their_abc_ref(form: type) -> None:
    for ref in _two_refs(form):
        assert issubclass(ref, BUILT_IN_ABC_REF[form]), ref


# ---------------------------------------------------------------------------
# what the refs mean
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("ref", [shape.TupleRef, shape.FrozenSetRef])
def test_a_frozen_value_slot_is_writable_but_its_value_is_not(ref: type) -> None:
    assert hasattr(ref, "set")
    assert hasattr(ref, "erase")
    for in_place in ("append", "insert", "add", "discard", "update"):
        assert not hasattr(ref, in_place), (ref, in_place)


@pytest.mark.parametrize(
    "ref", [shape.ReactiveTupleRef, shape.ReactiveFrozenSetRef, shape.ReactiveDictRef]
)
def test_a_reactive_slot_is_watched_whatever_it_holds(ref: type) -> None:
    from nu.core.reactive import OnChange

    assert isinstance(ref("slot").on_change(), OnChange)


def test_base_refs_have_slot_writes_but_no_watches() -> None:
    for form in BUILT_IN_ROWS + PRIMITIVE_ROWS:
        base, _ = _two_refs(form)
        assert hasattr(base, "erase"), base
        assert hasattr(base, "init"), base
        assert not hasattr(base, "on_change"), base


def test_abc_read_tiers_have_no_slot_writes() -> None:
    for row in ABC_ROWS.values():
        read_ref = getattr(sabc, _ref_name(row[0]))
        assert not hasattr(read_ref, "erase"), read_ref


def test_built_in_rows_carry_the_built_in_only_calls() -> None:
    assert hasattr(shape.DictRef, "merge")
    assert hasattr(shape.ListRef, "sort")
    assert hasattr(shape.SetRef, "copy")
    assert not hasattr(sabc.MappingRef, "merge")
    assert not hasattr(sabc.SequenceRef, "sort")


def test_a_fallback_off_a_slot_reads_as_the_plain_value_form() -> None:
    assert type(shape.ReactiveIntRef("n").fallback(0)) is forms.Int
    assert type(shape.DictRef("d").fallback({})) is forms.Dict
    assert issubclass(shape.IntRef, SlotForm)
