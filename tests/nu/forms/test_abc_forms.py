"""Abstract collection forms: a value typed only by its ABC gets the ABC surface."""

from __future__ import annotations

import collections.abc as cabc
import typing
from collections import OrderedDict, UserList, deque
from types import MappingProxyType

import pytest

import nu
from nu import mem as nm
from nu.forms import (
    AbstractSet,
    Collection,
    DictItems,
    DictKeys,
    DictValues,
    Mapping,
    MutableMapping,
    MutableSequence,
    MutableSet,
    Object,
    Sequence,
)
from nu.lang import Context
from nu.lang.helpers import compile, eval
from nu.lang.typeinfo import _form_for


def val(term: nu.Nu) -> object:
    # Unvalidated, as in the forms smoke suite: a command over a literal
    # mutates it in place instead of asking for a ref in slot 0.
    return eval(compile(term), Context())[0]


# --- each form wraps a value of its ABC and its surface runs ---------------


def test_collection_over_any_collection():
    assert val(Collection(frozenset({1, 2})).len()) == 2
    assert val(Collection(nu.Literal(factory=lambda: deque([1, 2, 3]))).contains(2)) is True
    assert val(Collection(range(3)).iter().to_list()) == [0, 1, 2]


def test_sequence_over_a_tuple_and_a_range():
    seq = Sequence((1, 2, 3))
    assert val(seq.index(2)) == 1
    assert val(seq.count(3)) == 1
    assert type(seq[0]) is Object
    assert val(seq[0]) == 1
    assert type(seq[1:]) is Sequence
    assert val(seq[1:]) == (2, 3)
    assert val(Sequence(range(5)).slice(1, 3)) == range(1, 3)


def test_mutable_sequence_over_a_user_list():
    seq = MutableSequence(nu.Literal(factory=lambda: UserList([3, 1, 2])))
    assert val(seq.len()) == 3
    assert type(seq.slice(0, 2)) is MutableSequence
    assert val(seq.slice(0, 2)) == UserList([3, 1])
    assert val(MutableSequence([1, 2, 3]).pop()) == 3


def test_mapping_over_a_mapping_proxy():
    m = Mapping(MappingProxyType({"a": 1, "b": 2}))
    assert val(m.get_item("a")) == 1
    assert val(m.get_item("z", 0)) == 0
    assert type(m["a"]) is Object
    assert type(m.keys()) is DictKeys
    assert type(m.values()) is DictValues
    assert type(m.items()) is DictItems
    assert list(val(m.keys())) == ["a", "b"]
    assert val(m.len()) == 2


def test_mutable_mapping_over_an_ordered_dict():
    m = MutableMapping(nu.Literal(factory=lambda: OrderedDict(a=1, b=2)))
    assert val(m.get_item("b")) == 2
    assert val(m.pop("a")) == 1
    assert val(MutableMapping({"a": 1}).set_item("b", 2)) is None


def test_abstract_set_over_a_frozenset_and_a_keys_view():
    s = AbstractSet(frozenset({1, 2}))
    assert val(s.union({3})) == frozenset({1, 2, 3})
    assert type(s.union({3})) is AbstractSet
    assert val(s.issubset({1, 2, 3})) is True
    assert val(
        AbstractSet(nu.Literal(factory=lambda: {"a": 1, "b": 2}.keys())).intersection({"a"})
    ) == {"a"}


def test_mutable_set_over_a_set():
    s = MutableSet({1, 2})
    assert val(s.isdisjoint({3})) is True
    assert type(s.difference({1})) is MutableSet
    assert val(s.difference({1})) == {2}
    assert val(MutableSet({1, 2}).add(3)) is None


# --- typeinfo maps the ABCs to them ----------------------------------------


@pytest.mark.parametrize(
    ("py_type", "form"),
    [
        (cabc.Collection, Collection),
        (cabc.Sequence, Sequence),
        (cabc.MutableSequence, MutableSequence),
        (cabc.Mapping, Mapping),
        (cabc.MutableMapping, MutableMapping),
        (cabc.Set, AbstractSet),
        (cabc.MutableSet, MutableSet),
        (cabc.Mapping[str, int], Mapping),
        (typing.Mapping, Mapping),
        (typing.AbstractSet, AbstractSet),
    ],
)
def test_form_for_maps_an_abc_to_its_form(py_type, form):
    assert _form_for(py_type) is form


def test_form_for_keeps_the_builtins():
    assert _form_for(dict) is nu.Dict
    assert _form_for(tuple) is nu.Tuple
    assert _form_for(frozenset) is nu.FrozenSet
    assert _form_for(cabc.Iterator) is Object


def test_the_abstract_forms_are_flat_at_the_root():
    for form in (
        Collection,
        Sequence,
        MutableSequence,
        Mapping,
        MutableMapping,
        AbstractSet,
        MutableSet,
    ):
        assert getattr(nu, form.__name__) is form


# --- a mutable abstract form over a ref acts like the concrete one ---------


class Held(nu.Shape):
    seq = nm.ListRef.slot(int)
    table = nm.DictRef.slot(int)
    bag = nm.SetRef.slot(int)


@pytest.mark.parametrize(
    ("abstract", "concrete", "slot", "data", "pop"),
    [
        (MutableSequence, nu.List, "seq", [1, 2, 3], ()),
        (MutableMapping, nu.Dict, "table", {"a": 1, "b": 2}, ("a",)),
        (MutableSet, nu.Set, "bag", {7}, ()),
    ],
    ids=["sequence", "mapping", "set"],
)
def test_a_mutable_abstract_form_over_a_ref_pops_like_the_concrete(
    abstract, concrete, slot, data, pop
):
    # pop is an Action: through a form it still lands on the value the ref holds.
    def run(form: type) -> tuple[object, object]:
        store = {slot: type(data)(data)}
        ctx = nu.Context().bind(dict, store, Held)
        popped = nu.run(form(getattr(Held, slot)).pop(*pop), ctx)[0]
        return popped, store[slot]

    assert run(abstract) == run(concrete)
