"""The ordered mapping tier: Mapping + Reversible, three levels.

``OrderedMappingForm`` carries the reversed reads and paging; plain
``MappingForm`` keeps the ``collections.abc.Mapping`` surface only. ``Dict``
sits on the mutable ordered tier, and the dict-only methods live on it alone.
"""

from __future__ import annotations

import inspect

import pytest

import nu
from nu.forms.collections.abc import (
    MappingForm,
    MutableMappingForm,
    MutableOrderedMappingForm,
    OrderedMappingForm,
    ReactiveMappingForm,
    ReactiveOrderedMappingForm,
)


ORDERED_READS = ("reversed_keys", "reversed_values", "reversed_items")
DICT_ONLY = ("copy", "merge", "merge_update")


def test_the_tiers_stack_on_the_plain_mapping_tiers():
    assert issubclass(OrderedMappingForm, MappingForm)
    assert issubclass(MutableOrderedMappingForm, OrderedMappingForm)
    assert issubclass(MutableOrderedMappingForm, MutableMappingForm)
    assert issubclass(ReactiveOrderedMappingForm, MutableOrderedMappingForm)
    assert issubclass(ReactiveOrderedMappingForm, ReactiveMappingForm)


def test_dict_is_a_mutable_ordered_mapping():
    assert issubclass(nu.Dict, MutableOrderedMappingForm)
    assert not issubclass(nu.Dict, ReactiveMappingForm)


@pytest.mark.parametrize("name", ORDERED_READS)
def test_reversed_reads_are_on_the_ordered_tier_only(name: str):
    assert not hasattr(MappingForm, name)
    assert not hasattr(MutableMappingForm, name)
    assert hasattr(OrderedMappingForm, name)


def test_plain_keys_take_no_paging_args():
    assert list(inspect.signature(MappingForm.keys).parameters) == ["self"]
    assert list(inspect.signature(OrderedMappingForm.keys).parameters) == [
        "self",
        "after",
        "limit",
    ]


@pytest.mark.parametrize("name", DICT_ONLY)
def test_dict_only_methods_are_on_dict_alone(name: str):
    for form in (MappingForm, MutableMappingForm, OrderedMappingForm, MutableOrderedMappingForm):
        assert not hasattr(form, name), form
    assert hasattr(nu.Dict, name)


def test_dict_reads_back_to_front():
    d = nu.Dict({"a": 1, "b": 2})
    assert list(nu.run(d.reversed_keys())[0]) == ["b", "a"]
    assert list(nu.run(d.reversed_values())[0]) == [2, 1]
    assert list(nu.run(d.reversed_items())[0]) == [("b", 2), ("a", 1)]


def test_dict_only_methods_run():
    d = nu.Dict({"a": 1})
    assert nu.run(d.copy())[0] == {"a": 1}
    assert nu.run(d.merge({"b": 2}))[0] == {"a": 1, "b": 2}
    assert nu.run(d.merge_update({"b": 2}))[0] == {"a": 1, "b": 2}
    assert type(d.copy()) is nu.Dict
