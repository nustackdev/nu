"""Tests for the transform atoms (stream-to-stream lenses).

Map and Filter bind each item under a name (a child, default "item") and
evaluate a Nu child against it, read via AttrRef. Sorted / Flatten / Unique are
single-source lenses. Coverage runs real programs through ``run``.
"""

from __future__ import annotations

from nu.context import AttrRef
from nu.core import Collect, Filter, Iter, Literal, Lt, Map, Mul
from nu.core.transform import Flatten, Sorted, Unique
from nu.lang import Attr, Cardinality
from nu.lang.helpers import compile, run, validate


# --- single-source lenses (Sorted / Flatten / Unique) --------------------


def test_sorted_orders_its_source():
    value, _ = run(Collect(Sorted(Iter(Literal([3, 1, 2])))))
    assert value == [1, 2, 3]


def test_flatten_concatenates_one_level():
    value, _ = run(Collect(Flatten(Iter(Literal([[1, 2], [3], [4, 5]])))))
    assert value == [1, 2, 3, 4, 5]


def test_unique_drops_repeats_first_seen_order():
    value, _ = run(Collect(Unique(Iter(Literal([1, 2, 1, 3, 2])))))
    assert value == [1, 2, 3]


def test_a_single_source_lens_is_a_stream_and_validates():
    program = compile(Sorted(Literal([3, 1, 2])))
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
