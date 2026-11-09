"""Abstract forms carry the collections.abc surface; built-in-only methods sit on the concrete forms.

Sequence: ``sort`` and ``copy`` are ``List``'s. Set: the abstract forms carry
the comparisons, ``isdisjoint``, and the named methods that are Nu's spelling
of the ABC's ``& | - ^`` and ``|= &= -= ^=``; only ``copy`` is ``Set`` /
``FrozenSet``'s. The mutable tiers carry every ABC mixin, so a ref on them
does too.
"""

from __future__ import annotations

import pytest

import nu
from nu.forms.collections.abc import (
    MutableSequenceForm,
    MutableSetForm,
    SequenceForm,
    SetLikeForm,
)


SET_QUERIES = (
    "union",
    "intersection",
    "difference",
    "symmetric_difference",
    "issubset",
    "issuperset",
)
SET_UPDATES = (
    "update",
    "intersection_update",
    "difference_update",
    "symmetric_difference_update",
)


class _Port(nu.Shape):
    xs = nu.ListRef.slot(int)
    st = nu.SetRef.slot(int)


def _ctx(data: dict) -> nu.Context:
    return nu.Context().bind(dict, data, _Port)


# --- sequence ------------------------------------------------------------------


@pytest.mark.parametrize("name", ["sort", "copy"])
def test_list_only_methods_are_on_list_alone(name: str):
    assert not hasattr(SequenceForm, name)
    assert not hasattr(MutableSequenceForm, name)
    assert not hasattr(_Port.xs, name)
    assert hasattr(nu.List, name)


@pytest.mark.parametrize(
    "name",
    [
        "__setitem__",
        "__delitem__",
        "__iadd__",
        "insert",
        "append",
        "extend",
        "pop",
        "remove",
        "reverse",
        "clear",
    ],
)
def test_mutable_sequence_form_carries_every_abc_mixin(name: str):
    assert name in vars(MutableSequenceForm)


def test_first_and_last_stay_on_the_sequence_form():
    assert "first_elem" in vars(SequenceForm)
    assert "last_elem" in vars(SequenceForm)


def test_subscript_write_delete_and_iadd_run_on_a_ref():
    data = {"xs": [1, 2, 3]}
    ctx = _ctx(data)
    _, ctx = nu.run(_Port.xs.__setitem__(0, 9), ctx)
    _, ctx = nu.run(_Port.xs.__delitem__(1), ctx)
    term = _Port.xs
    term += [4]
    assert type(term) is nu.List
    _, ctx = nu.run(term, ctx)
    assert data["xs"] == [9, 3, 4]


def test_list_copy_runs():
    assert nu.run(nu.List.of(3, 1, 2).copy())[0] == [3, 1, 2]
    assert type(nu.List.of(1).copy()) is nu.List


# --- set -----------------------------------------------------------------------


@pytest.mark.parametrize("name", SET_QUERIES)
def test_named_set_queries_are_on_the_abstract_set_form(name: str):
    assert name in vars(SetLikeForm)
    assert hasattr(_Port.st, name)
    assert hasattr(nu.FrozenSet, name)
    assert hasattr(nu.Dict({"a": 1}).keys(), name)


@pytest.mark.parametrize("name", SET_UPDATES)
def test_named_set_updates_are_on_the_abstract_mutable_set_form(name: str):
    assert name in vars(MutableSetForm)
    assert hasattr(_Port.st, name)
    assert not hasattr(nu.FrozenSet, name)


def test_copy_is_on_the_concrete_sets_alone():
    assert not hasattr(SetLikeForm, "copy")
    assert not hasattr(_Port.st, "copy")
    assert nu.run(nu.Set({1, 2}).copy())[0] == {1, 2}
    assert type(nu.FrozenSet(frozenset({1})).copy()) is nu.FrozenSet


def test_set_algebra_runs_on_a_ref():
    data = {"st": {1, 2}}
    ctx = _ctx(data)
    assert nu.run(_Port.st.union({3}), ctx)[0] == {1, 2, 3}
    assert nu.run(_Port.st.issubset({1, 2, 3}), ctx)[0] is True
    _, ctx = nu.run(_Port.st.difference_update({1}), ctx)
    assert data["st"] == {2}


@pytest.mark.parametrize(
    "name", ["__le__", "__lt__", "__ge__", "__gt__", "isdisjoint", "contains", "len"]
)
def test_set_like_form_carries_the_set_abc(name: str):
    assert hasattr(SetLikeForm, name)


@pytest.mark.parametrize("name", ["add", "discard", "remove", "pop", "clear"])
def test_mutable_set_form_carries_every_abc_mixin(name: str):
    assert name in vars(MutableSetForm)


@pytest.mark.parametrize(
    ("build", "expected"),
    [
        (lambda: nu.Set({1}) <= {1, 2}, True),
        (lambda: nu.Set({1, 2}) < {1, 2}, False),
        (lambda: nu.FrozenSet(frozenset({1, 2})) >= {1}, True),
        (lambda: nu.FrozenSet(frozenset({1, 2})) > {1, 2}, False),
        (lambda: nu.Dict({"a": 1}).keys() <= {"a", "b"}, True),
        (lambda: nu.Dict({"a": 1}).items() < {("a", 1), ("b", 2)}, True),
        (lambda: nu.Dict({"a": 1}).keys().isdisjoint({"b"}), True),
    ],
)
def test_subset_comparisons_run_on_every_set_like_form(build: object, expected: bool):
    assert nu.run(build())[0] is expected  # type: ignore[operator]


def test_subset_comparisons_and_isdisjoint_run_on_a_set_ref():
    ctx = _ctx({"st": {1, 2}})
    assert nu.run(_Port.st <= {1, 2, 3}, ctx)[0] is True
    assert nu.run(_Port.st > {1}, ctx)[0] is True
    assert nu.run(_Port.st.isdisjoint({3}), ctx)[0] is True


def test_flow_operators_still_compose_on_a_set():
    assert type(nu.Set({1}) & nu.Set({2})) is nu.Race
    assert type(_Port.st | _Port.st) is nu.Parallel


def test_named_set_queries_keep_the_concrete_type():
    assert nu.run(nu.FrozenSet(frozenset({1, 2})).union({3}))[0] == frozenset({1, 2, 3})
    assert type(nu.FrozenSet(frozenset({1})).union({2})) is nu.FrozenSet
    assert type(nu.Set({1}).union({2})) is nu.Set
