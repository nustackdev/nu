"""Functional tests for the whole-blob compound refs (``primitives``).

Each ref stores a container (list / dict / tuple / set / frozenset) as one
opaque blob via ``ItemPrimitiveSetCmd`` rather than decomposing it into
per-element storage. These tests round-trip a value through a real virtuals
transaction (the ``ctx`` fixture) and assert it comes back whole, as its true
domain type.
"""

from __future__ import annotations

from nu import Shape, run
from nu.virtuals import (
    PrimitiveDictRef,
    PrimitiveFrozenSetRef,
    PrimitiveListRef,
    PrimitiveSetRef,
    PrimitiveTupleRef,
)


class Bag(Shape):
    plist = PrimitiveListRef.slot()
    pdict = PrimitiveDictRef.slot()
    ptuple = PrimitiveTupleRef.slot()
    pset = PrimitiveSetRef.slot()
    pfrozen = PrimitiveFrozenSetRef.slot()


def _roundtrip(ref, value, ctx):
    run(ref.set(value), ctx)
    return run(ref, ctx)[0]


def test_primitive_list_roundtrip_whole_blob(ctx) -> None:
    # Heterogeneous list stored whole (no per-index decomposition).
    payload = [1, "two", {"three": 3}, [4, 5]]
    got = _roundtrip(Bag.plist, payload, ctx)
    assert got == payload
    assert isinstance(got, list)


def test_primitive_dict_roundtrip_whole_blob(ctx) -> None:
    payload = {"a": 1, "b": [2, 3], "c": {"nested": True}}
    got = _roundtrip(Bag.pdict, payload, ctx)
    assert got == payload
    assert isinstance(got, dict)


def test_primitive_tuple_roundtrip_whole_blob(ctx) -> None:
    payload = (1, "two", (3, 4))
    got = _roundtrip(Bag.ptuple, payload, ctx)
    assert got == payload
    assert isinstance(got, tuple)


def test_primitive_set_roundtrip_whole_blob(ctx) -> None:
    payload = {1, 2, 3, "four"}
    got = _roundtrip(Bag.pset, payload, ctx)
    assert got == payload
    assert isinstance(got, set)


def test_primitive_frozenset_roundtrip_whole_blob(ctx) -> None:
    payload = frozenset({1, 2, 3})
    got = _roundtrip(Bag.pfrozen, payload, ctx)
    assert got == payload
    assert isinstance(got, frozenset)
