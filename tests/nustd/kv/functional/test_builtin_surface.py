"""kv containers sit on the reactive shape ref of their built-in type, end to end on a store.

``DictRef``, ``ListRef`` and ``SetRef`` carry what only ``dict``, ``list`` and
``set`` have (``copy``, ``merge``, ``sort``, the set algebra), run against the
live View. ``Kh57Ref`` is a plain mapping: hashed order, so no reversal, no
paging and no dict-only calls.
"""

from __future__ import annotations

import pytest

import nu
from nu import run, shape
from nu.domains.shape import Shape, StructuredRef
from nu.forms import Dict, Int, List, Set, Str
from nu.lang import TypedNu
from nustd.kv import (
    BoolRef,
    BytesRef,
    DictRef,
    FloatRef,
    IntRef,
    Kh57Ref,
    ListRef,
    LogDictRef,
    ObjectRef,
    OrderedDictRef,
    RingRef,
    SetRef,
    ShapeRef,
    StrRef,
)


class Bag(Shape):
    meta = DictRef.slot(int)
    tags = ListRef.slot(str)
    members = SetRef.slot(str)
    points = Kh57Ref.slot(int)
    log = LogDictRef.slot(int)


# --- where each ref sits ----------------------------------------------------------


@pytest.mark.parametrize(
    ("ref", "base"),
    [
        (DictRef, shape.ReactiveDictRef),
        (OrderedDictRef, shape.ReactiveDictRef),
        (LogDictRef, shape.ReactiveDictRef),
        (ListRef, shape.ReactiveListRef),
        (SetRef, shape.ReactiveSetRef),
        (Kh57Ref, shape.ReactiveMappingRef),
        (ShapeRef, shape.ReactiveShapeRef),
        (RingRef, shape.SequenceRef),
        (IntRef, shape.ReactiveIntRef),
        (StrRef, shape.ReactiveStrRef),
        (FloatRef, shape.ReactiveFloatRef),
        (BoolRef, shape.ReactiveBoolRef),
        (BytesRef, shape.ReactiveBytesRef),
        (ObjectRef, shape.ReactiveObjectRef),
    ],
)
def test_each_kv_ref_sits_on_its_shape_ref(ref: type, base: type) -> None:
    assert issubclass(ref, base)
    mro = ref.__mro__
    if TypedNu in mro:
        assert mro.index(StructuredRef) < mro.index(TypedNu), ref


def test_kh57_is_a_plain_mapping_not_a_dict() -> None:
    assert not issubclass(Kh57Ref, DictRef)
    assert not issubclass(Kh57Ref, shape.OrderedMappingRef)
    for name in ("reversed_keys", "reversed_values", "reversed_items", "copy", "merge"):
        assert not hasattr(Kh57Ref, name), name


def test_ring_has_no_list_only_calls() -> None:
    for name in ("sort", "copy", "set_at", "insert", "pop"):
        assert not hasattr(RingRef, name), name


# --- end to end on a store ------------------------------------------------------------


def test_a_dict_copies_and_merges(ctx) -> None:
    run(Bag.meta.set({"a": 1}), ctx)
    copied = run(Bag.meta.copy(), ctx)[0]
    assert copied == {"a": 1}
    assert type(copied) is dict
    assert run(Bag.meta.merge({"b": 2}), ctx)[0] == {"a": 1, "b": 2}
    assert run(Bag.meta.extract(), ctx)[0] == {"a": 1}  # merge makes a new dict
    run(Bag.meta.merge_update({"b": 2}), ctx)
    assert run(Bag.meta.extract(), ctx)[0] == {"a": 1, "b": 2}


def test_a_merged_dict_carries_the_declared_value_type() -> None:
    merged = Bag.meta.merge({"b": 2})
    assert isinstance(merged, Dict)
    assert type(merged["b"]) is Int


def test_a_dict_reads_back_to_front_and_pages(ctx) -> None:
    run(Bag.log.set_item("a", 1) >> Bag.log.set_item("b", 2) >> Bag.log.set_item("c", 3), ctx)
    assert list(run(Bag.log.reversed_keys(), ctx)[0]) == ["c", "b", "a"]
    assert list(run(Bag.log.keys(after="a", limit=1), ctx)[0]) == ["b"]
    assert list(run(Bag.log.reversed_keys(before="c", limit=5), ctx)[0]) == ["b", "a"]


def test_a_list_sorts_copies_and_concatenates(ctx) -> None:
    run(Bag.tags.set(["b", "c", "a"]), ctx)
    assert run(Bag.tags.copy(), ctx)[0] == ["b", "c", "a"]
    assert run(Bag.tags + ["d"], ctx)[0] == ["b", "c", "a", "d"]  # noqa: RUF005 (a term)
    run(Bag.tags.sort(), ctx)
    assert run(Bag.tags.extract(), ctx)[0] == ["a", "b", "c"]
    assert type(Bag.tags.copy()) is List


def test_a_set_does_its_algebra(ctx) -> None:
    run(Bag.members.set({"a", "b"}), ctx)
    assert run(Bag.members.copy(), ctx)[0] == {"a", "b"}
    assert run(Bag.members.union({"c"}), ctx)[0] == {"a", "b", "c"}
    assert run(Bag.members.intersection({"b", "c"}), ctx)[0] == {"b"}
    assert run(Bag.members.difference({"a"}), ctx)[0] == {"b"}
    assert run(Bag.members.issubset({"a", "b", "c"}), ctx)[0] is True
    run(Bag.members.update({"c"}), ctx)
    assert run(Bag.members.extract(), ctx)[0] == {"a", "b", "c"}
    assert isinstance(Bag.members.union({"c"}), Set)


def test_a_built_in_call_types_its_elements() -> None:
    assert type(Bag.tags.copy()[0]) is Str
    assert isinstance(nu.Dict(Bag.meta), Dict)
