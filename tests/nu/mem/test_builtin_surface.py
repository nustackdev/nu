"""mem refs sit on the base shape ref of their type, so they carry its whole built-in surface."""

from __future__ import annotations

import pytest

import nu
from nu import forms, shape


class Port(nu.Shape):
    meta = nu.DictRef.slot(int)
    tags = nu.ListRef.slot(str)
    members = nu.SetRef.slot(str)
    count = nu.IntRef.slot()
    name = nu.StrRef.slot()


@pytest.mark.parametrize(
    ("ref", "base"),
    [
        (nu.DictRef, shape.DictRef),
        (nu.ListRef, shape.ListRef),
        (nu.SetRef, shape.SetRef),
        (nu.IntRef, shape.IntRef),
        (nu.StrRef, shape.StrRef),
        (nu.FloatRef, shape.FloatRef),
        (nu.BoolRef, shape.BoolRef),
        (nu.BytesRef, shape.BytesRef),
        (nu.ObjectRef, shape.ObjectRef),
    ],
)
def test_each_mem_ref_sits_on_the_base_shape_ref_of_its_type(ref: type, base: type) -> None:
    assert issubclass(ref, base)
    assert not issubclass(ref, shape.ReactiveItemRef)
    assert not issubclass(ref, shape.ReactiveMappingRef)


def test_a_dict_slot_merges_and_copies_like_a_dict() -> None:
    data = {"meta": {"a": 1}}
    ctx = nu.Context().bind(dict, data, Port)
    assert nu.run(Port.meta.merge({"b": 2}), ctx)[0] == {"a": 1, "b": 2}
    copied = nu.run(Port.meta.copy(), ctx)[0]
    assert copied == {"a": 1}
    assert copied is not data["meta"]


def test_a_merged_dict_carries_the_declared_value_type() -> None:
    merged = Port.meta.merge({"b": 2})
    assert isinstance(merged, forms.Dict)
    assert type(merged["b"]) is forms.Int


def test_a_list_slot_sorts_and_concatenates_like_a_list() -> None:
    data = {"tags": ["b", "a"]}
    ctx = nu.Context().bind(dict, data, Port)
    assert nu.run(Port.tags + ["c"], ctx)[0] == ["b", "a", "c"]  # noqa: RUF005 (a term, not a list)
    nu.run(Port.tags.sort(), ctx)
    assert data["tags"] == ["a", "b"]


def test_a_set_slot_copies_like_a_set() -> None:
    data = {"members": {"a"}}
    ctx = nu.Context().bind(dict, data, Port)
    copied = nu.run(Port.members.copy(), ctx)[0]
    assert copied == {"a"}
    assert copied is not data["members"]


def test_a_dict_slot_still_descends_by_key() -> None:
    assert isinstance(Port.meta["a"], nu.IntRef)
    assert isinstance(Port.tags[0], nu.StrRef)


def test_a_leaf_fallback_reads_as_the_plain_value_form() -> None:
    assert type(Port.count.fallback(0)) is forms.Int
    assert type(Port.name.fallback("x")) is forms.Str
