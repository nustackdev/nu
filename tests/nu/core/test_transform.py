"""Tests for the transform atoms.

Map and Filter bind each item under a name (a child, default "item") and
evaluate a Nu child against it, read via Attr. Flatten / Unique are
single-source lenses. Sorted is a scalar query: iterable in, list out.
Coverage runs real programs through ``run``.
"""

from __future__ import annotations

import asyncio

import pytest

import nu
from nu.context import Attr as AttrRef
from nu.core import Collect, Filter, Iter, Lt, Map, Mul
from nu.core.transform import Flatten, Sorted, Unique
from nu.engine.validation.law import ValidationError
from nu.forms.collections import List
from nu.lang import EMPTY, Attr, Cardinality, Literal
from nu.lang.helpers import arun, compile, run, validate


# --- Sorted: iterable in, list out ----------------------------------------


def test_sorted_orders_a_list_value_into_a_new_list():
    value, _ = run(Sorted(Literal((3, 1, 2))))
    assert value == [1, 2, 3]


def test_sorted_orders_a_ref():
    class Port(nu.Shape):
        tags = nu.ListRef.slot(str)

    ctx = nu.Context().bind(dict, {"tags": ["b", "c", "a"]}, Port)
    assert run(Sorted(Port.tags), ctx)[0] == ["a", "b", "c"]


def test_sorted_orders_a_collected_stream_sync_and_async():
    term = Sorted(Collect(Map(Iter(Literal([3, 1, 2])), Mul(AttrRef("item"), Literal(10)))))
    assert run(term)[0] == [10, 20, 30]
    assert asyncio.run(arun(term))[0] == [10, 20, 30]


def test_sorted_refuses_a_bare_stream():
    with pytest.raises(ValidationError, match="scalar_stream_refused"):
        run(Sorted(Iter(Literal([3, 1, 2]))))


def test_sorted_propagates_empty():
    assert run(Sorted(Literal(EMPTY)))[0] is EMPTY
    assert asyncio.run(arun(Sorted(Literal(EMPTY))))[0] is EMPTY


def test_sorted_is_a_scalar_and_validates():
    program = compile(Sorted(Literal([3, 1, 2])))
    assert program.attr(program.root, Attr.CARDINALITY) is Cardinality.SCALAR
    assert validate(program) is program


def test_sorted_function_gives_a_list_form():
    xs = nu.sorted([3, 1, 2])
    assert isinstance(xs, List)
    assert run(xs.len())[0] == 3
    assert run(xs.index(3))[0] == 2


# --- single-source lenses (Flatten / Unique) -----------------------------


def test_flatten_concatenates_one_level():
    value, _ = run(Collect(Flatten(Iter(Literal([[1, 2], [3], [4, 5]])))))
    assert value == [1, 2, 3, 4, 5]


def test_unique_drops_repeats_first_seen_order():
    value, _ = run(Collect(Unique(Iter(Literal([1, 2, 1, 3, 2])))))
    assert value == [1, 2, 3]


def test_a_single_source_lens_is_a_stream_and_validates():
    program = compile(Unique(Literal([3, 1, 2])))
    assert program.attr(program.root, Attr.CARDINALITY) is Cardinality.STREAM
    assert validate(program) is program


# --- Map -----------------------------------------------------------------


def test_map_is_a_stream():
    program = compile(Map(Iter(Literal([1, 2, 3])), Mul(AttrRef("item"), Literal(10))))
    assert program.attr(program.root, Attr.CARDINALITY) is Cardinality.STREAM


def test_map_applies_its_transform_per_item():
    tree = Collect(Map(Iter(Literal([1, 2, 3])), Mul(AttrRef("item"), Literal(10))))
    value, _ = run(tree)
    assert value == [10, 20, 30]


def test_map_honors_a_custom_item_name():
    tree = Collect(Map(Iter(Literal([1, 2])), Mul(AttrRef("x"), Literal(2)), key="x"))
    value, _ = run(tree)
    assert value == [2, 4]


# --- Filter --------------------------------------------------------------


def test_filter_keeps_matching_items():
    tree = Collect(Filter(Iter(Literal([1, 2, 3, 4])), Lt(AttrRef("item"), Literal(3))))
    value, _ = run(tree)
    assert value == [1, 2]


# --- Iterator.map / Iterator.filter -------------------------------------


def test_iterator_map_takes_a_lambda():
    assert run(nu.List.of(1, 2).iter().map(lambda x: nu.Int(x) * 10).to_list())[0] == [10, 20]


def test_iterator_map_takes_a_tree_under_the_default_name():
    assert run(nu.List.of(1, 2).iter().map(Mul(AttrRef("item"), 10)).to_list())[0] == [10, 20]


def test_iterator_map_takes_a_tree_under_an_explicit_name():
    assert run(nu.List.of(1, 2).iter().map(Mul(AttrRef("n"), 10), key="n").to_list())[0] == [10, 20]


def test_iterator_filter_takes_a_lambda():
    assert run(nu.List.of(1, 2, 3, 4).iter().filter(lambda x: x > 2).to_list())[0] == [3, 4]


def test_iterator_filter_takes_a_tree_under_the_default_name():
    assert run(nu.List.of(1, 2, 3).iter().filter(Lt(AttrRef("item"), 3)).to_list())[0] == [1, 2]


def test_iterator_filter_takes_a_tree_under_an_explicit_name():
    assert run(nu.List.of(1, 2, 3).iter().filter(Lt(AttrRef("n"), 3), key="n").to_list())[0] == [
        1,
        2,
    ]


@pytest.mark.parametrize("method", ["map", "filter"])
def test_iterator_methods_refuse_a_lambda_with_an_explicit_name(method):
    xs = nu.List.of(1, 2).iter()
    with pytest.raises(ValueError, match="not both"):
        getattr(xs, method)(lambda x: x, key="n")


def test_iterator_lambdas_chain():
    xs = nu.List.of(1, 2, 3).iter().filter(lambda x: x > 1).map(lambda x: nu.Int(x) * 10)
    assert run(xs.to_list())[0] == [20, 30]


# --- composition ---------------------------------------------------------


def test_a_lens_chain_stays_a_stream_and_evaluates():
    tree = Collect(
        Filter(
            Map(Iter(Literal([1, 2, 3])), Mul(AttrRef("item"), Literal(10))),
            Lt(AttrRef("item"), Literal(25)),
        )
    )
    program = compile(tree)
    assert validate(program) is program
    value, _ = run(tree)
    assert value == [10, 20]
